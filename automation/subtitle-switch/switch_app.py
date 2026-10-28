"""Shared presentation and save-target helpers. Importing this module never starts services or a GUI."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pipeline import InstanceLock, Pipeline
from switch_state import Inventory, read_inbox, write_preferences, flush_preferences, atomic_json
from services import Services, browser, intake_url, command
from metadata import refresh_metadata
from ask_research import ask
import ui_design as design


APP_NAME = 'AI動画字幕図書館司書猫さん'
MIN_WINDOW = (1100, 680)


def window_geometry(screen_width, screen_height, saved=None):
    """Restore only visible, valid window bounds; otherwise use a compact default."""
    if isinstance(saved, dict):
        w, h, x, y = (saved.get(k) for k in ('width', 'height', 'x', 'y'))
        if (all(type(v) is int for v in (w, h, x, y)) and
                MIN_WINDOW[0] <= w <= screen_width and MIN_WINDOW[1] <= h <= screen_height and
                0 <= x <= screen_width - w and 0 <= y <= screen_height - h):
            return f'{w}x{h}+{x}+{y}'
    width = max(MIN_WINDOW[0], min(int(screen_width * .70), screen_width))
    height = max(MIN_WINDOW[1], min(760, screen_height))
    return f'{width}x{height}'


def notebook_column_width(measure, values):
    return max([155, measure('Notebook使用数') + 48] + [measure(value) + 24 for value in values])

STAGE_LABELS = {
    'intake': '重複確認', 'captions': '字幕取得', 'transcript': '字幕OKF',
    'research': '研究ノート', 'review': '検品', 'catalog': '台帳・索引',
    'github': 'GitHub保存・確認', 'notebook': 'Notebook保存・確認',
}
STATUS_LABELS = {
    'pending': '未処理', 'running': '処理中', 'waiting': '待ち', 'attention': '要確認',
    'complete': '保存完了', 'ALREADY_REGISTERED': '登録済み・スキップ',
    'TRANSCRIPT_UNAVAILABLE': '字幕なし（TRANSCRIPT_UNAVAILABLE）',
}
REASON_LABELS = {
    'NOTEBOOK_LOGIN_EXPIRED': 'Notebookのログインを手動で復旧してください',
    'YOUTUBE_ROBOT_CHECK': 'YouTubeの確認待ちです',
    'CLAUDE_QUOTA': 'Claudeの利用枠の回復待ちです',
    'NOTEBOOK_CAPACITY': 'Notebookのソース上限を超えるため待っています',
    'WRITE_RESULT_UNKNOWN': '書き込み結果を確認できません。再送せず読み戻します',
    'DOM_READBACK_UNKNOWN': 'Notebook画面の独立2資料を確認できません',
    'SAVE_BRANCH_REQUIRED': 'GitHub作業フォルダの保存先ブランチを確認してください',
    'RETRY_LIMIT': '原因変更後の再試行上限です。状態を確認してください',
    'TRANSCRIPT_INTEGRITY_MISMATCH': '保存済み字幕の指紋が一致しません',
    'RESEARCH_EVIDENCE_TIME_UNVERIFIED': '研究ノートに字幕で確認できない時刻があります',
}


def display_row(row):
    """One table row, usable in headless acceptance tests without starting Tk."""
    status = ('弾いた：' + row['rejection_reason'] if row['rejected'] else
              STATUS_LABELS.get(row['status'], row['status']))
    if row.get('status_reason') and row['status'] in ('attention', 'waiting'):
        reason = row['status_reason']
        status += '：' + REASON_LABELS.get(reason, reason)
    used = notebook_usage(row)
    if row.get('notebook_capacity_warning'):
        used += '（上限前警告）'
    return tuple((row.get(key) or ('未設定' if key == 'theme' else '取得中…' if key in ('channel', 'published_at', 'lang') else '')) for key in ('title', 'channel', 'published_at', 'lang', 'theme', 'reason')) + (
        STAGE_LABELS.get(row['stage'], row['stage']), status, used)


def notebook_usage(row):
    value = row.get('notebook_sources_used')
    if value is not None and str(value) != 'UNKNOWN':
        return str(value)
    reason = row.get('status_reason', '')
    if reason == 'NOTEBOOK_LOGIN_EXPIRED':
        return 'Notebook 未接続'
    if row.get('stage') == 'notebook' and reason:
        return '読み取り失敗：' + REASON_LABELS.get(reason, reason)
    return '未実行（Notebook 工程の前）'


def toggle_checked(checked, video_id, rejected=False):
    checked = set(checked)
    if rejected:
        checked.discard(video_id)
    elif video_id in checked:
        checked.remove(video_id)
    else:
        checked.add(video_id)
    return checked


def folders(config):
    drive = Path(config.get('drive_root', 'G:/マイドライブ'))
    return {
        key: browser.lab_folder(name, drive_root=drive, lab_name='AI動画研究室',
                                override=config.get(key))
        for key, name in [('inbox', 'AI動画研究室_受け箱'),
                          ('preferences', 'AI動画研究室_好み'),
                          ('channels', 'AI動画研究室_登録チャンネル')]
    }


def save_session(inventory, services, preference_folder, notify=lambda: None, correction="", target_ids=None):
    """Process only the authorized IDs; None retains the legacy internal API."""
    if target_ids is not None:
        target_ids = set(target_ids)
        if not target_ids:
            return
    already_complete = {vid for vid, row in inventory.data['videos'].items() if row['status'] == 'complete'}
    outbox = inventory.path.parent / 'preference_outbox'
    # Preference delivery problems must not stop research.
    flush_preferences(outbox, preference_folder)
    try:
        Pipeline(inventory, services, notify).run(correction, target_ids)
    finally:
        write_preferences(outbox, inventory.preferences(date.today(),
                          saved_ids=(set(inventory.data['videos']) if target_ids is None else target_ids) - already_complete))
        flush_preferences(outbox, preference_folder)


def save_targets(inventory, mode, manual_text='', selected=()):
    """Validate all manual URLs before modifying state, or use selected IDs only."""
    if mode == 'selected':
        return {vid for vid in selected if vid in inventory.data['videos']
                and not inventory.data['videos'][vid]['rejected']}
    if mode != 'manual':
        raise ValueError('UNKNOWN_SAVE_MODE')
    manual = []
    for line in manual_text.splitlines():
        if not line.strip():
            continue
        vid = intake_url.extract_youtube_id(line)
        if not vid:
            raise ValueError('INVALID_YOUTUBE_URL')
        manual.append({'video_id': vid, 'url': intake_url.canonical_youtube_url(vid),
                       **{key: '' for key in ('title', 'channel', 'published_at', 'lang', 'theme', 'kind', 'reason')}})
    inventory.refresh(manual)
    return {row['video_id'] for row in manual if not inventory.data['videos'][row['video_id']]['rejected']}


def main(config_path):
    """Launch the local browser UI; importing this module starts nothing."""
    from web_server import run
    run(config_path)
