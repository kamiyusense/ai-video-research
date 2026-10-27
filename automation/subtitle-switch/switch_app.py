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
import ui_design as design


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
        root.geometry('1420x800')
        root.minsize(1050, 640)
        root.configure(background=design.BACKGROUND)
        root.option_add('*Font', ('Yu Gothic UI', 10))
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background=design.WHITE)
        style.configure('TLabel', background=design.WHITE)
        style.configure('TCheckbutton', background=design.WHITE)
        style.configure('Treeview', background=design.WHITE, fieldbackground=design.WHITE, rowheight=36, font=('Yu Gothic UI', 10))
        style.configure('Treeview.Heading', background='#f8f8fa', foreground='#202632', padding=8, font=('Yu Gothic UI', 10))
        style.layout('Treeview.Heading', [('Treeheading.cell', {'sticky': 'nswe', 'children': [
            ('Treeheading.border', {'sticky': 'nswe', 'children': [
                ('Treeheading.padding', {'sticky': 'nswe', 'children': [
                    ('Treeheading.image', {'side': 'left', 'sticky': ''}),
                    ('Treeheading.text', {'side': 'left', 'sticky': 'we'})]})]})]})])
        style.configure('Card.TFrame', background=design.WHITE, relief='solid', borderwidth=1)
        style.configure('Accent.TButton', background=design.RED, foreground=design.WHITE, padding=(28, 12), font=('Yu Gothic UI', 14, 'bold'))
        style.map('Accent.TButton', background=[('disabled', '#e59aa4'), ('active', '#d4182c')])
        images = {kind: design.photo(tk, root, kind, 22) for kind in
                  ('document','play','calendar','globe','tag','bulb','gear','wave','notebook','skip','back','refresh','info')}
        images['app'] = design.photo(tk, root, 'app', 32, True)
        images['save'] = design.photo(tk, root, 'book', 32, True)
        root.iconphoto(True, images['app'])
        events = queue.Queue()
        busy = False
        show_rejected = tk.BooleanVar(value=False)
        show_processed = tk.BooleanVar(value=False)
        explanation = tk.StringVar(value='手動保存は入力URLだけ、選択保存は選択行だけを保存します。')
        banner = tk.Frame(root, background=design.PINK, padx=16, pady=14)
        banner.pack(fill='x', padx=18, pady=(14, 10))
        tk.Label(banner, image=images['info'], background=design.PINK).pack(side='left', padx=(0, 12))
        tk.Label(banner, textvariable=explanation, background=design.PINK, anchor='w', wraplength=1250).pack(side='left', fill='x', expand=True)
        card = ttk.Frame(root, style='Card.TFrame', padding=8)
        card.pack(fill='both', expand=True, padx=18, pady=6)
        columns = tuple(col[0] for col in design.COLUMNS)
        table = ttk.Treeview(card, columns=columns, show='headings', selectmode='extended')
        for key, name, icon, width in design.COLUMNS:
            table.heading(key, text=' ' + name, image=images[icon])
            table.column(key, width=width, minwidth=65, stretch=key in ('title', 'status'))
        table.tag_configure('attention', background=design.PINK)
        table.tag_configure('running', background='#fff3f5')
        scroll_x = ttk.Scrollbar(card, orient='horizontal', command=table.xview)
        scroll_y = ttk.Scrollbar(card, orient='vertical', command=table.yview)
        table.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        table.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        card.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)
        controls = ttk.Frame(root, style='Card.TFrame', padding=16)
        controls.pack(fill='x', padx=18, pady=(8, 16))
        toolbar = ttk.Frame(controls)
        toolbar.pack(fill='x', pady=(0, 10))
        reject_reason = tk.StringVar(value=design.REJECT_REASONS[0])
        ttk.Combobox(toolbar, textvariable=reject_reason, state='normal', width=18,
                     values=design.REJECT_REASONS).pack(side='left')

        def render():
            selected = table.selection()
            table.delete(*table.get_children())
            active = None
            for row in inventory.visible(show_rejected.get(), show_processed.get()):
                table.insert('', 'end', iid=row['video_id'], values=display_row(row), tags=(design.row_tag(row),))
                if row['status'] == 'running':
                    active = row['video_id']
            table.selection_set([vid for vid in selected if table.exists(vid)])
            if active:
                table.see(active)

        def refresh():
            if busy:
                return
            rows, errors = read_inbox(locations['inbox'])
            inventory.refresh(rows)
            text = ' ／ '.join(error['file'] + '：要確認' for error in errors)
            if not locations['inbox'].is_dir():
                text = '受け箱にアクセスできません（UNKNOWN）。設定とDrive同期を確認してください。'
            explanation.set(text or '手動保存は入力URLだけ、選択保存は選択行だけを保存します。')
            render()

        def reject(value):
            if busy:
                return
            for vid in table.selection():
                inventory.reject(vid, value, reject_reason.get())
            render()

        ttk.Button(toolbar, text='弾く', image=images['skip'], compound='left', command=lambda: reject(True)).pack(side='left', padx=4)
        ttk.Button(toolbar, text='戻す', image=images['back'], compound='left', command=lambda: reject(False)).pack(side='left')
        ttk.Checkbutton(toolbar, text='弾いた動画も表示', variable=show_rejected, command=render).pack(side='left', padx=8)
        ttk.Checkbutton(toolbar, text='完了・登録済みも表示', variable=show_processed, command=render).pack(side='left', padx=8)
        ttk.Button(toolbar, text='一覧を更新', image=images['refresh'], compound='left', command=refresh).pack(side='left')
        correction = tk.StringVar(value='')
        ttk.Label(controls, text='失敗から再開する場合だけ、直した原因を選択（同じ原因の再試行はしません）').pack(anchor='w', padx=10)
        ttk.Combobox(controls, textvariable=correction, state='readonly', values=(
            '', '手動ログインを復旧', '設定を修正', '利用枠の回復を確認', '字幕取得条件を修正')).pack(fill='x', padx=10)
        urls = tk.Text(controls, height=3, relief='solid', borderwidth=1)
        ttk.Label(controls, text='手動URL（1行1本、短縮URL・時刻つきも可）').pack(anchor='w', padx=10)
        urls.pack(fill='x', padx=10)

        def start(mode):
            nonlocal busy
            if busy:
                return
            try:
                targets = save_targets(inventory, mode, urls.get('1.0', 'end'), table.selection())
            except ValueError:
                messagebox.showerror('URL要確認', 'YouTube URLを確認してください。')
                return
            if not targets:
                return
            if mode == 'manual':
                urls.delete('1.0', 'end')
            render()
            correction_value = correction.get()
            busy = True
            for button in save_buttons:
                button.configure(state='disabled')

            def worker():
                try:
                    services = Services(config)
                    save_session(inventory, services, locations['preferences'], lambda: events.put('render'), correction_value, targets)
                    pending = len(list((state_dir / 'preference_outbox').glob('preferences_*.json')))
                    events.put(('done', f'処理終了。好みメモ送信待ち：{pending}件。待ち／要確認は一覧を確認してください。'))
                except Exception:
                    events.put(('done', '要確認：処理を停止しました。設定と状態を確認してください（UNKNOWN）。'))
            threading.Thread(target=worker, daemon=False).start()

        button_bar = ttk.Frame(controls)
        button_bar.pack(pady=(12, 0))
        save_buttons = []
        for mode, label in design.SAVE_BUTTONS:
            button = ttk.Button(button_bar, text=label, image=images['save'], compound='left',
                                style='Accent.TButton', command=lambda value=mode: start(value))
            button.pack(side='left', padx=10)
            save_buttons.append(button)

        def poll():
            nonlocal busy
            while not events.empty():
                event = events.get_nowait()
                if isinstance(event, tuple):
                    busy = False
                    for button in save_buttons:
                        button.configure(state='normal')
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
