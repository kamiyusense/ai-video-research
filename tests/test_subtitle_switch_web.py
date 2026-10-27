from types import SimpleNamespace
"""Loopback HTTP, target separation and browser lifecycle with fake adapters."""
import base64
import contextlib
import http.client
import io
import json
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

APP = Path(__file__).resolve().parents[1] / 'automation/subtitle-switch'
sys.path.insert(0, str(APP))
import web_server as web
import switch_app
from switch_state import Inventory, FIELDS


def candidate(vid, **values):
    return {'video_id': vid, 'url': 'https://www.youtube.com/watch?v=' + vid,
            **{key: values.get(key, '') for key in FIELDS}}


@pytest.fixture
def controller(tmp_path):
    config = {k: str(tmp_path / k) for k in ('repository', 'vault', 'inbox', 'preferences', 'channels')}
    inventory = Inventory(tmp_path / 'inventory.json')
    inventory.refresh([candidate('aaaaaaaaaaa', title='最初の動画'), candidate('bbbbbbbbbbb', title='次の動画')])
    calls = []
    def session(inv, service, folder, notify, correction, targets):
        calls.append((targets, correction))
        for vid in targets:
            inv.data['videos'][vid]['status'] = 'complete'
        notify()
    control = web.Controller(config, inventory, tmp_path, service_factory=lambda _: object(),
                             session=session, question=lambda *a: '偽の回答', metadata=lambda *a, **kw: None)
    control.calls = calls
    yield control
    if control.worker:
        control.worker.join(timeout=5)
        assert not control.worker.is_alive()


def make_server(controller):
    # The sandbox denies socket creation. Exercise real HTTP parsing via BytesIO,
    # while verifying the exact address handed to the stdlib server constructor.
    def fake_init(server, address, handler):
        assert address == ('127.0.0.1', 0)
        assert handler is web.Handler
        server.server_address = ('127.0.0.1', 8765)
        server.server_port = 8765
    with patch.object(web.ThreadingHTTPServer, '__init__', fake_init):
        return web.LocalServer(controller)


@pytest.fixture
def server(controller):
    return make_server(controller)


class MemoryConnection:
    def __init__(self, raw):
        self.input = io.BytesIO(raw)
        self.output = io.BytesIO()
    def makefile(self, *args):
        return self.input
    def sendall(self, data):
        self.output.write(data)
    def settimeout(self, seconds):
        pass


def exchange(server, raw):
    wire = MemoryConnection(raw)
    web.Handler(wire, ('127.0.0.1', 12345), server)
    response = http.client.HTTPResponse(MemoryConnection(wire.output.getvalue()))
    response.begin()
    return response.status, dict(response.getheaders()), response.read()


def request(server, path='/api/state', method='GET', *, key=True, host=None, headers=None, body=None):
    path += ('?key=' + server.key) if key else ''
    combined = {'Host': host or server.host, **(headers or {})}
    if method == 'POST':
        combined.setdefault('X-App-Key', server.key)
        combined.setdefault('Content-Type', 'application/json')
        body = json.dumps(body if body is not None else {'action': 'check_all'})
    payload = (body or '').encode('utf-8')
    if method == 'POST':
        combined['Content-Length'] = str(len(payload))
    raw = f'{method} {path} HTTP/1.1\r\n' + ''.join(f'{k}: {v}\r\n' for k, v in combined.items()) + '\r\n'
    return exchange(server, raw.encode('ascii') + payload)


def test_loopback_secret_host_and_origin(server):
    assert server.server_address[0] == '127.0.0.1'
    assert len(server.key) >= 40
    assert request(server)[0] == 200
    assert request(server, key=False)[0] == 403
    assert request(server, path='/api/state?key=bad', key=False)[0] == 403
    assert request(server, host='localhost:' + str(server.server_port))[0] == 403
    assert request(server, host='evil.invalid')[0] == 403
    assert request(server, host='127.0.0.1:1')[0] == 403
    assert request(server, headers={'Origin': 'https://evil.invalid'})[0] == 403
    assert request(server, headers={'Origin': server.origin})[0] == 200
    assert request(server, path='/api/state?key=%E7%8C%AB', key=False)[0] == 403
    assert request(server, path='/api/state?key=' + server.key, key=True)[0] == 403


def test_post_only_and_no_cors(server):
    before = server.controller.snapshot()['checked']
    assert request(server, '/api/action')[0] == 404
    assert server.controller.snapshot()['checked'] == before
    assert request(server, '/api/action', 'POST', headers={'X-App-Key': 'bad'})[0] == 403
    assert request(server, '/api/action', 'POST', headers={'Origin': 'null'})[0] == 403
    assert request(server, '/api/action', 'POST', headers={'Content-Type': 'text/plain'})[0] == 415
    code, headers, _ = request(server, '/api/action', 'POST')
    assert code == 200 and 'Access-Control-Allow-Origin' not in headers
    assert set(server.controller.snapshot()['checked']) == {'aaaaaaaaaaa', 'bbbbbbbbbbb'}
    assert request(server, '/api/action', 'OPTIONS')[0] == 405
    assert request(server, '/api/action', 'POST', body={'action': 'unknown'})[0] == 400
    assert request(server, '/api/action', 'POST', body={'action': 'manual', 'urls': 'x' * 70000})[0] == 413


def test_duplicate_host_rejected(server):
    raw = f'GET /api/state?key={server.key} HTTP/1.1\r\nHost: {server.host}\r\nHost: evil.invalid\r\n\r\n'
    assert exchange(server, raw.encode('ascii'))[0] == 403


def test_serves_only_allowlisted_assets_and_never_logs_secret(server):
    output = io.StringIO()
    with contextlib.redirect_stderr(output), contextlib.redirect_stdout(output):
        status, headers, content = request(server, '/')
        assert status == 200 and switch_app.APP_NAME.encode('utf-8') in content
        assert 'frame-ancestors' in headers['Content-Security-Policy']
        assert headers['Referrer-Policy'] == 'no-referrer'
        assert request(server, '/assets/fonts/ZenMaruGothic-Black-title.ttf')[0] == 200
        assert request(server, '/assets/../web_server.py')[0] == 404
        assert request(server, '/assets/fonts/%2e%2e/%2e%2e/web_server.py')[0] == 404
        assert request(server, '/assets/fonts/README.md')[0] == 404
        assert request(server, '/assets/cat_sprites/idle/idle_00.png', key=False)[0] == 403
    assert server.key not in output.getvalue()


def test_secrets_change_each_launch(controller):
    first, second = make_server(controller), make_server(controller)
    assert first.key != second.key


def test_checked_targets_all_toggle_and_restore(controller):
    c = controller
    c.operate({'action': 'check_all'})
    assert set(c.snapshot()['checked']) == {'aaaaaaaaaaa', 'bbbbbbbbbbb'}
    c.operate({'action': 'check_all'})
    assert c.snapshot()['checked'] == []
    c.operate({'action': 'check', 'id': 'aaaaaaaaaaa'})
    c.operate({'action': 'selected'})
    c.worker.join(5)
    assert c.calls == [({'aaaaaaaaaaa'}, '')]
    assert c.inventory.data['videos']['bbbbbbbbbbb']['status'] == 'pending'
    c.operate({'action': 'check', 'id': 'bbbbbbbbbbb'})
    c.operate({'action': 'reject', 'reason': 'もう知ってる'})
    assert c.inventory.data['videos']['bbbbbbbbbbb']['rejection_reason'] == 'もう知ってる'
    assert not c.snapshot()['rows']
    c.operate({'action': 'filters', 'rejected': True, 'processed': False})
    c.operate({'action': 'check', 'id': 'bbbbbbbbbbb'})
    c.operate({'action': 'selected'})
    assert len(c.calls) == 1  # rejected rows can be selected for restore, never saved
    c.operate({'action': 'restore'})
    assert not c.inventory.data['videos']['bbbbbbbbbbb']['rejected']
    assert c.inventory.data['videos']['bbbbbbbbbbb']['rejection_reason'] == ''


def test_hidden_checked_rows_are_not_selected_save_targets(controller):
    c = controller
    c.operate({'action': 'check', 'id': 'aaaaaaaaaaa'})
    c.inventory.data['videos']['aaaaaaaaaaa']['status'] = 'complete'
    c.publish()
    c.operate({'action': 'selected'})
    assert not c.calls


def test_manual_save_does_not_include_checked_row(controller):
    c = controller
    c.operate({'action': 'check_all'})
    c.operate({'action': 'manual', 'urls': 'https://youtu.be/ccccccccccc?t=60'})
    c.worker.join(5)
    assert c.calls == [({'ccccccccccc'}, '')]
    assert c.inventory.data['videos']['aaaaaaaaaaa']['status'] == 'pending'
    before = set(c.inventory.data['videos'])
    with pytest.raises(ValueError):
        c.operate({'action': 'manual', 'urls': 'https://youtu.be/ddddddddddd\nnot a url'})
    assert set(c.inventory.data['videos']) == before


def test_empty_save_and_duplicate_operation_never_start_services(controller):
    c = controller
    c.service_factory = Mock(side_effect=AssertionError('unexpected service'))
    c.operate({'action': 'selected'})
    c.operate({'action': 'manual', 'urls': ''})
    assert not c.service_factory.called
    entered, release = threading.Event(), threading.Event()
    def fake(*args, **kwargs):
        entered.set()
        assert release.wait(3)
        return '回答'
    c.question = fake
    c.operate({'action': 'ask', 'question': '質問'})
    try:
        assert entered.wait(2)
        assert c.snapshot()['cat'] == 'walk'
        with pytest.raises(ValueError):
            c.operate({'action': 'ask', 'question': '二重起動'})
    finally:
        release.set()
        c.worker.join(5)
    assert c.snapshot()['cat'] == 'done'


def test_question_limits_grok_and_failure_state(controller):
    c = controller
    c.question = Mock(return_value='回答')
    for text in ('', ' ', '猫' * 2001):
        with pytest.raises(ValueError):
            c.operate({'action': 'ask', 'question': text})
    with pytest.raises(ValueError, match='UNKNOWN'):
        c.operate({'action': 'ask', 'question': '質問', 'provider': 'grok'})
    assert not c.question.called
    c.operate({'action': 'ask', 'question': '猫' * 2000})
    c.worker.join(5)
    assert c.snapshot()['answer'] == '回答'
    assert c.question.call_args.args[2] == c.state_dir / 'question_logs'
    c.question = Mock(side_effect=RuntimeError('secret should not appear'))
    c.operate({'action': 'ask', 'question': '質問'})
    c.worker.join(5)
    assert c.snapshot()['cat'] == 'error'
    assert 'secret' not in c.snapshot()['notice']


def test_refresh_metadata_and_persistent_inventory(controller):
    c = controller
    inbox = c.locations['inbox']
    inbox.mkdir()
    (inbox / 'fixture.json').write_text(json.dumps({'videos': [{'url': 'https://youtu.be/ccccccccccc', 'title': '受け箱の動画'}]}), encoding='utf-8')
    def fake(rows, cache, runner, **kw):
        kw['notify']('ccccccccccc', {'channel': '偽チャンネル'})
    c.metadata = fake
    c.operate({'action': 'refresh'})
    c.worker.join(5)
    assert any(row['cells'][1]['full'] == '偽チャンネル' for row in c.snapshot()['rows'])
    assert 'ccccccccccc' in Inventory(c.inventory.path).data['videos']


def test_missing_inbox_is_an_error_and_preserves_existing_rows(controller):
    controller.operate({'action': 'refresh'})
    controller.worker.join(5)
    assert controller.snapshot()['cat'] == 'error'
    assert len(controller.snapshot()['rows']) == 2
    assert 'UNKNOWN' in controller.snapshot()['notice']


def test_short_status_retains_full_reason_and_notebook(controller):
    row = controller.inventory.data['videos']['aaaaaaaaaaa']
    row.update(status='waiting', status_reason='NOTEBOOK_LOGIN_EXPIRED', reason='長い説明' * 20)
    result = web.table_row(row)
    assert result['cells'][7]['text'] == '待ち'
    assert '手動で復旧' in result['cells'][7]['full']
    assert len(result['cells'][5]['text']) <= 9
    assert result['cells'][5]['full'] == row['reason']
    assert result['cells'][8]['text'] == '未接続'


def test_heartbeat_and_close_grace(server):
    assert not server.expired(server.last_heartbeat + 44)
    assert server.expired(server.last_heartbeat + 46)
    assert request(server, '/api/heartbeat', 'POST', body={})[0] == 200
    assert server.connected
    assert not server.expired(server.last_heartbeat + 11)
    assert server.expired(server.last_heartbeat + 13)
    server.controller.busy = True
    assert not server.expired(server.last_heartbeat + 10000)
    server.controller.busy = False


@pytest.mark.parametrize('exe', ['Microsoft/Edge/Application/msedge.exe', 'Google/Chrome/Application/chrome.exe'])
def test_browser_launch_is_app_sized_and_has_no_console(tmp_path, exe):
    edge = tmp_path / exe
    edge.parent.mkdir(parents=True)
    edge.write_bytes(b'fixture')
    popen, fallback = Mock(), Mock()
    with patch.object(subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True):
        web.launch_browser('http://127.0.0.1:1/?key=fixture', popen=popen, fallback=fallback, environ={'PROGRAMFILES': str(tmp_path)})
    args, kwargs = popen.call_args
    assert '--app=http://127.0.0.1:1/?key=fixture' in args[0]
    assert '--window-size=1280,840' in args[0]
    assert kwargs['creationflags'] == 0x08000000
    assert kwargs['stdout'] == kwargs['stderr'] == subprocess.DEVNULL
    fallback.assert_not_called()
    web.launch_browser('fixture-url', popen=popen, fallback=fallback, environ={})
    fallback.assert_called_once_with('fixture-url')


def test_title_fonts_are_six_local_licensed_files():
    with patch.object(web.secrets, 'randbelow', side_effect=range(6)) as choose:
        assert [web.boot_data()['font'] for _ in range(6)] == list(range(6))
    assert all(call.args == (6,) for call in choose.call_args_list)
    assert len(web.FONTS) == 6
    for name in web.FONTS:
        assert (web.ROOT / f'assets/fonts/{name}-title.ttf').is_file()
    assert len(list((web.ROOT / 'assets/fonts').glob('OFL-*.txt'))) == 6


def test_cat_manifest_present_missing_and_fixture(tmp_path):
    assert web.load_manifest(tmp_path) is None
    assert web.load_manifest(tmp_path, True) is None
    actual = web.load_manifest(web.ROOT / 'assets/cat_sprites')
    assert actual['states']['walk']['frames'] == 8
    assert actual['states']['done']['hold_last'] is True
    assert web.load_manifest(web.ROOT / 'assets/cat_play', True)['frame_width'] == 256
    manifest = {'frame_width': 1, 'frame_height': 1, 'look': {'directions': 8},
                'punch_left': {'frames': 2, 'fps': 10}, 'punch_right': {'frames': 2, 'fps': 10},
                'cursor': {'hotspot': [0, 0]}, 'punch_radius_px': 40, 'punch_cooldown_sec': .6}
    pixel = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
    for group, count in [('look', 8), ('punch_left', 2), ('punch_right', 2)]:
        (tmp_path / group).mkdir()
        for i in range(count):
            (tmp_path / group / f'{group}_{i:02}.png').write_bytes(pixel)
    (tmp_path / 'cursor').mkdir()
    (tmp_path / 'cursor/teaser_32.png').write_bytes(pixel)
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    assert web.load_manifest(tmp_path, True) == manifest
    (tmp_path / 'look/look_07.png').unlink()
    assert web.load_manifest(tmp_path, True) is None


def test_cat_node_rules():
    result = subprocess.run(['node', str(Path(__file__).parent / 'subtitle_switch_cat_test.cjs')],
                            capture_output=True, text=True, encoding='utf-8', timeout=10)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('launch_fails', [False, True])
def test_lifecycle_holds_lock_refreshes_and_closes_after_worker(tmp_path, launch_fails):
    config = {'vault': str(tmp_path / 'vault')}
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(config), encoding='utf-8')
    calls = Mock()
    control = calls.controller
    context = MagicMock()
    context.__enter__.return_value = calls.server
    context.__exit__.return_value = False
    calls.server.expired.side_effect = [False, True]
    lock = MagicMock()
    def unlock(*args):
        calls.unlock()
        return False
    lock.__exit__.side_effect = unlock
    if launch_fails:
        calls.launch.side_effect = RuntimeError('fake browser failure')
    with patch.object(web, 'InstanceLock', return_value=lock) as lock_type, \
         patch.object(web, 'Controller', return_value=control), \
         patch.object(web, 'LocalServer', return_value=context), \
         patch.object(web, 'launch_browser', calls.launch), \
         patch.object(web.threading, 'Thread', return_value=calls.thread), \
         patch.object(web.time, 'sleep', calls.sleep):
        if launch_fails:
            with pytest.raises(RuntimeError, match='fake browser'):
                web.run(path)
        else:
            web.run(path)
    lock_type.assert_called_once_with(Path(config['vault']) / 'subtitle-switch-state/instance.lock')
    lock.__enter__.assert_called_once()
    control.operate.assert_called_once_with({'action': 'refresh'})
    control.worker.join.assert_called_once()
    calls.server.shutdown.assert_called_once()
    events = [c[0] for c in calls.mock_calls]
    assert events.index('controller.worker.join') < events.index('server.shutdown') < events.index('thread.join') < events.index('unlock')


def test_question_uses_checked_rows_and_shows_own_errors(controller):
    c = controller
    c.inventory.refresh([{'video_id': 'eeeeeeeeeee', 'url': 'https://www.youtube.com/watch?v=eeeeeeeeeee', 'title': 'T',
                          'channel': '', 'published_at': '', 'lang': 'en', 'theme': '', 'kind': '', 'reason': ''}])
    c.publish()
    c.operate({'action': 'check', 'id': 'eeeeeeeeeee'})
    c.question = Mock(side_effect=ValueError('選んだ動画はまだ保存されていない'))
    c.operate({'action': 'ask', 'question': '要約して'})
    c.worker.join(5)
    assert c.question.call_args.kwargs['video_ids'] == ['eeeeeeeeeee']
    snap = c.snapshot()
    assert snap['cat'] == 'error' and '保存されていない' in snap['answer'] and '保存されていない' in snap['notice']
    row = next(r for r in snap['rows'] if r['id'] == 'eeeeeeeeeee')
    assert row['url'] == 'https://www.youtube.com/watch?v=eeeeeeeeeee' and row['translate'] is True


def test_question_success_is_not_marked_failed_by_old_waiting_rows(controller):
    c = controller
    c.inventory.refresh([{'video_id': 'fffffffffff', 'url': 'https://www.youtube.com/watch?v=fffffffffff', 'title': 'T',
                          'channel': '', 'published_at': '', 'lang': 'ja', 'theme': '', 'kind': '', 'reason': ''}])
    c.inventory.data['videos']['fffffffffff']['status'] = 'waiting'
    c.question = Mock(return_value='回答')
    c.operate({'action': 'ask', 'question': '質問'})
    c.worker.join(5)
    assert c.snapshot()['cat'] == 'done'
    assert c.question.call_args.kwargs['video_ids'] is None


def test_title_translation_is_cached_and_uses_inbox_value(tmp_path):
    from translate_title import TitleTranslator, needs_translation
    assert needs_translation('en-US') and needs_translation('en')
    assert not needs_translation('ja') and not needs_translation('') and not needs_translation('未設定')
    calls = []
    def runner(args, stdin=None, timeout=None):
        calls.append((args, stdin))
        return SimpleNamespace(returncode=0, stdout='最高のエージェントIDE\n', stderr='')
    t = TitleTranslator(tmp_path / 'cache.json', runner=runner)
    assert t.translate('a', 'The Best Agent IDE') == '最高のエージェントIDE'
    assert t.translate('a', 'The Best Agent IDE') == '最高のエージェントIDE'
    assert len(calls) == 1 and '--tools' in calls[0][0] and 'claude-haiku-5-5' in calls[0][0]
    assert '<title>The Best Agent IDE</title>' in calls[0][1]
    assert TitleTranslator(tmp_path / 'cache.json', runner=runner).translate('a', 'x') == '最高のエージェントIDE'
    assert t.translate('b', 'x', title_ja='受け箱の訳') == '受け箱の訳' and len(calls) == 1


def test_question_cli_uses_owner_model_effort_and_logs_failures(tmp_path):
    import subprocess
    from unittest.mock import patch
    import ask_research
    repo = tmp_path / 'repo'; (repo / 'research').mkdir(parents=True)
    (repo / 'research' / 'n.md').write_text('# note\n', encoding='utf-8')
    records = [{'record_path': 'research/n.md', 'video_id': 'ggggggggggg'}]
    seen = []
    def runner(args, cwd=None, stdin=None, timeout=None):
        seen.append((args, timeout))
        raise subprocess.TimeoutExpired(args, timeout)
    with patch.object(ask_research.knowledge, 'build_video_knowledge_catalog', return_value=({}, records)):
        with pytest.raises(subprocess.TimeoutExpired):
            ask_research.ask('質問', repo, tmp_path / 'log', runner=runner, video_ids=['ggggggggggg'])
        with pytest.raises(ValueError, match='保存されていない'):
            ask_research.build_prompt('質問', repo, ['hhhhhhhhhhh'])
    args, timeout = seen[0]
    assert args[args.index('--model') + 1] == 'claude-opus-5-5' and args[args.index('--effort') + 1] == 'medium'
    assert timeout == 300
    log = (tmp_path / 'log' / 'questions.jsonl').read_text(encoding='utf-8')
    assert 'TimeoutExpired' in log and '質問' not in log


def test_window_size_follows_screen_and_chrome_is_preferred(tmp_path):
    assert web.window_size(lambda i: (1920, 1080)[i]) == (1248, 778)
    assert web.window_size(lambda i: (1280, 720)[i]) == (900, 620)
    assert web.window_size(lambda i: 0) == (1280, 840)
    for exe in ('Microsoft/Edge/Application/msedge.exe', 'Google/Chrome/Application/chrome.exe'):
        (tmp_path / exe).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / exe).write_bytes(b'fixture')
    popen = Mock()
    web.launch_browser('u', popen=popen, fallback=Mock(), environ={'PROGRAMFILES': str(tmp_path)}, size=(1248, 778))
    args = popen.call_args.args[0]
    assert args[0].endswith('chrome.exe') and '--window-size=1248,778' in args


def test_old_attention_row_does_not_make_refresh_an_error(controller):
    c = controller
    c.inventory.refresh([{'video_id': 'fffffffffff', 'url': 'https://www.youtube.com/watch?v=fffffffffff', 'title': 'T',
                          'channel': '', 'published_at': '', 'lang': 'ja', 'theme': '', 'kind': '', 'reason': ''}])
    c.inventory.data['videos']['fffffffffff']['status'] = 'attention'
    c.locations['inbox'].mkdir()
    c.metadata = Mock()
    c.operate({'action': 'refresh'})
    c.worker.join(5)
    assert c.snapshot()['cat'] == 'done'
    assert c.inventory.data['videos']['fffffffffff']['status'] == 'attention'
