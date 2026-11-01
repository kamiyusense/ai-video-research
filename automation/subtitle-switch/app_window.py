"""Windows browser-window restore and icons using only the standard library."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path


class WindowsDesktop:
    def __init__(self, title, icon):
        import ctypes
        from ctypes import wintypes
        self.ctypes, self.title = ctypes, title
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        # HWND/HICON and LRESULT are pointer-sized, including on 64-bit Windows.
        signatures = {
            'EnumWindows': ([self.callback_type, wintypes.LPARAM], wintypes.BOOL),
            'GetWindowTextW': ([wintypes.HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int),
            'GetClassNameW': ([wintypes.HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int),
            'IsWindow': ([wintypes.HWND], wintypes.BOOL),
            'IsIconic': ([wintypes.HWND], wintypes.BOOL),
            'ShowWindowAsync': ([wintypes.HWND, ctypes.c_int], wintypes.BOOL),
            'SetForegroundWindow': ([wintypes.HWND], wintypes.BOOL),
            'LoadImageW': ([wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                            ctypes.c_int, ctypes.c_int, wintypes.UINT], wintypes.HANDLE),
            'SendMessageTimeoutW': ([wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                     wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                                     ctypes.POINTER(ctypes.c_size_t)], ctypes.c_ssize_t),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.user, name)
            function.argtypes, function.restype = args, result
        # Keep icons alive while any browser window can refer to them.
        self.icons = [(kind, self.user.LoadImageW(None, str(Path(icon)), 1, size, size, 0x10))
                      for kind, size in ((0, 16), (1, 32))]
        if not all(handle for _, handle in self.icons):
            raise OSError('APP_ICON_LOAD_FAILED')

    def matches(self, hwnd, *, title=True):
        if not self.user.IsWindow(hwnd):
            return False
        caption, kind = self.ctypes.create_unicode_buffer(512), self.ctypes.create_unicode_buffer(128)
        self.user.GetWindowTextW(hwnd, caption, len(caption))
        self.user.GetClassNameW(hwnd, kind, len(kind))
        return kind.value == 'Chrome_WidgetWin_1' and (not title or caption.value == self.title)

    def windows(self, *, title=True):
        found = set()
        @self.callback_type
        def collect(hwnd, _):
            if self.matches(hwnd, title=title):
                found.add(hwnd)
            return True
        self.user.EnumWindows(collect, 0)
        return found

    def set_icons(self, hwnd):
        result = self.ctypes.c_size_t()
        for kind, handle in self.icons:
            # WM_SETICON; bounded even if the browser is temporarily unresponsive.
            self.user.SendMessageTimeoutW(hwnd, 0x80, kind, handle, 0x2, 250,
                                         self.ctypes.byref(result))

    def show(self, hwnd):
        self.set_icons(hwnd)
        self.user.ShowWindowAsync(hwnd, 9 if self.user.IsIconic(hwnd) else 5)
        self.user.SetForegroundWindow(hwnd)


class AppWindow:
    def __init__(self, url, launch, title, icon, size, *, desktop=None, clock=time.monotonic,
                 sleep=time.sleep):
        self.url, self.launch, self.size = url, launch, size
        self.desktop = desktop if desktop is not None else (WindowsDesktop(title, icon) if os.name == 'nt' else None)
        self.clock, self.sleep = clock, sleep
        self.guard = threading.RLock()
        self.hwnd = None
        self.pending = False
        self.baseline = set()

    def start(self):
        with self.guard:
            # Include loading browser windows so a reload is never mistaken for a close.
            self.baseline = self.desktop.windows(title=False) if self.desktop else set()
            self.hwnd = None
            self.pending = True
            self.launch(self.url, size=self.size)

    def poll(self):
        with self.guard:
            if self.desktop and self.pending:
                candidates = self.desktop.windows() - self.baseline
                if candidates:
                    self.hwnd = min(candidates)
                    self.pending = False
                    self.desktop.set_icons(self.hwnd)

    def activate(self, *, page_closed=False):
        """Return whether a closed window had to be reopened; never double-launch startup."""
        with self.guard:
            if not self.desktop:
                self.launch(self.url, size=self.size)
                return True
            self.poll()
            reopened = False
            closed_before_discovery = (self.pending and page_closed
                                       and not (self.desktop.windows(title=False) - self.baseline))
            if closed_before_discovery or (not self.pending and not self.desktop.matches(self.hwnd, title=False)):
                self.start()
                reopened = True
            deadline = self.clock() + 20
            while self.pending:
                self.poll()
                if not self.pending:
                    break
                if self.clock() >= deadline:
                    raise RuntimeError('APP_WINDOW_NOT_FOUND')
                self.sleep(.1)
            self.desktop.show(self.hwnd)
            return reopened
