from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd

app = FastAPI()

# CORS for local testing and deployed site
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://ktripapp.github.io"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _serialize_doc(doc: dict):
    # Remove `_id` and convert datetimes to ISO strings for JSON
    out = {}
    for k, v in doc.items():
        if k == '_id':
            continue
        elif hasattr(v, 'isoformat'):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


@app.get("/")
def root():
    return {"status": "ok"}


@app.get('/api/health')
def health():
    """Health check: reports whether service can reach MongoDB or has parquet fallback."""
    mongo_uri = os.environ.get('MONGO_URI')
    # fallback to local secrets_local.py for development
    if not mongo_uri:
        try:
            import secrets_local
            mongo_uri = getattr(secrets_local, 'MONGO_URI', None)
        except Exception:
            mongo_uri = None
    if mongo_uri:
        try:
            from pymongo import MongoClient
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            client.admin.command('ping')
            return {"status": "ok", "source": "mongodb"}
        except Exception as e:
            return JSONResponse(status_code=500, content={"status": "error", "source": "mongodb", "detail": str(e)})

    # parquet fallback
    file_path = os.path.join(os.path.dirname(__file__), 'data.parquet')
    if os.path.exists(file_path):
        return {"status": "ok", "source": "parquet"}
    return JSONResponse(status_code=500, content={"status": "error", "detail": "no data source available"})


@app.get("/api/historical_daily_data")
def get_data():
    """Return historical daily OHLCV records.

    Priority:
    1) If `MONGO_URI` env var is set, read from MongoDB `coins.historical_daily_data`.
    2) Otherwise, fallback to reading `data.parquet` next to this file.
    Returns JSON array of documents or a JSON error with 500 status.
    """
    try:
        mongo_uri = os.environ.get('MONGO_URI')
        # fallback to local secrets_local.py for development
        if not mongo_uri:
            try:
                import secrets_local
                mongo_uri = getattr(secrets_local, 'MONGO_URI', None)
            except Exception:
                mongo_uri = None

        # If we have a Mongo URI, try to fetch from MongoDB
        if mongo_uri:
            try:
                from pymongo import MongoClient
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": "pymongo not installed", "detail": str(e)})

            try:
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                db = client['coins']
                coll = db['historical_daily_data']
                cursor = coll.find().sort('date', 1)
                docs = [_serialize_doc(d) for d in cursor]
                return docs
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": "mongodb connection failed", "detail": str(e)})

        # Fallback to data.parquet
        file_path = os.path.join(os.path.dirname(__file__), 'data.parquet')
        if not os.path.exists(file_path):
            return JSONResponse(status_code=500, content={"error": "no data source available", "detail": "MONGO_URI not set and data.parquet missing"})

        try:
            df = pd.read_parquet(file_path)
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": "failed reading parquet", "detail": str(e)})

        try:
            records = df.to_dict(orient='records')
            return records
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": "failed serializing data", "detail": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "internal server error", "detail": str(e)})


@app.get('/api/extra_series')
def extra_series():
    """Return extra indicator series from other collections in the `coins` DB.

    Collections/fields:
    - onchain_data.mvrv -> returns list of {date,value}
    - ETF_flows.bitb    -> returns list of {date,value}
    - cryptofg.value    -> returns list of {date,value}
    - bond_yields.m2sl  -> returns list of {date,value}

    Falls back with 500 if MongoDB isn't available.
    """
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        try:
            import secrets_local
            mongo_uri = getattr(secrets_local, 'MONGO_URI', None)
        except Exception:
            mongo_uri = None

    if not mongo_uri:
        return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})

    try:
        from pymongo import MongoClient
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "pymongo not installed", "detail": str(e)})

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client['coins']

        out = {}
        # helper to read a collection and pick date + field
        def read_series(coll_name, field_name):
            coll = db[coll_name]
            cursor = coll.find({},{'_id':0, 'date':1, field_name:1}).sort('date', 1)
            arr = []
            for d in cursor:
                # normalize date and value
                date = d.get('date')
                v = d.get(field_name)
                if date is None or v is None:
                    continue
                # if date is a datetime-like, isoformat it; else stringify
                try:
                    if hasattr(date, 'isoformat'):
                        ds = date.isoformat()
                    else:
                        ds = str(date)
                except Exception:
                    ds = str(date)
                try:
                    vv = float(v)
                except Exception:
                    try:
                        vv = float(str(v).replace(',',''))
                    except Exception:
                        continue
                arr.append({'date': ds, 'value': vv})
            return arr

        out['onchain_mvrv'] = read_series('onchain_data', 'mvrv')
        out['etf_bitb'] = read_series('ETF_flows', 'bitb')
        out['fear_greed'] = read_series('cryptofg', 'value')
        out['bond_m2sl'] = read_series('bond_yields', 'm2sl')

        return out
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed","detail":str(e)})


@app.get('/api/onchain_data')
def onchain_data():
    """Backward-compatible endpoint returning onchain `mvrv` series.

    Returns list of {date, value} similar to what `/api/extra_series` provides
    under `onchain_mvrv`.
    """
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        try:
            import secrets_local
            mongo_uri = getattr(secrets_local, 'MONGO_URI', None)
        except Exception:
            mongo_uri = None

    if not mongo_uri:
        return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})

    try:
        from pymongo import MongoClient
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "pymongo not installed", "detail": str(e)})

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client['coins']
        coll = db['onchain_data']
        cursor = coll.find({}, {'_id':0, 'date':1, 'mvrv':1}).sort('date', 1)
        arr = []
        for d in cursor:
            date = d.get('date')
            v = d.get('mvrv')
            if date is None or v is None:
                continue
            try:
                ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
            except Exception:
                ds = str(date)
            try:
                vv = float(v)
            except Exception:
                try:
                    vv = float(str(v).replace(',',''))
                except Exception:
                    continue
            arr.append({'date': ds, 'value': vv})
        return arr
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed","detail":str(e)})


@app.get('/api/ETF_flows')
def etf_flows():
    """Return ETF flows `bitb` series as list of {date,value}."""
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        try:
            import secrets_local
            mongo_uri = getattr(secrets_local, 'MONGO_URI', None)
        except Exception:
            mongo_uri = None

    if not mongo_uri:
        return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})

    try:
        from pymongo import MongoClient
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "pymongo not installed", "detail": str(e)})

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client['coins']
        coll = db['ETF_flows']
        cursor = coll.find({}, {'_id':0, 'date':1, 'bitb':1}).sort('date', 1)
        arr = []
        for d in cursor:
            date = d.get('date')
            v = d.get('bitb')
            if date is None or v is None:
                continue
            try:
                ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
            except Exception:
                ds = str(date)
            try:
                vv = float(v)
            except Exception:
                try:
                    vv = float(str(v).replace(',',''))
                except Exception:
                    continue
            arr.append({'date': ds, 'value': vv})
        return arr
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed","detail":str(e)})


@app.get('/api/cryptofg')
def cryptofg():
    """Return Fear/Greed `value` series as list of {date,value}."""
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        try:
            import secrets_local
            mongo_uri = getattr(secrets_local, 'MONGO_URI', None)
        except Exception:
            mongo_uri = None

    if not mongo_uri:
        return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})

    try:
        from pymongo import MongoClient
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "pymongo not installed", "detail": str(e)})

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client['coins']
        coll = db['cryptofg']
        cursor = coll.find({}, {'_id':0, 'date':1, 'value':1}).sort('date', 1)
        arr = []
        for d in cursor:
            date = d.get('date')
            v = d.get('value')
            if date is None or v is None:
                continue
            try:
                ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
            except Exception:
                ds = str(date)
            try:
                vv = float(v)
            except Exception:
                try:
                    vv = float(str(v).replace(',',''))
                except Exception:
                    continue
            arr.append({'date': ds, 'value': vv})
        return arr
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed","detail":str(e)})


@app.get('/api/bond_yields')
def bond_yields():
    """Return bond yields `m2sl` series as list of {date,value}."""
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        try:
            import secrets_local
            mongo_uri = getattr(secrets_local, 'MONGO_URI', None)
        except Exception:
            mongo_uri = None

    if not mongo_uri:
        return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})

    try:
        from pymongo import MongoClient
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "pymongo not installed", "detail": str(e)})

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client['coins']
        coll = db['bond_yields']
        cursor = coll.find({}, {'_id':0, 'date':1, 'm2sl':1}).sort('date', 1)
        arr = []
        for d in cursor:
            date = d.get('date')
            v = d.get('m2sl')
            if date is None or v is None:
                continue
            try:
                ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
            except Exception:
                ds = str(date)
            try:
                vv = float(v)
            except Exception:
                try:
                    vv = float(str(v).replace(',',''))
                except Exception:
                    continue
            arr.append({'date': ds, 'value': vv})
        return arr
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed","detail":str(e)})