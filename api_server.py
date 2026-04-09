from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import pandas as pd

app = FastAPI()


def _serialize_doc(doc: dict):
    # Convert common non-JSON types (ObjectId, datetime) to strings
    try:
        from bson import ObjectId
    except Exception:
        ObjectId = None

    out = {}
    for k, v in doc.items():
        if ObjectId is not None and isinstance(v, ObjectId):
            out[k] = str(v)
        elif hasattr(v, 'isoformat'):
            try:
                out[k] = v.isoformat()
            except Exception:
                out[k] = str(v)
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
            if mongo_uri:
            try:
                from pymongo import MongoClient
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": "pymongo not installed", "detail": str(e)})

                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            db = client['coins']
            coll = db['historical_daily_data']
            cursor = coll.find().sort('date', 1)
            docs = [_serialize_doc(d) for d in cursor]
            return docs

        # Fallback to data.parquet
        file_path = os.path.join(os.path.dirname(__file__), 'data.parquet')
        if not os.path.exists(file_path):
            return JSONResponse(status_code=500, content={"error": "no data source available", "detail": "MONGO_URI not set and data.parquet missing"})

        df = pd.read_parquet(file_path)
        return df.to_dict(orient='records')
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "internal server error", "detail": str(e)})