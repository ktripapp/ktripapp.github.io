from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import logging
import traceback

app = FastAPI()


# ---- Mongo client lifecycle & helpers ----
def _get_mongo_uri():
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        try:
            import secrets_local
            mongo_uri = getattr(secrets_local, 'MONGO_URI', None)
        except Exception:
            mongo_uri = None
    return mongo_uri


@app.on_event('startup')
def _startup_mongo():
    """Initialize a shared MongoClient (if configured) at app startup."""
    uri = _get_mongo_uri()
    if not uri:
        app.state.mongo_client = None
        app.state.mongo_db = None
        return
    try:
        from pymongo import MongoClient
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # test connection (short timeout)
        client.admin.command('ping')
        app.state.mongo_client = client
        app.state.mongo_db = client['coins']
    except Exception:
        # leave client as None on failure; endpoints will fall back or error
        app.state.mongo_client = None
        app.state.mongo_db = None


@app.on_event('shutdown')
def _shutdown_mongo():
    mc = getattr(app.state, 'mongo_client', None)
    try:
        if mc:
            try:
                mc.close()
            except Exception:
                pass
    finally:
        app.state.mongo_client = None
        app.state.mongo_db = None


def _read_series_from_db(coll_name, field_name):
    """Generic helper: read (date, field) pairs from a collection in the configured `coins` DB.

    Returns list of dicts: [{'date': iso_date, 'value': float}, ...]
    Raises ValueError if no Mongo configured.
    """
    db = getattr(app.state, 'mongo_db', None)
    if not db:
        raise ValueError('no mongo')
    coll = db[coll_name]
    cursor = coll.find({}, {'_id': 0, 'date': 1, field_name: 1}).sort('date', 1)
    arr = []
    for d in cursor:
        date = d.get('date')
        v = d.get(field_name)
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

# ---- end helpers ----

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


def _verify_request(request: Request):
    """Simple verifier for requests coming from the GitHub Pages frontend.

    - Checks referer/origin contains the configured host (default: ktripapp.github.io).
    - Allows a development token via `PROXY_DEV_TOKEN` env var when provided
      (send in header `X-Proxy-Token`) to enable curl/testing without a real referer.
    This is intended as a lightweight protection (not perfect) while keeping
    the Render API key secret on the server.
    """
    referer = request.headers.get('referer') or request.headers.get('origin')
    allowed = os.environ.get('ALLOWED_REFERER_HOST', 'ktripapp.github.io')

    # Require referer/origin to match expected host. Development bypass removed.
    if not referer or allowed not in referer:
        raise HTTPException(status_code=403, detail='forbidden: invalid referer')


def _forward_to_render(path: str, timeout: int = 15):
    """Internal helper: forward GET request to the configured Render base.

    The server-side `RENDER_API_KEY` is injected into the forwarded request.
    """
    # Remote forwarding removed. This function is no longer used.
    raise RuntimeError('_forward_to_render has been removed')


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
        except Exception:
            return JSONResponse(status_code=500, content={"status": "error", "source": "mongodb"})

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
    # Prefer shared MongoDB client initialized at startup
    try:
        db = getattr(app.state, 'mongo_db', None)
        if db:
            try:
                coll = db['historical_daily_data']
                cursor = coll.find().sort('date', 1)
                docs = [_serialize_doc(d) for d in cursor]
                return docs
            except Exception as e:
                logging.exception('MongoDB read failed in /api/historical_daily_data')
                return JSONResponse(status_code=500, content={"error": "mongodb read failed", "detail": str(e)})

        # Fallback to data.parquet
        file_path = os.path.join(os.path.dirname(__file__), 'data.parquet')
        if not os.path.exists(file_path):
            msg = f"MONGO_URI not set and data.parquet missing at {file_path}"
            logging.error(msg)
            return JSONResponse(status_code=500, content={"error": "no data source available", "detail": msg})

        try:
            df = pd.read_parquet(file_path)
        except Exception as e:
            logging.exception('Failed reading parquet file')
            return JSONResponse(status_code=500, content={"error": "failed reading parquet", "detail": str(e)})

        try:
            records = df.to_dict(orient='records')
            return records
        except Exception as e:
            logging.exception('Failed serializing parquet data')
            return JSONResponse(status_code=500, content={"error": "failed serializing data", "detail": str(e)})
    except Exception as e:
        logging.exception('Unexpected error in /api/historical_daily_data')
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": "internal server error", "detail": str(e), "trace": tb})


@app.get('/api/extra_series')
def extra_series():
    """Return extra indicator series from other collections in the `coins` DB."""
    try:
        try:
            out = {
                'onchain_mvrv': _read_series_from_db('onchain_data', 'mvrv'),
                'etf_ibit': _read_series_from_db('ETF_flows', 'ibit'),
                'fear_greed': _read_series_from_db('cryptofg', 'value'),
                'bond_m2sl': _read_series_from_db('bond_yields', 'm2sl')
            }
            return out
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})


@app.get('/proxy/historical_daily_data')
def proxy_historical(request: Request):
    """Proxy endpoint that forwards to the Render API's `/api/historical_daily_data`.

    This keeps `RENDER_API_KEY` on the server and only allows requests originating
    from the configured referer host (or when a dev token is provided).
    """
    _verify_request(request)
    # RENDER_API_KEY / remote forwarding is not used — always serve local data
    return get_data()


@app.get('/proxy/extra_series')
def proxy_extra_series(request: Request):
    """Proxy endpoint that forwards to the Render API's `/api/extra_series`."""
    _verify_request(request)
    # RENDER_API_KEY / remote forwarding is not used — always serve local data
    return extra_series()


@app.get('/api/onchain_data')
def onchain_data():
    """Backward-compatible endpoint returning onchain `mvrv` series.

    Returns list of {date, value} similar to what `/api/extra_series` provides
    under `onchain_mvrv`.
    """
    try:
        try:
            arr = _read_series_from_db('onchain_data', 'mvrv')
            return arr
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})


@app.get('/api/ETF_flows')
def etf_flows():
    """Return ETF flows `bitb` series as list of {date,value}."""
    try:
        try:
            arr = _read_series_from_db('ETF_flows', 'ibit')
            return arr
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})


@app.get('/api/cryptofg')
def cryptofg():
    """Return Fear/Greed `value` series as list of {date,value}."""
    try:
        try:
            arr = _read_series_from_db('cryptofg', 'value')
            return arr
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})


@app.get('/api/bond_yields')
def bond_yields():
    """Return bond yields `m2sl` series as list of {date,value}."""
    try:
        try:
            arr = _read_series_from_db('bond_yields', 'm2sl')
            return arr
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})