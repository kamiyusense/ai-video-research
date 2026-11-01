"""No sockets, Windows desktop, browser, service or external model is used."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'automation/subtitle-switch'))
import app_activation as ipc
from app_window import AppWindow
import switch_app
import web_server as web


class Desktop:
    def __init__(self):
        self.handles = {9}  # An earlier, unrelated window with the same caption.
        self.show = Mock()
        self.set_icons = Mock()

    def windows(self, *, title=True):
        return self.handles.copy()

    def matches(self, hwnd, *, title=True):
        return hwnd in self.handles


def test_starting_repeated_launch_restores_one_window_and_closed_window_reopens():
    desktop = Desktop()
    launch = Mock()
    def finish_starting(_):
        desktop.handles.add(12)
    window = AppWindow('same-private-url', launch, switch_app.APP_NAME, 'decided.ico',
                       (1000, 800), desktop=desktop, sleep=finish_starting)
    window.start()
    assert window.activate() is False  # Request arrives before its title is available.
    assert window.activate() is False  # Existing/minimized window is reused.
    launch.assert_called_once_with('same-private-url', size=(1000, 800))
    assert desktop.show.call_args_list == [((12,),), ((12,),)]
    desktop.set_icons.assert_called_once_with(12)
    desktop.handles.remove(12)
    assert window.activate() is True
    assert launch.call_count == 2
    assert all(call.args == ('same-private-url',) for call in launch.call_args_list)
    desktop.show.assert_called_with(12)


def test_slow_window_is_not_duplicated_when_native_discovery_times_out():
    desktop, launch = Desktop(), Mock()
    window = AppWindow('private-url', launch, 'Title', 'decided.ico', (1, 1),
                       desktop=desktop, clock=Mock(side_effect=[0, 21]), sleep=Mock())
    window.start()
    with pytest.raises(RuntimeError, match='APP_WINDOW_NOT_FOUND'):
        window.activate()
    assert launch.call_count == 1
    desktop.show.assert_not_called()


def test_close_before_first_discovery_reopens_the_same_url():
    desktop, launch = Desktop(), Mock()
    def finish_starting(_):
        desktop.handles.add(12)
    window = AppWindow('same-private-url', launch, 'Title', 'decided.ico', (1, 1),
                       desktop=desktop, sleep=finish_starting)
    window.start()
    # The page sent /api/bye and its HWND disappeared before the first poll.
    assert window.activate(page_closed=True) is True
    assert launch.call_count == 2
    assert all(call.args == ('same-private-url',) for call in launch.call_args_list)
    desktop.show.assert_called_once_with(12)


def test_reload_before_first_discovery_keeps_the_loading_window():
    desktop, launch, loading = Desktop(), Mock(), {12}
    def windows(*, title=True):
        return desktop.handles.copy() if title else desktop.handles | loading
    desktop.windows = windows
    def finish_loading(_):
        desktop.handles.add(12)
    # Loading begins after the initial baseline snapshot.
    window = AppWindow('same-private-url', launch, 'Title', 'decided.ico', (1, 1),
                       desktop=desktop, sleep=finish_loading)
    loading.clear()
    window.start()
    loading.add(12)
    assert window.activate(page_closed=True) is False
    launch.assert_called_once()
    desktop.show.assert_called_once_with(12)


def connection():
    result = MagicMock()
    result.__enter__.return_value = result
    result.poll.return_value = True
    return result


def test_secondary_waits_for_endpoint_grants_foreground_and_never_receives_url(tmp_path):
    conn = connection()
    conn.recv_bytes.side_effect = [b'123', b'OK']
    with patch.object(ipc, 'Client', side_effect=[FileNotFoundError(), conn]) as client, \
         patch.object(ipc, 'allow_foreground') as allow, patch.object(ipc.time, 'sleep'):
        ipc.request_activation(tmp_path)
    assert client.call_count == 2
    allow.assert_called_once_with(123)
    conn.send_bytes.assert_called_once_with(b'ACTIVATE')
    assert conn.recv.call_count == 0  # Never deserialize untrusted pickle input.


def test_unknown_activation_is_not_resent(tmp_path):
    conn = connection()
    conn.recv_bytes.return_value = b'123'
    conn.poll.side_effect = [True, False]
    with patch.object(ipc, 'Client', return_value=conn) as client, patch.object(ipc, 'allow_foreground'):
        with pytest.raises(RuntimeError, match='APP_ACTIVATION_UNKNOWN'):
            ipc.request_activation(tmp_path)
    assert client.call_count == 1
    conn.send_bytes.assert_called_once_with(b'ACTIVATE')


@pytest.mark.parametrize('callback_result, expected', [(True, b'OK'), (False, b'CLOSING'),
                                                    (RuntimeError('secret-url'), b'FAILED')])
def test_owner_acknowledges_actual_activation_without_leaking_errors(callback_result, expected):
    service = object.__new__(ipc.ActivationService)
    service.activate = Mock()
    if isinstance(callback_result, Exception):
        service.activate.side_effect = callback_result
    else:
        service.activate.return_value = callback_result
    conn = connection()
    conn.recv_bytes.return_value = b'ACTIVATE'
    service.handle(conn)
    service.activate.assert_called_once()
    assert conn.send_bytes.call_args_list[-1].args == (expected,)
    assert conn.recv.call_count == 0


def test_owner_ignores_other_commands():
    service = object.__new__(ipc.ActivationService)
    service.activate = Mock()
    conn = connection()
    conn.recv_bytes.return_value = b'RUN SOMETHING'
    service.handle(conn)
    service.activate.assert_not_called()


def test_second_launcher_exits_quietly_without_initializing_services(tmp_path):
    path = tmp_path / 'config.json'
    path.write_text(json.dumps({'vault': str(tmp_path)}), encoding='utf-8')
    lock = MagicMock()
    lock.__enter__.side_effect = RuntimeError('ALREADY_RUNNING')
    alert = Mock()
    with patch.object(web, 'InstanceLock', return_value=lock), \
         patch.object(web, 'request_activation') as activate, patch.object(web, 'Controller') as controller:
        switch_app.main(path, run=web.run, alert=alert)
    activate.assert_called_once_with(tmp_path / 'subtitle-switch-state')
    controller.assert_not_called()
    alert.assert_not_called()
    assert not (tmp_path / 'app_error.log').exists()


def test_real_lock_failure_still_alerts_and_does_not_activate(tmp_path):
    path = tmp_path / 'config.json'
    path.write_text(json.dumps({'vault': str(tmp_path)}), encoding='utf-8')
    lock = MagicMock()
    lock.__enter__.side_effect = RuntimeError('real startup failure')
    alert = Mock()
    with patch.object(web, 'InstanceLock', return_value=lock), patch.object(web, 'request_activation') as activate:
        with pytest.raises(RuntimeError, match='real startup failure'):
            switch_app.main(path, run=web.run, alert=alert)
    activate.assert_not_called()
    alert.assert_called_once()
    assert 'real startup failure' in (tmp_path / 'app_error.log').read_text(encoding='utf-8')


def test_unknown_request_never_restarts_owner(tmp_path):
    path = tmp_path / 'config.json'
    path.write_text(json.dumps({'vault': str(tmp_path)}), encoding='utf-8')
    lock = MagicMock()
    lock.__enter__.side_effect = RuntimeError('ALREADY_RUNNING')
    with patch.object(web, 'InstanceLock', return_value=lock) as acquire, \
         patch.object(web, 'request_activation', side_effect=RuntimeError('APP_ACTIVATION_UNKNOWN')):
        with pytest.raises(RuntimeError, match='APP_ACTIVATION_UNKNOWN'):
            web.run(path)
    assert acquire.call_count == 1


def test_port_in_use_still_alerts_and_closes_activation_endpoint(tmp_path):
    path = tmp_path / 'config.json'
    path.write_text(json.dumps({'vault': str(tmp_path)}), encoding='utf-8')
    service = MagicMock()
    alert = Mock()
    with patch.object(web, 'InstanceLock', return_value=MagicMock()), \
         patch.object(web, 'ActivationService', return_value=service) as activation, \
         patch.object(web, 'Controller'), patch.object(web, 'LocalServer', side_effect=OSError('port in use')):
        with pytest.raises(OSError, match='port in use'):
            switch_app.main(path, run=web.run, alert=alert)
    service.__exit__.assert_called_once()
    assert activation.call_args.args[1]() is False
    alert.assert_called_once()


@pytest.mark.parametrize('minimized, show_command', [(True, 9), (False, 5)])
def test_windows_icons_and_restore_use_pointer_sized_native_calls(minimized, show_command):
    import ctypes
    from app_window import WindowsDesktop
    user = Mock()
    user.LoadImageW.side_effect = [0x123456789, 0x234567890]
    user.IsWindow.return_value = True
    user.IsIconic.return_value = minimized
    def title(hwnd, buffer, size):
        buffer.value = switch_app.APP_NAME if hwnd == 42 else 'Other page'
    def kind(hwnd, buffer, size):
        buffer.value = 'Chrome_WidgetWin_1'
    user.GetWindowTextW.side_effect = title
    user.GetClassNameW.side_effect = kind
    def enum(callback, _):
        callback(41, 0)
        callback(42, 0)
        return True
    user.EnumWindows.side_effect = enum
    with patch.object(ctypes, 'WinDLL', return_value=user, create=True), \
         patch.object(ctypes, 'WINFUNCTYPE', ctypes.CFUNCTYPE, create=True):
        desktop = WindowsDesktop(switch_app.APP_NAME, Path('app-icon-v3-2.ico'))
        assert desktop.windows() == {42}
        assert desktop.matches(42, title=False)
        desktop.show(42)
    user.ShowWindowAsync.assert_called_once_with(42, show_command)
    user.SetForegroundWindow.assert_called_once_with(42)
    assert [call.args[1:4] for call in user.SendMessageTimeoutW.call_args_list] == [
        (0x80, 0, 0x123456789), (0x80, 1, 0x234567890)]
    assert user.LoadImageW.restype is ctypes.wintypes.HANDLE
    assert user.SendMessageTimeoutW.restype is ctypes.c_ssize_t
    assert all(call.args[1] == 'app-icon-v3-2.ico' for call in user.LoadImageW.call_args_list)


def test_startup_activation_waits_until_first_launch_and_renews_close_grace(tmp_path):
    import threading
    real_thread, real_event = threading.Thread, threading.Event
    path = tmp_path / 'config.json'
    path.write_text(json.dumps({'vault': str(tmp_path)}), encoding='utf-8')
    callbacks, results, threads = [], [], []
    waiting, completed, ready = real_event(), real_event(), real_event()
    tracked_ready = Mock()
    tracked_ready.set.side_effect = ready.set
    def wait(timeout):
        waiting.set()
        return ready.wait(timeout)
    tracked_ready.wait.side_effect = wait
    first_event = [tracked_ready]
    def make_event():
        return first_event.pop() if first_event else real_event()
    window, server, controller = Mock(), Mock(), Mock()
    server.expired.side_effect = [False, True]
    window.activate.return_value = True
    context = MagicMock()
    context.__enter__.return_value = server
    def service_factory(state_dir, callback):
        callbacks.append(callback)
        return MagicMock()
    def start_window():
        def request():
            results.append(callbacks[0]())
            completed.set()
        thread = real_thread(target=request, daemon=True)
        threads.append(thread)
        thread.start()
        assert waiting.wait(2)
        window.activate.assert_not_called()
    window.start.side_effect = start_window
    with patch.object(web, 'InstanceLock', return_value=MagicMock()), \
         patch.object(web, 'ActivationService', side_effect=service_factory), \
         patch.object(web, 'Controller', return_value=controller), \
         patch.object(web, 'LocalServer', return_value=context), \
         patch.object(web, 'AppWindow', return_value=window) as window_type, \
         patch.object(web.threading, 'Event', side_effect=make_event), \
         patch.object(web.threading, 'Thread'), \
         patch.object(web.time, 'sleep', side_effect=lambda _: completed.wait(2)):
        web.run(path)
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()
    assert results == [True]
    window.start.assert_called_once()
    window.activate.assert_called_once()
    assert window_type.call_args.args[3] == web.ROOT / 'assets/app_icon/app-icon-v3-2.ico'
    assert server.connected is False
    assert isinstance(server.last_heartbeat, float)
    assert callbacks[0]() is False  # Already closing: explicitly not applied.


def test_owner_exiting_before_handoff_allows_new_start_after_lock_releases(tmp_path):
    path = tmp_path / 'config.json'
    path.write_text(json.dumps({'vault': str(tmp_path)}), encoding='utf-8')
    busy, owned, server = MagicMock(), MagicMock(), Mock()
    busy.__enter__.side_effect = RuntimeError('ALREADY_RUNNING')
    context = MagicMock()
    context.__enter__.return_value = server
    server.expired.return_value = True
    with patch.object(web, 'InstanceLock', side_effect=[busy, owned]) as acquire, \
         patch.object(web, 'request_activation', side_effect=ipc.ActivationUnavailable('APP_OWNER_CLOSING')) as activate, \
         patch.object(web, 'ActivationService'), patch.object(web, 'Controller'), \
         patch.object(web, 'LocalServer', return_value=context), patch.object(web, 'AppWindow') as window, \
         patch.object(web.threading, 'Thread'), patch.object(web.time, 'sleep'):
        web.run(path)
    assert acquire.call_count == 2
    activate.assert_called_once()
    window.return_value.start.assert_called_once()
    owned.__exit__.assert_called_once()
