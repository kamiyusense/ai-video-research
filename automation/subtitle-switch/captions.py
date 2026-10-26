"""Pure caption conversion. No fetching in this module."""
from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal


def select_track(metadata):
    for kind, tracks in [('manual', metadata.get('subtitles', {})),
                         ('automatic', metadata.get('automatic_captions', {}))]:
        languages = sorted(tracks, key=lambda lang: (not lang.startswith('ja'), not lang.startswith('en'), lang))
        for language in languages:
            for track in tracks[language]:
                if track.get('ext') == 'json3' and track.get('url'):
                    return kind, language, track['url']
    return None


def parse_json3(document, automatic=False):
    cues, previous, previous_end = [], '', -1
    for event in document.get('events', []):
        if 'segs' not in event:
            continue
        text = ''.join(segment.get('utf8', '') for segment in event['segs'])
        # json3 line breaks are presentation; preserve all other characters.
        text = text.replace('\r\n', ' ').replace('\n', ' ')
        if not text.strip():
            continue
        start = event.get('tStartMs')
        if not isinstance(start, (int, float)) or not math.isfinite(start) or start < 0:
            raise ValueError('INVALID_CAPTION_TIME')
        original = text
        if automatic and start < previous_end:
            overlap = 0
            for size in range(1, min(len(previous), len(text)) + 1):
                if previous[-size:] == text[:size]:
                    overlap = size
            text = text[overlap:]
        previous = original
        duration = event.get('dDurationMs', 0)
        if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration < 0:
            raise ValueError('INVALID_CAPTION_DURATION')
        previous_end = start + duration
        if text.strip():
            cues.append((str(Decimal(str(start)) / 1000), text))
    return cues


def build_okf(row, cues, kind, language):
    if not cues:
        raise ValueError('TRANSCRIPT_UNAVAILABLE')
    body = '\n'.join(f'[{start}] {text}' for start, text in cues) + '\n'
    vid = row['video_id']
    metadata = {
        'okf_version': '0.2', 'type': 'TRANSCRIPT',
        'title': f'【字幕原文】{row.get("title", "")} [{vid}]',
        'description': '取得した字幕原文（自動字幕の正確性は未確認）',
        'tags': ['AI技術研究室', '動画研究'],
        'video_id': vid, 'logical_id': f'youtube:{vid}:transcript',
        'research_logical_id': f'youtube:{vid}:research',
        'resource': row['url'], 'canonical_url': row['url'],
        'published_at': row.get('published_at') or 'UNKNOWN',
        'language': language, 'caption_kind': kind, 'time_source': 'YOUTUBE_CAPTION',
        'acquisition_method': 'YT_DLP_JSON3',
        'deduplication': 'rolling_overlap_v1' if kind == 'automatic' else 'NONE',
        'sha256': hashlib.sha256(body.encode()).hexdigest(),
        'cue_count': len(cues), 'line_count': len(cues),
        'transcript_status': 'UNVERIFIED',
    }
    # JSON scalars/lists are valid YAML and prevent metadata injection.
    front = '\n'.join(f'{key}: {json.dumps(value, ensure_ascii=False)}' for key, value in metadata.items())
    return f'---\n{front}\n---\n{body}', metadata
