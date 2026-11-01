"""Local activation only: never publish the browser URL or unpickle IPC input."""
from __future__ import annotations

import hashlib
import os
import tempfile
import threading
import time
from multiprocessing.connection import Client, Listener
from pathlib import Path


class ActivationUnavailable(RuntimeError):
    """No request was applied; the owner may have exited during launch."""


def endpoint(state_dir):
    identity = hashlib.sha256(os.path.normcase(str(Path(state_dir).resolve())).encode('utf-8')).hexdigest()[:32]
    if os.name == 'nt':
        return '\\\\.\\pipe\\SubtitleSwitch-' + identity, 'AF_PIPE'
    # Keep the Unix socket below its path-length limit, even for a long vault path.
    return str(Path(tempfile.gettempdir()) / ('subtitle-switch-' + str(os.getuid()) + '-' + identity)), 'AF_UNIX'


def allow_foreground(pid):
    if os.name == 'nt':
        import ctypes
        ctypes.windll.user32.AllowSetForegroundWindow(pid)


def request_activation(state_dir, *, timeout=10):
    """Retry connection establishment only. A sent request is never replayed."""
    address, family = endpoint(state_dir)
    deadline = time.monotonic() + timeout
    while True:
        try:
            connection = Client(address, family=family, authkey=None)
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise ActivationUnavailable('APP_ACTIVATION_UNAVAILABLE') from None
            time.sleep(.1)
    with connection:
        if not connection.poll(30):
            raise RuntimeError('APP_ACTIVATION_TIMEOUT')
        pid = int(connection.recv_bytes(32).decode('ascii'))
        # The user launched this process; let the existing process take foreground.
        allow_foreground(pid)
        connection.send_bytes(b'ACTIVATE')
        if not connection.poll(30):
            raise RuntimeError('APP_ACTIVATION_UNKNOWN')
        result = connection.recv_bytes(32)
        if result == b'CLOSING':
            raise ActivationUnavailable('APP_OWNER_CLOSING')
        if result != b'OK':
            raise RuntimeError('APP_ACTIVATION_FAILED')


class ActivationService:
    """Owned under InstanceLock. Windows named pipes use the process default ACL."""
    def __init__(self, state_dir, activate):
        self.address, self.family = endpoint(state_dir)
        if self.family == 'AF_UNIX':
            # Only the lock owner can remove a stale endpoint after a crash.
            Path(self.address).unlink(missing_ok=True)
        self.listener = Listener(self.address, family=self.family, authkey=None)
        if self.family == 'AF_UNIX':
            os.chmod(self.address, 0o600)
        self.activate = activate
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self.serve, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def serve(self):
        while not self.stopping.is_set():
            try:
                with self.listener.accept() as connection:
                    if self.stopping.is_set():
                        break
                    self.handle(connection)
            except (OSError, EOFError):
                if self.stopping.is_set():
                    break

    def handle(self, connection):
        connection.send_bytes(str(os.getpid()).encode('ascii'))
        if not connection.poll(5) or connection.recv_bytes(16) != b'ACTIVATE':
            return
        try:
            result = b'OK' if self.activate() else b'CLOSING'
        except Exception:
            # Do not send exception text, which could contain a browser URL/key.
            result = b'FAILED'
        connection.send_bytes(result)

    def __exit__(self, *exc):
        self.stopping.set()
        try:
            # Wake an idle accept without issuing another activation.
            with Client(self.address, family=self.family, authkey=None):
                pass
        except OSError:
            pass
        self.listener.close()
        self.thread.join(timeout=1)
