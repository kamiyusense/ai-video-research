"""Loopback-only browser shell. No service, browser or server runs on import."""
from __future__ import annotations

import copy
import json
import mimetypes
import os
import secrets
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import switch_app as app
from ask_research import GROK_REASON, MAX_QUESTION, ask
from metadata import refresh_metadata
from pipeline import InstanceLock, StageFailure
from services import Services, command
from switch_state import Inventory, read_inbox
from translate_title import TitleTranslator, needs_translation

ROOT = Path(__file__).resolve().parent
FONTS = ('ZenMaruGothic-Black', 'KiwiMaru-Medium', 'DelaGothicOne-Regular',
         'HachiMaruPop-Regular', 'DotGothic16-Regular', 'PottaOne-Regular')
FAILURE_LABELS = {
    'CLAUDE_API_CONFIGURATION_BLOCKED': 'PCにAPIキー等の設定があるためClaudeを呼びませんでした（キーなしの購読ログインだけを使います）',
    'CLAUDE_COMMAND_NOT_FOUND': 'PCでClaude Codeが見つかりません',
    'INBOX_UNAVAILABLE': '受け箱フォルダが見つかりません（UNKNOWN）。Googleドライブの同期を確認してください',
}
CORRECTIONS = ('', '手動ログインを復旧', '設定を修正', '利用枠の回復を確認', '字幕取得条件を修正')


def short_cell(text, limit=12):
    text = str(text)
    return {'text': text if len(text) <= limit else text[:limit - 1] + '…', 'full': text}


def table_row(row, metadata=None):
    values = app.display_row({**row, **(metadata or {})})
    cells = [short_cell(v, n) for v, n in zip(values, (200, 40, 10, 8, 15, 9, 10, 8, 8))]
    # Keep meaningful short labels while retaining the complete explanation on hover.
    cells[7]['text'] = ('弾いた' if row['rejected'] else app.STATUS_LABELS.get(row['status'], row['status']).split('（')[0])[:8]
    if row.get('notebook_sources_used') is None or str(row.get('notebook_sources_used')) == 'UNKNOWN':
        cells[8]['text'] = '未接続' if row.get('status_reason') == 'NOTEBOOK_LOGIN_EXPIRED' else '未実行' if row.get('stage') != 'notebook' else '要確認'
    lang = (metadata or {}).get('lang') or row.get('lang') or ''
    return {'id': row['video_id'], 'cells': cells, 'rejected': row['rejected'], 'status': row['status'],
            'url': 'https://www.youtube.com/watch?v=' + row['video_id'], 'translate': needs_translation(lang)}


class Controller:
    """One mutation worker; snapshots are published at the pipeline checkpoints."""
    def __init__(self, config, inventory, state_dir, *, service_factory=Services,
                 session=app.save_session, question=ask, metadata=refresh_metadata):
        self.config, self.inventory, self.state_dir = config, inventory, Path(state_dir)
        self.locations = app.folders(config)
        self.service_factory, self.session = service_factory, session
        self.question, self.metadata = question, metadata
        self.guard = threading.RLock()
        self.checked = set()
        self.show_rejected = self.show_processed = False
        self.busy = False
        self.cat = 'idle'
        self.notice = '手動保存は入力URLだけ、選択保存はチェックした行だけを保存します。'
        self.answer = ''
        self.metadata_values, self.metadata_failures = {}, set()
        self.rows = []
        self.worker = None
        self.translator = TitleTranslator(self.state_dir / 'title_ja_cache.json')
        self.publish()

    def publish(self):
        with self.guard:
            self.rows = [table_row(row, self.metadata_values.get(row['video_id']))
                         for row in self.inventory.visible(self.show_rejected, self.show_processed)]

    def snapshot(self):
        with self.guard:
            return copy.deepcopy({'rows': self.rows, 'checked': sorted(self.checked),
                                  'busy': self.busy, 'cat': self.cat, 'notice': self.notice,
                                  'answer': self.answer, 'grok_reason': GROK_REASON})

    def _start(self, action, job):
        # Caller owns guard; setting busy precedes spawning so duplicate POSTs cannot race.
        self.busy, self.cat = True, 'walk'
        self.notice = action + '中…'

        def work():
            failed = False
            try:
                before = {vid: row.get('status') for vid, row in self.inventory.data['videos'].items()}
                job()
                # Only rows this operation moved into attention/waiting count; old leftovers
                # (e.g. an earlier run's attention row) stay visible in the list, not on the cat.
                failed = any(row['status'] in ('attention', 'waiting') and before.get(vid) != row['status']
                             for vid, row in self.inventory.data['videos'].items())
            except subprocess.TimeoutExpired:
                failed = True
                self.notice = '要確認：Claudeの返事が時間内に来ませんでした（UNKNOWN）。'
                if action == '質問':
                    self.answer = 'Claudeの返事が時間内に来ませんでした（UNKNOWN）。もう一度送る前に、少し待ってください。'
            except (ValueError, StageFailure) as error:
                # Our own Japanese messages (no secrets); show them where the owner looks.
                failed = True
                message = FAILURE_LABELS.get(str(error), str(error))
                self.notice = '要確認：' + message
                if action == '質問':
                    self.answer = message
            except Exception:
                failed = True
                self.notice = '要確認：処理を停止しました。設定と状態を確認してください（UNKNOWN）。'
            finally:
                with self.guard:
                    self.busy, self.cat = False, 'error' if failed else 'done'
                    if self.notice.endswith('中…'):
                        self.notice = action + '終了。待ち／要確認は一覧を確認してください。'
                    self.publish()

        self.worker = threading.Thread(target=work, daemon=False)
        self.worker.start()

    def operate(self, data):
        if not isinstance(data, dict) or not isinstance(data.get('action'), str):
            raise ValueError('操作を確認してください')
        action = data['action']
        with self.guard:
            if self.busy:
                raise ValueError('処理中です。工程の終了を待ってください')
            if action == 'filters':
                if any(type(data.get(k)) is not bool for k in ('rejected', 'processed')):
                    raise ValueError('表示指定を確認してください')
                self.show_rejected, self.show_processed = data['rejected'], data['processed']
                self.publish()
            elif action in ('check', 'check_all'):
                visible = {r['id'] for r in self.rows}
                if action == 'check':
                    vid = data.get('id')
                    if not isinstance(vid, str) or vid not in visible:
                        raise ValueError('一覧の行を選択してください')
                    self.checked.symmetric_difference_update({vid})
                else:
                    self.checked = self.checked - visible if visible <= self.checked else self.checked | visible
            elif action in ('reject', 'restore'):
                reason = data.get('reason', '')
                if not isinstance(reason, str) or len(reason) > 200:
                    raise ValueError('理由は200文字以内で入力してください')
                targets = self.checked & {r['id'] for r in self.rows}
                for vid in targets:
                    self.inventory.reject(vid, action == 'reject', reason)
                self.checked -= targets
                self.publish()
            elif action == 'refresh':
                def refresh():
                    if not self.locations['inbox'].is_dir():
                        raise ValueError('INBOX_UNAVAILABLE')
                    rows, errors = read_inbox(self.locations['inbox'])
                    self.inventory.refresh(rows)
                    self.metadata_values.clear()
                    self.notice = ' ／ '.join(e['file'] + '：要確認' for e in errors) or '一覧を更新しました。'
                    self.publish()
                    def received(vid, values):
                        with self.guard:
                            self.metadata_values[vid] = values
                            self.publish()
                    self.metadata(rows, self.state_dir / 'metadata_cache.json', command,
                                  notify=received, failures=self.metadata_failures)
                self._start('一覧更新', refresh)
            elif action in ('manual', 'selected'):
                text, correction = data.get('urls', ''), data.get('correction', '')
                if not isinstance(text, str) or len(text) > 32000 or correction not in CORRECTIONS:
                    raise ValueError('URLまたは再開原因を確認してください')
                # Visible checked rows only: hidden rows cannot be saved accidentally.
                selected = self.checked & {r['id'] for r in self.rows}
                targets = app.save_targets(self.inventory, action, text, selected)
                if targets:
                    def save():
                        self.session(self.inventory, self.service_factory(self.config),
                                     self.locations['preferences'], self.publish, correction, targets)
                        pending = len(list((self.state_dir / 'preference_outbox').glob('preferences_*.json')))
                        self.notice = f'処理終了。好みメモ送信待ち：{pending}件。待ち／要確認は一覧を確認してください。'
                    self.publish()
                    self._start('保存', save)
            elif action == 'ask':
                text = data.get('question')
                if data.get('provider', 'claude') != 'claude':
                    raise ValueError(GROK_REASON)
                if not isinstance(text, str) or not 1 <= len(text.strip()) <= MAX_QUESTION:
                    raise ValueError('質問は1〜2000文字で入力してください')
                self.answer = ''
                # Checked visible rows narrow the question to those videos' notes.
                chosen = sorted(self.checked & {r['id'] for r in self.rows})
                def question():
                    self.answer = self.question(text, self.config['repository'], self.state_dir / 'question_logs',
                                                video_ids=chosen or None)
                self._start('質問', question)
            else:
                raise ValueError('未対応の操作です')
            return self.snapshot()

    def translate(self, data):
        vid = data.get('id') if isinstance(data, dict) else None
        with self.guard:
            row = self.inventory.data['videos'].get(vid) if isinstance(vid, str) else None
            if row is None:
                raise ValueError('一覧の行を確認してください')
            title, title_ja = row.get('title', ''), row.get('title_ja', '')
        return {'id': vid, 'ja': self.translator.translate(vid, title, title_ja)}


def load_manifest(folder, play=False):
    """Validate the shipped manifests and every referenced frame before use."""
    try:
        doc = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        if any(type(doc.get(k)) is not int or not 1 <= doc[k] <= 1024 for k in ('frame_width', 'frame_height')):
            return None
        if play:
            if doc['look']['directions'] != 8:
                return None
            groups = [('look', 8)] + [(k, doc[k]['frames']) for k in ('punch_left', 'punch_right')]
            for k in ('punch_left', 'punch_right'):
                if not 0 < doc[k]['fps'] <= 60:
                    return None
            if not 0 < doc.get('punch_radius_px', 70) <= 300 or not .1 <= doc.get('punch_cooldown_sec', .6) <= 10:
                return None
            hotspot = doc['cursor']['hotspot']
            if len(hotspot) != 2 or any(type(v) is not int or not 0 <= v < 32 for v in hotspot):
                return None
            if not (folder / 'cursor/teaser_32.png').is_file():
                return None
        else:
            if any(type(doc['face'].get(k)) is not int or not 1 <= doc['face'][k] <= 1024 for k in ('frame_width', 'frame_height')):
                return None
            groups = [(k, doc['states'][k]['frames']) for k in ('idle', 'walk', 'done', 'error')]
            for k, count in groups:
                if not 0 < doc['states'][k]['fps'] <= 60:
                    return None
                face = doc['face']['states'][k]
                if not 0 < face['fps'] <= 60 or type(face['frames']) is not int or not 1 <= face['frames'] <= 120:
                    return None
                if not all((folder / f'face/{k}/face_{k}_{i:02}.png').is_file() for i in range(face['frames'])):
                    return None
        for k, count in groups:
            if type(count) is not int or not 1 <= count <= 120:
                return None
            if not all((folder / f'{k}/{k}_{i:02}.png').is_file() for i in range(count)):
                return None
        return doc
    except (OSError, ValueError, KeyError, TypeError):
        return None


def boot_data():
    return {'font': secrets.randbelow(len(FONTS)), 'fonts': FONTS,
            'sprites': load_manifest(ROOT / 'assets/cat_sprites'),
            'play': load_manifest(ROOT / 'assets/cat_play', True), 'grok_reason': GROK_REASON}


def render_page(boot, asset_base='/assets/', auth='', nonce='preview'):
    css = (ROOT / 'web/style.css').read_text(encoding='utf-8')
    css += '\n' + '\n'.join(f'@font-face{{font-family:title{i};src:url("{asset_base}fonts/{name}-title.ttf{auth}") format("truetype");font-display:swap}}' for i, name in enumerate(FONTS))
    js = '\n'.join((ROOT / 'web' / name).read_text(encoding='utf-8') for name in ('cat.js', 'app.js'))
    data = json.dumps({**boot, 'asset_base': asset_base, 'auth': auth}, ensure_ascii=False).replace('<', '\\u003c')
    html = (ROOT / 'web/index.html').read_text(encoding='utf-8')
    return html.replace('<!--STYLE-->', '<style>' + css + '</style>').replace('<!--ICONS-->', (ROOT / 'web/icons.svg').read_text(encoding='utf-8')).replace('<!--SCRIPT-->', f'<script nonce="{nonce}">const BOOT={data};\n{js}</script>')


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    def handle_error(self, request, client_address):
        # Tracebacks from HTTP request handling must not expose URLs/secrets.
        pass

    def __init__(self, controller):
        self.controller = controller
        self.key = secrets.token_urlsafe(32)
        self.nonce = secrets.token_urlsafe(24)
        self.boot = boot_data()
        self.last_heartbeat = time.monotonic()
        self.connected = False
        super().__init__(('127.0.0.1', 0), Handler)
        self.host = f'127.0.0.1:{self.server_port}'
        self.origin = 'http://' + self.host

    @property
    def url(self):
        return self.origin + '/?key=' + self.key

    def expired(self, now=None):
        return not self.controller.busy and (time.monotonic() if now is None else now) - self.last_heartbeat > (12 if self.connected else 45)


class Handler(BaseHTTPRequestHandler):
    # Never log the request URL: it contains the per-launch secret.
    def log_message(self, *args):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def _reply(self, status, body=b'', mime='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', f"default-src 'none'; script-src 'nonce-{self.server.nonce}'; style-src 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self, post=False):
        query = parse_qs(urlsplit(self.path).query)
        keys = query.get('key', [])
        hosts = self.headers.get_all('Host', [])
        origins = self.headers.get_all('Origin', [])
        valid = hosts == [self.server.host] and len(keys) == 1 and keys[0].isascii() and secrets.compare_digest(keys[0], self.server.key)
        valid = valid and (not origins or origins == [self.server.origin])
        if post:
            valid = valid and self.headers.get_all('X-App-Key', []) == [self.server.key]
        if not valid:
            self._reply(403, {'error': '許可されていない要求です'})
        return valid

    def do_GET(self):
        if not self._authorized():
            return
        path = unquote(urlsplit(self.path).path)
        if path == '/':
            page = render_page(self.server.boot, auth='?key=' + self.server.key, nonce=self.server.nonce)
            self._reply(200, page.encode('utf-8'), 'text/html; charset=utf-8')
        elif path == '/api/state':
            self._reply(200, self.server.controller.snapshot())
        elif path.startswith('/assets/'):
            relative = Path(path[len('/assets/'):])
            target = (ROOT / 'assets' / relative).resolve()
            # Compare to lexical allowlisted directories, rejecting symlink escapes.
            allowed = any(target.is_relative_to(ROOT / 'assets' / k) for k in ('fonts', 'cat_sprites', 'cat_play'))
            if not allowed or not target.is_relative_to((ROOT / 'assets').resolve()) or target.suffix.lower() not in ('.ttf', '.png') or not target.is_file():
                self._reply(404)
            else:
                self._reply(200, target.read_bytes(), mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        else:
            self._reply(404)

    def do_POST(self):
        if not self._authorized(post=True):
            return
        try:
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or not lengths[0].isdigit() or not 0 < int(lengths[0]) <= 65536 or self.headers.get('Transfer-Encoding'):
                self._reply(413)
                return
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                self._reply(415)
                return
            data = json.loads(self.rfile.read(int(lengths[0])).decode('utf-8'))
            path = urlsplit(self.path).path
            if path == '/api/heartbeat':
                self.server.connected = True
                self.server.last_heartbeat = time.monotonic()
                self._reply(200, {})
            elif path == '/api/action':
                self._reply(200, self.server.controller.operate(data))
            elif path == '/api/translate':
                self._reply(200, self.server.controller.translate(data))
            else:
                self._reply(404)
        except json.JSONDecodeError:
            self._reply(400, {'error': '入力または処理状態を確認してください'})
        except (ValueError, StageFailure) as error:
            # Controller messages are authored Japanese text without secrets.
            self._reply(400, {'error': FAILURE_LABELS.get(str(error), str(error))[:300]})
        except subprocess.TimeoutExpired:
            self._reply(504, {'error': '時間内に返事が来ませんでした（UNKNOWN）'})
        except UnicodeError:
            self._reply(400, {'error': '入力または処理状態を確認してください'})
        except Exception:
            self._reply(500, {'error': 'UNKNOWN：操作を停止しました。状態を確認してください'})

    def do_OPTIONS(self):
        if self._authorized():
            self._reply(405)


def window_size(metrics=None):
    """About 65% x 72% of the main screen (owner's preferred size), in the units Chrome's --window-size uses."""
    try:
        if metrics is None:
            import ctypes
            metrics = ctypes.windll.user32.GetSystemMetrics  # this process is not DPI-aware: scaled (logical) pixels
        cx, cy = int(metrics(0)), int(metrics(1))
    except Exception:
        return 1280, 840
    if cx < 800 or cy < 600:
        return 1280, 840
    return max(900, round(cx * .65)), max(620, round(cy * .72))


def launch_browser(url, *, popen=subprocess.Popen, fallback=None, environ=None, size=(1280, 840)):
    env = os.environ if environ is None else environ
    # Chrome first (owner's default); links opened from the app window go to the same browser.
    candidates = [Path(env[k]) / suffix
                  for suffix in ('Google/Chrome/Application/chrome.exe', 'Microsoft/Edge/Application/msedge.exe')
                  for k in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA') if env.get(k)]
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    for exe in candidates:
        if exe.is_file():
            popen([str(exe), '--app=' + url, f'--window-size={size[0]},{size[1]}', '--no-first-run'],
                  creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    if fallback:
        fallback(url)
    elif os.name == 'nt':
        # Shell association opens a GUI browser, never cmd.exe or a console child.
        os.startfile(url)
    else:
        webbrowser.open_new(url)


def run(config_path):
    config = json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    state_dir = Path(config['vault']) / 'subtitle-switch-state'
    state_dir.mkdir(parents=True, exist_ok=True)
    with InstanceLock(state_dir / 'instance.lock'):
        controller = Controller(config, Inventory(state_dir / 'inventory.json'), state_dir)
        with LocalServer(controller) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                controller.operate({'action': 'refresh'})
                launch_browser(server.url, size=window_size() if os.name == 'nt' else (1280, 840))
                while not server.expired():
                    time.sleep(.5)
            finally:
                if controller.worker:
                    controller.worker.join()
                server.shutdown()
                thread.join()
