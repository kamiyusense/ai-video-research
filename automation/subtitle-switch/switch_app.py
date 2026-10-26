"""Windows thin UI. Importing this module never starts services or a GUI."""
from __future__ import annotations

import json
import queue
import threading
from datetime import date
from pathlib import Path

from pipeline import InstanceLock, Pipeline
from switch_state import Inventory, read_inbox, write_preferences, flush_preferences
from services import Services, browser, intake_url


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
    used = str(row.get('notebook_sources_used', 'UNKNOWN'))
    if row.get('notebook_capacity_warning'):
        used += '（上限前警告）'
    return tuple(row.get(key, '') for key in ('title', 'channel', 'published_at', 'lang', 'theme', 'reason')) + (
        STAGE_LABELS.get(row['stage'], row['stage']), status, used)


def folders(config):
    drive = Path(config.get('drive_root', 'G:/マイドライブ'))
    return {
        key: browser.lab_folder(name, drive_root=drive, lab_name='AI動画研究室',
                                override=config.get(key))
        for key, name in [('inbox', 'AI動画研究室_受け箱'),
                          ('preferences', 'AI動画研究室_好み'),
                          ('channels', 'AI動画研究室_登録チャンネル')]
    }


def save_session(inventory, services, preference_folder, notify=lambda: None, correction=""):
    """Exactly one invocation handles the whole eligible inventory."""
    already_complete = {vid for vid, row in inventory.data['videos'].items() if row['status'] == 'complete'}
    outbox = inventory.path.parent / 'preference_outbox'
    # Preference delivery problems must not stop research.
    flush_preferences(outbox, preference_folder)
    try:
        Pipeline(inventory, services, notify).run(correction)
    finally:
        write_preferences(outbox, inventory.preferences(date.today(),
                          saved_ids=set(inventory.data['videos']) - already_complete))
        flush_preferences(outbox, preference_folder)


def main(config_path):
    import tkinter as tk
    from tkinter import ttk, messagebox

    config = json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    state_dir = Path(config['vault']) / 'subtitle-switch-state'
    state_dir.mkdir(parents=True, exist_ok=True)
    with InstanceLock(state_dir / 'instance.lock'):
        inventory = Inventory(state_dir / 'inventory.json')
        locations = folders(config)
        root = tk.Tk()
        root.title('字幕保存スイッチ')
        root.geometry('1180x650')
        events = queue.Queue()
        busy = False
        show_rejected = tk.BooleanVar(value=False)
        show_processed = tk.BooleanVar(value=False)
        explanation = tk.StringVar(value='保存開始を押すと、一覧の残った動画のGitHub・Notebook保存を許可します。')
        ttk.Label(root, textvariable=explanation).pack(fill='x', padx=10, pady=8)
        columns = ('title', 'channel', 'published_at', 'lang', 'theme', 'reason', 'stage', 'status', 'notebook')
        table = ttk.Treeview(root, columns=columns, show='headings', selectmode='extended')
        names = ('タイトル', 'チャンネル', '公開日', '言語', 'テーマ', '理由', '工程', '状態／待ち理由', 'Notebook使用数')
        for key, name in zip(columns, names):
            table.heading(key, text=name)
            table.column(key, width=120 if key != 'title' else 210)
        table.pack(fill='both', expand=True, padx=10)
        toolbar = ttk.Frame(root)
        toolbar.pack(fill='x', padx=10, pady=6)
        reject_reason = tk.StringVar(value='興味なし')
        ttk.Combobox(toolbar, textvariable=reject_reason, state='readonly',
                     values=('興味なし', 'もう知ってる', '長すぎる', '')).pack(side='left')

        def render():
            table.delete(*table.get_children())
            for row in inventory.visible(show_rejected.get(), show_processed.get()):
                table.insert('', 'end', iid=row['video_id'], values=display_row(row))

        def refresh():
            if busy:
                return
            rows, errors = read_inbox(locations['inbox'])
            inventory.refresh(rows)
            text = ' ／ '.join(error['file'] + '：要確認' for error in errors)
            if not locations['inbox'].is_dir():
                text = '受け箱にアクセスできません（UNKNOWN）。設定とDrive同期を確認してください。'
            explanation.set(text or '保存開始1回で、弾いていない動画を順番に保存します。')
            render()

        def reject(value):
            if busy:
                return
            for vid in table.selection():
                inventory.reject(vid, value, reject_reason.get())
            render()

        ttk.Button(toolbar, text='弾く', command=lambda: reject(True)).pack(side='left', padx=4)
        ttk.Button(toolbar, text='戻す', command=lambda: reject(False)).pack(side='left')
        ttk.Checkbutton(toolbar, text='弾いた動画も表示', variable=show_rejected, command=render).pack(side='left', padx=8)
        ttk.Checkbutton(toolbar, text='完了・登録済みも表示', variable=show_processed, command=render).pack(side='left', padx=8)
        ttk.Button(toolbar, text='一覧を更新', command=refresh).pack(side='left')
        correction = tk.StringVar(value='')
        ttk.Label(root, text='失敗から再開する場合だけ、直した原因を選択（同じ原因の再試行はしません）').pack(anchor='w', padx=10)
        ttk.Combobox(root, textvariable=correction, state='readonly', values=(
            '', '手動ログインを復旧', '設定を修正', '利用枠の回復を確認', '字幕取得条件を修正')).pack(fill='x', padx=10)
        urls = tk.Text(root, height=3)
        ttk.Label(root, text='手動URL（1行1本、短縮URL・時刻つきも可）').pack(anchor='w', padx=10)
        urls.pack(fill='x', padx=10)

        def start():
            nonlocal busy
            if busy:
                return
            manual = []
            for line in urls.get('1.0', 'end').splitlines():
                if not line.strip():
                    continue
                vid = intake_url.extract_youtube_id(line)
                if not vid:
                    messagebox.showerror('URL要確認', 'YouTube URLを確認してください。')
                    return
                manual.append({'video_id': vid, 'url': intake_url.canonical_youtube_url(vid),
                               **{key: '' for key in ('title', 'channel', 'published_at', 'lang', 'theme', 'kind', 'reason')}})
            inventory.refresh(manual)
            urls.delete('1.0', 'end')
            correction_value = correction.get()
            busy = True
            save_button.configure(state='disabled')

            def worker():
                try:
                    services = Services(config)
                    save_session(inventory, services, locations['preferences'], lambda: events.put('render'), correction_value)
                    pending = len(list((state_dir / 'preference_outbox').glob('preferences_*.json')))
                    events.put(('done', f'処理終了。好みメモ送信待ち：{pending}件。待ち／要確認は一覧を確認してください。'))
                except Exception:
                    events.put(('done', '要確認：処理を停止しました。設定と状態を確認してください（UNKNOWN）。'))
            threading.Thread(target=worker, daemon=False).start()

        save_button = ttk.Button(root, text='保存開始', command=start)
        save_button.pack(pady=10)

        def poll():
            nonlocal busy
            while not events.empty():
                event = events.get_nowait()
                if isinstance(event, tuple):
                    busy = False
                    save_button.configure(state='normal')
                    explanation.set(event[1])
                render()
            root.after(200, poll)

        def close():
            if busy:
                messagebox.showinfo('処理中', '工程の終了まで画面を開いておいてください。')
                return
            root.destroy()

        root.protocol('WM_DELETE_WINDOW', close)
        refresh()
        poll()
        root.mainloop()
