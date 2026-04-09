from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os
from datetime import datetime

# Try to load local secrets file if present
MONGO_URI = None
try:
    import secrets_local
    MONGO_URI = getattr(secrets_local, 'MONGO_URI', None)
except Exception:
    MONGO_URI = None

if not MONGO_URI:
    MONGO_URI = os.getenv('MONGO_URI') or os.getenv('MONGO')

app = Flask(__name__)
CORS(app)

client = None
db = None
collection = None
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # ensure server is reachable
        client.admin.command('ping')
        db = client.get_database('coins')
        collection = db.get_collection('historical_daily_data')
    except Exception as e:
        collection = None
        app.logger.warning('MongoDB 연결 실패: %s', e)
else:
    app.logger.warning('MONGO_URI가 설정되지 않았습니다. 환경변수 또는 secrets_local.MONGO_URI를 확인하세요.')


def _to_iso(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    try:
        # fallback for types that can be stringified
        return str(val)
    except Exception:
        return None


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'mongo': client is not None and collection is not None})


@app.route('/api/historical_daily_data')
def historical_daily_data():
    if collection is None:
        return jsonify({'error': 'MongoDB 연결이 없습니다.'}), 500

    # optional query params: limit, start, end
    try:
        limit = int(request.args.get('limit', 1000))
    except Exception:
        limit = 1000

    start = request.args.get('start')  # ISO date
    end = request.args.get('end')

    query = {}
    if start or end:
        time_query = {}
        if start:
            try:
                time_query['$gte'] = datetime.fromisoformat(start)
            except Exception:
                pass
        if end:
            try:
                time_query['$lte'] = datetime.fromisoformat(end)
            except Exception:
                pass
        if time_query:
            # prefer 'date' then 'timestamp'
            query['$or'] = [{'date': time_query}, {'timestamp': time_query}]

    # prefer sorting by date or timestamp if present
    sort_fields = []
    try:
        # try to sort by date -> timestamp -> _id
        sort_fields = [('date', 1)]
        # perform find
        cursor = collection.find(query).sort(sort_fields).limit(limit)
    except Exception:
        cursor = collection.find(query).limit(limit)

    out = []
    for doc in cursor:
        # extract date-like field
        date_val = doc.get('date') or doc.get('timestamp') or doc.get('_id')
        # extract close-like field
        close_val = (doc.get('close') if 'close' in doc else
                     doc.get('price') if 'price' in doc else
                     doc.get('close_price') if 'close_price' in doc else
                     doc.get('value') if 'value' in doc else None)

        try:
            if close_val is not None:
                close_val = float(close_val)
        except Exception:
            close_val = None

        out.append({'date': _to_iso(date_val), 'close': close_val, '_raw': {k: v for k, v in doc.items() if k in ['symbol','volume']}})

    return jsonify(out)


if __name__ == '__main__':
    # default port 5000, change with PORT env var
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
