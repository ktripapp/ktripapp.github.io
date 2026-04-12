from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import logging
import traceback
from urllib.parse import urlparse

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
    if db is None:
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
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://ktripapp.github.io",
]

# Allow overriding via environment variable (comma-separated)
env_list = os.environ.get('ALLOWED_ORIGINS')
if env_list:
    allowed_origins = [s.strip() for s in env_list.split(',') if s.strip()]
else:
    allowed_origins = DEFAULT_ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    if not referer:
        raise HTTPException(status_code=403, detail='forbidden: missing referer/origin')

    # Normalize to origin (scheme://host:port) and compare against allowed list
    try:
        p = urlparse(referer)
        origin = f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else referer
    except Exception:
        origin = referer

    if origin not in allowed_origins:
        raise HTTPException(status_code=403, detail='forbidden: invalid origin')


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
def get_data(request: Request):
    """Return historical daily OHLCV records.

    Priority:
    1) If `MONGO_URI` env var is set, read from MongoDB `coins.historical_daily_data`.
    2) Otherwise, fallback to reading `data.parquet` next to this file.
    Returns JSON array of documents or a JSON error with 500 status.
    """
    # Verify origin
    _verify_request(request)

    # Prefer shared MongoDB client initialized at startup
    try:
        db = getattr(app.state, 'mongo_db', None)
        # Some pymongo Database objects raise NotImplementedError when truth-tested.
        # Guard the truth-test and fall back to attempting to use the DB directly.
        try:
            has_db = (db is not None)
        except NotImplementedError:
            has_db = True

        if has_db:
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
def extra_series(request: Request):
    """Return extra indicator series from other collections in the `coins` DB."""
    _verify_request(request)
    try:
        try:
            db = getattr(app.state, 'mongo_db', None)
            if db is None:
                raise ValueError('no mongo')

            # onchain_mvrv: documents store different metrics in 'metric'/'value'
            onchain = []
            for d in db['onchain_data'].find({'metric': 'mvrv'}, {'_id': 0, 'date': 1, 'value': 1}).sort('date', 1):
                date = d.get('date')
                val = d.get('value')
                if date is None or val is None:
                    continue
                try:
                    ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
                except Exception:
                    ds = str(date)
                try:
                    vv = float(val)
                except Exception:
                    continue
                onchain.append({'date': ds, 'value': vv})

            # ETF IBIT: field stored as 'IBIT' (uppercase) in ETF_flows
            etf = []
            for d in db['ETF_flows'].find({}, {'_id': 0, 'date': 1, 'IBIT': 1}).sort('date', 1):
                date = d.get('date')
                val = d.get('IBIT') if 'IBIT' in d else d.get('ibit')
                if date is None or val is None:
                    continue
                try:
                    ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
                except Exception:
                    ds = str(date)
                try:
                    vv = float(val)
                except Exception:
                    continue
                etf.append({'date': ds, 'value': vv})

            # fear_greed: standard series
            fg = _read_series_from_db('cryptofg', 'value')

            # bond_m2sl: bond_yields uses 'observation_date' and 'M2SL'
            bond = []
            for d in db['bond_yields'].find({}, {'_id': 0, 'observation_date': 1, 'M2SL': 1}).sort('observation_date', 1):
                date = d.get('observation_date') or d.get('date')
                val = d.get('M2SL') if 'M2SL' in d else d.get('m2sl')
                if date is None or val is None:
                    continue
                try:
                    ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
                except Exception:
                    ds = str(date)
                try:
                    vv = float(val)
                except Exception:
                    continue
                bond.append({'date': ds, 'value': vv})

            out = {
                'onchain_mvrv': onchain,
                'etf_ibit': etf,
                'fear_greed': fg,
                'bond_m2sl': bond
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
def onchain_data(request: Request):
    """Backward-compatible endpoint returning onchain `mvrv` series.

    Returns list of {date, value} similar to what `/api/extra_series` provides
    under `onchain_mvrv`.
    """
    _verify_request(request)
    try:
        try:
            db = getattr(app.state, 'mongo_db', None)
            if db is None:
                raise ValueError('no mongo')
            out = []
            for d in db['onchain_data'].find({'metric': 'mvrv'}, {'_id': 0, 'date': 1, 'value': 1}).sort('date', 1):
                date = d.get('date')
                val = d.get('value')
                if date is None or val is None:
                    continue
                try:
                    ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
                except Exception:
                    ds = str(date)
                try:
                    vv = float(val)
                except Exception:
                    continue
                out.append({'date': ds, 'value': vv})
            return out
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})


@app.get('/api/ETF_flows')
def etf_flows(request: Request):
    """Return ETF flows `bitb` series as list of {date,value}."""
    _verify_request(request)
    try:
        try:
            db = getattr(app.state, 'mongo_db', None)
            if db is None:
                raise ValueError('no mongo')
            out = []
            for d in db['ETF_flows'].find({}, {'_id': 0, 'date': 1, 'IBIT': 1}).sort('date', 1):
                date = d.get('date')
                val = d.get('IBIT') if 'IBIT' in d else d.get('ibit')
                if date is None or val is None:
                    continue
                try:
                    ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
                except Exception:
                    ds = str(date)
                try:
                    vv = float(val)
                except Exception:
                    continue
                out.append({'date': ds, 'value': vv})
            return out
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})


@app.get('/api/cryptofg')
def cryptofg(request: Request):
    """Return Fear/Greed `value` series as list of {date,value}."""
    _verify_request(request)
    try:
        try:
            arr = _read_series_from_db('cryptofg', 'value')
            return arr
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})


@app.get('/api/bond_yields')
def bond_yields(request: Request):
    """Return bond yields `m2sl` series as list of {date,value}."""
    _verify_request(request)
    try:
        try:
            db = getattr(app.state, 'mongo_db', None)
            if db is None:
                raise ValueError('no mongo')
            out = []
            for d in db['bond_yields'].find({}, {'_id': 0, 'observation_date': 1, 'M2SL': 1}).sort('observation_date', 1):
                date = d.get('observation_date') or d.get('date')
                val = d.get('M2SL') if 'M2SL' in d else d.get('m2sl')
                if date is None or val is None:
                    continue
                try:
                    ds = date.isoformat() if hasattr(date, 'isoformat') else str(date)
                except Exception:
                    ds = str(date)
                try:
                    vv = float(val)
                except Exception:
                    continue
                out.append({'date': ds, 'value': vv})
            return out
        except ValueError:
            return JSONResponse(status_code=500, content={"error": "MONGO_URI not configured"})
    except Exception:
        return JSONResponse(status_code=500, content={"error":"mongodb read failed"})


@app.get('/api/yahoo_btc_latest')
def yahoo_btc_latest(request: Request):
    """Return the most recent daily OHLCV for BTC from Yahoo Finance.

    This is intended as a lightweight live-check endpoint for the frontend.
    It enforces the same referer/origin verification as other API endpoints.
    """
    _verify_request(request)
    try:
        try:
            import yfinance as yf
        except Exception:
            return JSONResponse(status_code=500, content={"error": "yfinance not installed"})

        ticker = yf.Ticker('BTC-USD')
        # fetch last 7 days to be safe and take the last available day
        df = ticker.history(period='7d', interval='1d')
        if df is None or df.empty:
            return JSONResponse(status_code=500, content={"error": "no data from yahoo"})

        last = df.iloc[-1]
        idx = df.index[-1]
        # index may be pandas.Timestamp
        try:
            dt = idx.to_pydatetime()
            date_iso = dt.date().isoformat()
        except Exception:
            date_iso = str(idx)

        out = {
            'date': date_iso,
            'open': float(last['Open']),
            'high': float(last['High']),
            'low': float(last['Low']),
            'close': float(last['Close']),
            'volume': float(last.get('Volume', 0)) if 'Volume' in last.index else 0
        }
        return out
    except Exception as e:
        logging.exception('yahoo_btc_latest failed')
        return JSONResponse(status_code=500, content={"error": "yahoo fetch failed", "detail": str(e)})


@app.get('/_debug/series_counts')
def _debug_series_counts(request: Request):
    """Debug helper: return counts and last document date for indicator collections."""
    _verify_request(request)
    db = getattr(app.state, 'mongo_db', None)
    if db is None:
        return JSONResponse(status_code=500, content={"error": "no mongo"})
    out = {}
    for c in ['onchain_data','ETF_flows','bond_yields','cryptofg']:
        if c in db.list_collection_names():
            cnt = db[c].count_documents({})
            last = None
            cur = db[c].find().sort('date', -1).limit(1)
            for d in cur:
                last = d.get('date') or d.get('observation_date')
            out[c] = {'count': cnt, 'last': (last.isoformat() if hasattr(last, 'isoformat') else str(last))}
        else:
            out[c] = {'count': 0, 'last': None}
    return out
