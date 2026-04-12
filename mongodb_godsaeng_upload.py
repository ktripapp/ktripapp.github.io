import os
import requests
from datetime import datetime, timezone
import argparse
import time
import hashlib
import json
from pathlib import Path


HISTORY_DIR = Path('monitoring')
HISTORY_FILE = HISTORY_DIR / 'godsaeng_history.jsonl'
LATEST_FILE = HISTORY_DIR / 'godsaeng_latest.json'


def write_local_entry(url: str, status_code: int, content: bytes):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    content_hash = hashlib.sha256(content).hexdigest() if content else None
    entry = {
        'url': url,
        'status_code': status_code,
        'content_hash': content_hash,
        'content_len': len(content) if content else 0,
        'checked_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
    }
    # append history line
    with open(HISTORY_FILE, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + '\n')
    # update latest
    with open(LATEST_FILE, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, indent=2))
    return entry


def main():
    parser = argparse.ArgumentParser(description='Monitor https://godsaeng.streamlit.app and write results to local files')
    parser.add_argument('--monitor', action='store_true', help='Run monitoring against https://godsaeng.streamlit.app/')
    parser.add_argument('--url', type=str, default='https://godsaeng.streamlit.app/', help='URL to monitor')
    parser.add_argument('--interval-hours', type=float, default=3.0, help='Interval between checks in hours (default: 3)')
    parser.add_argument('--once', action='store_true', help='Run only once and exit (useful for cron/GitHub Actions)')
    args = parser.parse_args()

    if args.monitor:
        interval_seconds = max(1, args.interval_hours) * 3600
        print(f'Starting monitor for {args.url} every {args.interval_hours} hours')
        try:
            while True:
                status, content = fetch_godsaeng_page(args.url)
                try:
                    rec = write_local_entry(args.url, status, content)
                    print(f'Checked {args.url}: status={status}, len={rec["content_len"]}, hash={rec["content_hash"]}')
                except Exception as e:
                    print('Error writing local entry:', e)

                if args.once:
                    break

                try:
                    time.sleep(interval_seconds)
                except KeyboardInterrupt:
                    print('Monitor interrupted, exiting')
                    break
        except Exception as exc:
            print('Error in monitor loop:', exc)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
