"""Metadata-only lookup with a persistent cache; callers run it off the UI thread."""
import json
import re
import time
from pathlib import Path

from switch_state import atomic_json


def refresh_metadata(rows, cache_path, run, sleep=time.sleep, notify=lambda *_: None, failures=None):
    failures = failures if failures is not None else set()
    path = Path(cache_path)
    try:
        cache = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    except (ValueError, OSError):
        cache = {}
    first = True
    for row in rows:
        vid = row['video_id']
        values = cache.get(vid) or {}
        keys = ('channel', 'published_at', 'lang')
        missing = [key for key in keys if not (row.get(key) or values.get(key))]
        if not missing:
            notify(vid, {key: row.get(key) or values.get(key) for key in keys})
            continue
        if vid in failures:
            notify(vid, {key: row.get(key) or values.get(key) or '取得失敗：原因を直してから再起動' for key in keys})
            continue
        if missing:
            notify(vid, {key: row.get(key) or values.get(key) or '取得中…' for key in keys})
            if not first:
                sleep(2)
            first = False
            try:
                result = run(['yt-dlp', '--ignore-config', '--skip-download', '--no-playlist',
                              '--no-warnings', '--socket-timeout', '30', '--dump-single-json', row['url']])
                if result.returncode:
                    raise ValueError('情報を取得できません')
                data = json.loads(result.stdout)
                if data.get('id') != vid:
                    raise ValueError('動画IDが一致しません')
                published = data.get('upload_date') or ''
                if re.fullmatch(r'\d{8}', published):
                    published = f'{published[:4]}-{published[4:6]}-{published[6:]}'
                else:
                    published = ''
                fetched = {'channel': data.get('channel') or data.get('uploader') or '',
                           'published_at': published, 'lang': data.get('language') or ''}
                values = {key: values.get(key) or fetched[key] for key in keys}
                cache[vid] = values
                atomic_json(path, cache)
                if any(not (row.get(key) or values.get(key)) for key in keys):
                    failures.add(vid)
            except Exception:
                failures.add(vid)
        notify(vid, {key: row.get(key) or values.get(key) or '取得失敗：情報なし・接続を確認' for key in ('channel', 'published_at', 'lang')})
