"""Metadata-only lookup with a persistent cache; callers run it off the UI thread."""
import json
import re
import time
from pathlib import Path

from switch_state import atomic_json

SHOWN = ('channel', 'published_at', 'lang')
# title: inbox rows bring their own; manual-URL rows only get one from this lookup.
KEYS = SHOWN + ('ja_dub', 'title', 'views')


def views_text(count):
    """Short play count; '不明' (not empty) so a video without one is not looked up again."""
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return '不明'
    if count >= 10 ** 8:
        return f'{count / 10 ** 8:.1f}億回'
    if count >= 10 ** 6:
        return f'{count // 10 ** 4}万回'
    return f'{count / 10 ** 4:.1f}万回' if count >= 10 ** 4 else f'{count:,}回'


def japanese_dub(data):
    """'日本語' for Japanese videos, else whether YouTube offers a Japanese (auto-)dubbed audio track.

    Measured 2026-10-28 with yt-dlp: dubbed tracks are audio-only formats whose language starts
    with 'ja' (format_note like '日本語 - dubbed-auto'). Japanese auto-captions are not dubbing."""
    if (data.get('language') or '').lower().startswith('ja'):
        return '日本語'
    tracks = [f for f in data.get('formats') or [] if f.get('vcodec') == 'none']
    return 'あり' if any((f.get('language') or '').lower().startswith('ja') for f in tracks) else 'なし'


def _known(row, values, key):
    if key == 'ja_dub' and (row.get('lang') or values.get('lang') or '').lower().startswith('ja'):
        return '日本語'
    return row.get(key) or values.get(key)


def _extra(row, values):
    return {key: _known(row, values, key) or '' for key in ('ja_dub', 'title', 'views')}


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
        keys = KEYS
        # A missing title alone never starts a lookup (inbox rows may omit it); a manual-URL
        # row lacks channel/date/lang too, so its lookup runs and brings the title along.
        missing = [key for key in keys if key != 'title' and not _known(row, values, key)]
        if not missing:
            notify(vid, {key: _known(row, values, key) or '' for key in keys})
            continue
        if vid in failures:
            notify(vid, {**{key: _known(row, values, key) or '取得失敗：原因を直してから再起動' for key in SHOWN}, **_extra(row, values)})
            continue
        if missing:
            notify(vid, {**{key: _known(row, values, key) or '取得中…' for key in SHOWN}, **_extra(row, values)})
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
                           'published_at': published, 'lang': data.get('language') or '',
                           'ja_dub': japanese_dub(data), 'title': data.get('title') or '',
                           'views': views_text(data.get('view_count'))}
                values = {key: values.get(key) or fetched[key] for key in keys}
                cache[vid] = values
                atomic_json(path, cache)
                if any(not _known(row, values, key) for key in SHOWN):
                    failures.add(vid)
            except Exception:
                failures.add(vid)
        notify(vid, {**{key: _known(row, values, key) or '取得失敗：情報なし・接続を確認' for key in SHOWN}, **_extra(row, values)})
