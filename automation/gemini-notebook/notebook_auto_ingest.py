#!/usr/bin/env python3
"""AI技術研究室 | Gemini Notebook 自動登録・読み戻しモジュール (notebook_auto_ingest.py v3.0).

目的:
対象Notebook (https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7) に対し、
1. 元YouTube動画（YouTube URLソース）
2. 独自研究ノート（Copied text または Markdown）
を自動登録し、登録結果を実際のNotebook画面から読み戻して検証する。

設計:
- [専用Chromeプロファイル] 既存の通常Chromeを破壊せず、専用ディレクトリ
  `%LOCALAPPDATA%/ai-video-research/chrome-notebook-profile` を使用してポート9222で起動。
  初回のみユーザーが通常ログインし、以後はそのセッションを永続再利用。
- [純粋Python WebSocket/CDPクライアント] 外部pip依存なしでCDP JSON-RPCを直接操作。
- [DOM自動操作] ソース追加モーダルを開き、YouTube URL投入および研究ノート投入を実行。
- [Readback検証] ソース一覧を走査し、YouTubeソースおよび研究ノートの存在・識別子を検証。
- [冪等性・二重登録防止] 同一動画が既にソース一覧に存在する場合は追加をスキップ。
- [Google Drive同期連携] Drive側専用フォルダへの自動配置も引き続き併用。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
AUTO_DIR = Path(__file__).resolve().parent

NOTEBOOK_ID = "e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7"
NOTEBOOK_URL = f"https://gemini.google.com/notebook/{NOTEBOOK_ID}"
DEFAULT_DRIVE_ROOT = Path("G:/マイドライブ")
DEFAULT_NOTEBOOK_SOURCES_DIR = DEFAULT_DRIVE_ROOT / "AI技術研究室_Notebookソース"
DEFAULT_CDP_PORT = 9222
DEFAULT_CDP_HOST = "127.0.0.1"

# Dedicated profile path for isolation and session persistence
DEFAULT_DEDICATED_PROFILE_DIR = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    / "ai-video-research"
    / "chrome-notebook-profile"
)
CHROME_EXECUTABLE_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
]


class MinimalWebSocket:
    """Minimal pure-Python RFC 6455 WebSocket client over standard socket."""

    def __init__(self, host: str, port: int, path: str, timeout: float = 25.0):
        self.host = host
        self.port = port
        self.path = path
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

        # Generate 16-byte random key
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode("ascii"))

        # Read handshake response
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket handshake connection closed unexpectedly")
            resp += chunk

        status_line = resp.split(b"\r\n")[0].decode("ascii", errors="replace")
        if "101" not in status_line:
            raise ConnectionError(f"WebSocket handshake failed: {status_line}")

    def send_text(self, payload: str):
        if not self.sock:
            raise ConnectionError("WebSocket not connected")
        data = payload.encode("utf-8")
        length = len(data)

        # Client-to-server frames MUST be masked
        header = bytearray([0x81])  # FIN=1, opcode=1 (text)
        mask_key = os.urandom(4)

        if length <= 125:
            header.append(0x80 | length)
        elif length <= 65535:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))

        header.extend(mask_key)
        # Mask the data
        masked_data = bytearray(length)
        for i in range(length):
            masked_data[i] = data[i] ^ mask_key[i % 4]

        self.sock.sendall(header + masked_data)

    def recv_text(self) -> str:
        if not self.sock:
            raise ConnectionError("WebSocket not connected")

        # Read 2-byte header
        header = self._recv_exact(2)
        opcode = header[0] & 0x0F
        masked = bool(header[1] & 0x80)
        payload_len = header[1] & 0x7F

        if payload_len == 126:
            payload_len = struct.unpack("!H", self._recv_exact(2))[0]
        elif payload_len == 127:
            payload_len = struct.unpack("!Q", self._recv_exact(8))[0]

        mask = self._recv_exact(4) if masked else None
        raw_payload = self._recv_exact(payload_len)

        if masked and mask:
            unmasked = bytearray(payload_len)
            for i in range(payload_len):
                unmasked[i] = raw_payload[i] ^ mask[i % 4]
            raw_payload = bytes(unmasked)

        return raw_payload.decode("utf-8", errors="replace")

    def _recv_exact(self, num_bytes: int) -> bytes:
        buf = b""
        while len(buf) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(buf))
            if not chunk:
                raise ConnectionError("Socket closed while reading frame")
            buf += chunk
        return buf

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


class CDPClient:
    """Lightweight pure-Python client for Chrome DevTools Protocol."""

    def __init__(self, host: str = DEFAULT_CDP_HOST, port: int = DEFAULT_CDP_PORT):
        self.host = host
        self.port = port
        self._msg_id = 0

    def is_port_open(self, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection((self.host, self.port), timeout=timeout):
                return True
        except Exception:
            return False

    def list_tabs(self, timeout: float = 2.0) -> List[Dict[str, Any]]:
        url = f"http://{self.host}:{self.port}/json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            all_tabs = json.loads(resp.read().decode("utf-8"))
            # Filter to top-level page targets only, excluding background iframes and extensions
            return [t for t in all_tabs if t.get("type") == "page"]

    def find_notebook_tab(self, notebook_id: str = NOTEBOOK_ID) -> Optional[Dict[str, Any]]:
        tabs = self.list_tabs()
        for tab in tabs:
            tab_url = tab.get("url", "")
            if (notebook_id in tab_url or "gemini.google.com/notebook" in tab_url) and "RotateCookiesPage" not in tab_url:
                return tab
        return None

    def execute_script_on_tab(self, tab: Dict[str, Any], js_expression: str, max_frames: int = 40) -> Any:
        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            raise ValueError("Tab has no webSocketDebuggerUrl")

        # Parse host, port, path from ws_url (e.g. ws://127.0.0.1:9222/devtools/page/...)
        m = re.match(r"ws://([^:/]+):(\d+)(/.*)", ws_url)
        if not m:
            raise ValueError(f"Invalid WebSocket URL: {ws_url}")

        host, port_str, path = m.group(1), m.group(2), m.group(3)
        ws = MinimalWebSocket(host, int(port_str), path)
        try:
            ws.connect()
            self._msg_id += 1
            cmd_id = self._msg_id
            cmd = {
                "id": cmd_id,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": js_expression,
                    "returnByValue": True,
                    "awaitPromise": True,
                },
            }
            ws.send_text(json.dumps(cmd))
            
            # Loop until matching message id response is received, skipping asynchronous CDP event frames
            resp = None
            for _ in range(max_frames):
                resp_raw = ws.recv_text()
                if not resp_raw:
                    continue
                try:
                    data = json.loads(resp_raw)
                except Exception:
                    continue
                if isinstance(data, dict) and data.get("id") == cmd_id:
                    resp = data
                    break

            if not resp:
                raise TimeoutError(f"CDP response for message id {cmd_id} not received within {max_frames} frames")

            if "error" in resp:
                raise RuntimeError(f"CDP error response: {resp['error']}")

            result = resp.get("result", {}).get("result", {})
            return result.get("value")
        finally:
            ws.close()


def find_chrome_binary() -> Optional[str]:
    """Find installed Google Chrome executable path on Windows."""
    for cand in CHROME_EXECUTABLE_CANDIDATES:
        p = Path(cand)
        if p.is_file():
            return str(p)
    return None


def launch_dedicated_chrome(
    port: int = DEFAULT_CDP_PORT,
    profile_dir: Path = DEFAULT_DEDICATED_PROFILE_DIR,
    target_url: str = NOTEBOOK_URL,
) -> Dict[str, Any]:
    """Launch visible Chrome with a dedicated, isolated user data directory and remote debugging port."""
    chrome_bin = find_chrome_binary()
    if not chrome_bin:
        return {
            "status": "CHROME_NOT_FOUND",
            "message": "Google Chrome executable was not found on this system.",
        }

    profile_dir.mkdir(parents=True, exist_ok=True)

    args = [
        chrome_bin,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        target_url,
    ]

    try:
        proc = subprocess.Popen(args)
        return {
            "status": "CHROME_LAUNCHED",
            "pid": proc.pid,
            "port": port,
            "profile_dir": str(profile_dir),
            "target_url": target_url,
        }
    except Exception as ex:
        return {
            "status": "CHROME_LAUNCH_ERROR",
            "message": str(ex),
        }


def build_transcript_okf_content(
    video_id: str,
    video_url: str,
    video_title: str,
    cues: Optional[List[Dict[str, Any]]] = None,
    raw_text: Optional[str] = None,
    language: str = "ja",
    status: str = "UNVERIFIED",
) -> str:
    """Generate exact verbatim transcript OKF document with OKF v0.2 frontmatter."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    transcript_logical_id = f"youtube:{video_id}:transcript"
    research_logical_id = f"youtube:{video_id}:research"
    cues_list = cues or []
    cue_count = len(cues_list)

    lines = [
        "---",
        'okf_version: "0.2"',
        'type: "TRANSCRIPT"',
        f'title: "【字幕原文】 {video_title}"',
        f'logical_id: "{transcript_logical_id}"',
        f'research_logical_id: "{research_logical_id}"',
        f'related_research_id: "{research_logical_id}"',
        f'video_id: "{video_id}"',
        f'resource: "{video_url}"',
        f'url: "{video_url}"',
        f'canonical_url: "{video_url}"',
        f'original_url: "{video_url}"',
        f'language: "{language}"',
        f'acquired_at: "{today}"',
        f"cue_count: {cue_count}",
        f'transcript_status: "{status}"',
        'acquisition_method: "YOUTUBE_TIMEDTEXT_API"',
        "tags:",
        '  - "AI技術研究室"',
        '  - "字幕原文"',
        '  - "一次資料"',
        "---",
        "",
        f"# 【字幕原文】 {video_title}",
        "",
        f"<!-- ID: AI_VIDEO_TRANSCRIPT_RAW:{video_id} -->",
        f"<!-- LOGICAL_ID: {transcript_logical_id} -->",
        f"<!-- RESEARCH_REF: {research_logical_id} -->",
        f"<!-- RELATED_RESEARCH_ID: {research_logical_id} -->",
        f"<!-- RESOURCE: {video_url} -->",
        f"<!-- CANONICAL_URL: {video_url} -->",
        f"<!-- ORIGINAL_URL: {video_url} -->",
        f"- **元YouTube URL**: {video_url}",
        f"- **動画URL**: {video_url}",
        f"- **総Cue数**: {cue_count} 件",
        f"- **検証状態**: {status}",
        "- **原文保持規約**: 発話テキストは要約・清書・改変を行わず、取得全量をそのまま記録しています。",
        "",
        "## 字幕発話タイムライン (取得全量)",
        "",
    ]

    if cues_list:
        for c in cues_list:
            if isinstance(c, (list, tuple)):
                st_sec = float(c[0]) if len(c) > 0 else 0.0
                txt = str(c[2]).strip() if len(c) > 2 else ""
            elif isinstance(c, dict):
                st_sec = float(c.get("start", 0))
                txt = str(c.get("text", "")).strip()
            else:
                st_sec = 0.0
                txt = str(c).strip()
            m = int(st_sec // 60)
            s = int(st_sec % 60)
            mmss = f"{m:02d}:{s:02d}"
            lines.append(f"- **[{mmss}]** ({st_sec:.1f}s) {txt}")
    elif raw_text:
        lines.append(raw_text)
    else:
        lines.append("- (字幕発話データなし)")

    return "\n".join(lines)


def evaluate_2_source_okf_independence(
    items: List[Dict[str, Any]],
    video_id: str,
    video_title: str,
) -> Dict[str, Any]:
    """Verify presence and independence of Transcript OKF and Research Note OKF.
    
    Conforms to docs/OKF_KNOWLEDGE_ROADMAP.md v1.1 '1動画2ソースMVP完成契約'.
    Requires Transcript OKF and Research Note OKF to exist as separate, distinct DOM elements.
    """
    note_identifier = f"AI_VIDEO_RESEARCH_NOTE:{video_id}"
    transcript_identifier = f"AI_VIDEO_TRANSCRIPT_RAW:{video_id}"
    transcript_alt_id = f"AI_VIDEO_TRANSCRIPT:{video_id}"

    yt_candidates = []
    note_candidates = []
    transcript_candidates = []

    title_snippets = []
    if video_title:
        clean_title = video_title.strip()
        if len(clean_title) >= 6:
            title_snippets.append(clean_title[:10])
            title_snippets.append(clean_title[:15])
            title_snippets.append(clean_title[-8:])

    for it in items:
        txt = it.get("text", "")
        idx = it.get("index")

        is_explicit_transcript = (
            transcript_identifier in txt
            or transcript_alt_id in txt
            or f"youtube:{video_id}:transcript" in txt
            or "【字幕原文】" in txt
            or ("字幕" in txt and video_id in txt)
        )
        is_explicit_note = (
            note_identifier in txt
            or f"youtube:{video_id}:research" in txt
            or f"研究ノート_{video_id}" in txt
            or f"研究ノート {video_id}" in txt
            or ("【研究カード】" in txt and video_id in txt)
        )

        if is_explicit_transcript:
            transcript_candidates.append(idx)
        elif is_explicit_note:
            note_candidates.append(idx)
        else:
            # Generic Copied text MD items
            if ("Copied text" in txt or "Copied tex" in txt) and ("MD" in txt or "\nMD" in txt):
                note_candidates.append(idx)
                transcript_candidates.append(idx)
            elif "MD" in txt and (video_id in txt or "研究ノート" in txt):
                note_candidates.append(idx)

            # YouTube URL candidates
            id_match = video_id in txt
            title_match = any(snip in txt for snip in title_snippets) if title_snippets else False
            is_yt_type = "YouTube" in txt or "youtube.com" in txt or "youtu.be" in txt
            if (id_match or (title_match and is_yt_type) or (title_match and not ("MD" in txt or ".md" in txt))) and not ("MD" in txt):
                yt_candidates.append(idx)

    chosen_yt_idx = yt_candidates[0] if yt_candidates else None
    chosen_note_idx = None
    chosen_transcript_idx = None

    if note_candidates and transcript_candidates:
        distinct_pairs = [
            (n, t) for n in note_candidates for t in transcript_candidates if n != t and n != chosen_yt_idx and t != chosen_yt_idx
        ]
        if distinct_pairs:
            chosen_note_idx, chosen_transcript_idx = distinct_pairs[-1]
        else:
            if note_candidates:
                chosen_note_idx = note_candidates[-1]
            if transcript_candidates and transcript_candidates[-1] != chosen_note_idx:
                chosen_transcript_idx = transcript_candidates[-1]
    else:
        if note_candidates:
            chosen_note_idx = note_candidates[-1]
        if transcript_candidates:
            chosen_transcript_idx = transcript_candidates[-1]

    yt_found = chosen_yt_idx is not None
    note_found = chosen_note_idx is not None
    transcript_found = chosen_transcript_idx is not None
    is_2_source_okf = (
        note_found
        and transcript_found
        and chosen_note_idx != chosen_transcript_idx
    )

    return {
        "youtube_found": yt_found,
        "research_note_found": note_found,
        "transcript_source_found": transcript_found,
        "youtube_item_index": chosen_yt_idx,
        "research_note_item_index": chosen_note_idx,
        "transcript_item_index": chosen_transcript_idx,
        "is_2_source_okf_verified": is_2_source_okf,
    }


def evaluate_sources_independence(
    items: List[Dict[str, Any]],
    video_id: str,
    video_title: str,
) -> Tuple[bool, bool, Optional[int], Optional[int]]:
    """Verify that YouTube source and Research Note exist as separate, distinct DOM elements.
    
    Prevents false PASS when only 1 element contains both or only video_id is present.
    Maintains backward compatibility with tests expecting a 4-element tuple.
    """
    res = evaluate_2_source_okf_independence(items, video_id, video_title)
    return (
        res["youtube_found"],
        res["research_note_found"],
        res["youtube_item_index"],
        res["research_note_item_index"],
    )


def readback_notebook_sources_via_cdp(
    client: CDPClient,
    tab: Dict[str, Any],
    video_id: str,
    video_title: str,
) -> Dict[str, Any]:
    """Inspect actual NotebookLM DOM via CDP to extract registered sources and verify readback."""
    js_extract_sources = """
    (async () => {
        // 1. Ensure source list dialog is open
        let dialog = document.querySelector('mat-dialog-container, [role="dialog"]');
        if (!dialog) {
            const chip = document.querySelector('gem-source-list-chip, [aria-label*="ソース"]');
            if (chip) {
                chip.click();
                await new Promise(r => setTimeout(r, 1000));
            }
        }

        // 2. Query source items
        const elements = Array.from(document.querySelectorAll(
            'project-file-upload-item, [role="listitem"], .source-card, .source-title, [data-source-id], mat-list-item, div.source-item, .source-chip'
        ));

        const items = [];
        elements.forEach((el, idx) => {
            const txt = (el.innerText || el.textContent || '').trim();
            if (txt) {
                items.push({ index: idx, tag: el.tagName, text: txt });
            }
        });

        return {
            item_count: items.length,
            items: items,
            full_text_sample: document.body ? document.body.innerText.slice(0, 1500) : ''
        };
    })()
    """
    try:
        data = client.execute_script_on_tab(tab, js_extract_sources)
        if not isinstance(data, dict):
            return {
                "status": "READBACK_PARSE_ERROR",
                "message": "DOM script execution returned non-dict value",
                "youtube_source_found": False,
                "research_note_found": False,
                "transcript_source_found": False,
                "is_2_source_okf_verified": False,
            }

        items = data.get("items", [])
        okf_res = evaluate_2_source_okf_independence(items, video_id, video_title)
        yt_found = okf_res["youtube_found"]
        note_found = okf_res["research_note_found"]
        transcript_found = okf_res["transcript_source_found"]
        is_2_source_okf = okf_res["is_2_source_okf_verified"]

        if is_2_source_okf:
            status = "SUCCESS_2_SOURCE_OKF"
        elif yt_found and note_found:
            status = "NOTEBOOK_READBACK_PASS"
        elif yt_found or note_found or transcript_found:
            status = "NOTEBOOK_READBACK_PARTIAL"
        else:
            status = "NOTEBOOK_READBACK_NOT_FOUND"

        return {
            "status": status,
            "youtube_source_found": yt_found,
            "research_note_found": note_found,
            "transcript_source_found": transcript_found,
            "is_2_source_okf_verified": is_2_source_okf,
            "youtube_item_index": okf_res["youtube_item_index"],
            "research_note_item_index": okf_res["research_note_item_index"],
            "transcript_item_index": okf_res["transcript_item_index"],
            "detected_source_count": data.get("item_count", 0),
            "sources_sample": [it.get("text", "") for it in items[:10]],
        }
    except Exception as ex:
        return {
            "status": "READBACK_EXCEPTION",
            "message": str(ex),
            "youtube_source_found": False,
            "research_note_found": False,
        }


def add_youtube_source_via_cdp(
    client: CDPClient,
    tab: Dict[str, Any],
    video_id: str,
    video_url: str,
) -> Dict[str, Any]:
    """Open Notebook source modal and add YouTube URL source via CDP DOM interaction."""
    js_add_youtube = f"""
    (async () => {{
        // 1. Ensure source dialog is open
        let dialog = document.querySelector('mat-dialog-container');
        if (!dialog) {{
            const chip = document.querySelector('gem-source-list-chip, [aria-label*="ソース"]');
            if (chip) {{
                chip.click();
                await new Promise(r => setTimeout(r, 1000));
            }}
        }}

        // 2. Click "ソースを追加" button
        const addBtn = Array.from(document.querySelectorAll('button, [role="button"]'))
            .find(b => (b.getAttribute('aria-label') || '').includes('ソースを追加') || (b.innerText || '').includes('ソースを追加'));
        if (!addBtn) {{
            return {{ success: false, reason: "ソースを追加 button not found" }};
        }}
        addBtn.click();
        await new Promise(r => setTimeout(r, 1000));

        // 3. Select "ウェブサイトを追加" option
        const ytOption = Array.from(document.querySelectorAll('span, button, div[role="button"], [role="menuitem"]'))
            .find(el => (el.innerText || '').trim() === 'ウェブサイトを追加' || (el.innerText || '').trim().includes('ウェブサイト'));
        if (!ytOption) {{
            return {{ success: false, reason: "ウェブサイトを追加 option not found" }};
        }}
        ytOption.click();
        await new Promise(r => setTimeout(r, 1000));

        // 4. Set YouTube URL into textarea
        const inputEl = document.querySelector('textarea, input[type="text"], input[type="url"]');
        if (!inputEl) {{
            return {{ success: false, reason: "URL input element not found in modal" }};
        }}
        inputEl.focus();
        inputEl.value = {json.dumps(video_url)};
        inputEl.dispatchEvent(new Event('input', {{ bubbles: true }}));
        inputEl.dispatchEvent(new Event('change', {{ bubbles: true }}));
        await new Promise(r => setTimeout(r, 600));

        // 5. Click "挿入" button
        const confirmBtn = Array.from(document.querySelectorAll('button, [role="button"]'))
            .find(b => (b.innerText || '').trim() === '挿入' && !b.disabled);
        if (confirmBtn) {{
            confirmBtn.click();
            await new Promise(r => setTimeout(r, 2500));
            return {{ success: true, action: "YOUTUBE_URL_INSERTED" }};
        }}
        return {{ success: false, reason: "挿入 button not found or disabled" }};
    }})()
    """
    try:
        res = client.execute_script_on_tab(tab, js_add_youtube)
        return res if isinstance(res, dict) else {"success": False, "raw": res}
    except Exception as ex:
        return {"success": False, "error": str(ex)}


def add_copied_text_source_via_cdp(
    client: CDPClient,
    tab: Dict[str, Any],
    video_id: str,
    note_content: str,
    note_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Add research note as Copied text source with unique identifier via CDP DOM interaction."""
    title_to_set = note_title or f"AI_VIDEO_RESEARCH_NOTE:{video_id}"
    body_to_set = f"# {title_to_set}\n\n<!-- ID: {title_to_set} -->\n" + note_content

    js_add_text = f"""
    (async () => {{
        // 1. Ensure source dialog is open
        let dialog = document.querySelector('mat-dialog-container');
        if (!dialog) {{
            const chip = document.querySelector('gem-source-list-chip, [aria-label*="ソース"]');
            if (chip) {{
                chip.click();
                await new Promise(r => setTimeout(r, 1000));
            }}
        }}

        // 2. Click "ソースを追加" button
        const addBtn = Array.from(document.querySelectorAll('button, [role="button"]'))
            .find(b => (b.getAttribute('aria-label') || '').includes('ソースを追加') || (b.innerText || '').includes('ソースを追加'));
        if (!addBtn) {{
            return {{ success: false, reason: "ソースを追加 button not found" }};
        }}
        addBtn.click();
        await new Promise(r => setTimeout(r, 1000));

        // 3. Select "テキストを追加" option
        const textOption = Array.from(document.querySelectorAll('span, button, div[role="button"], [role="menuitem"]'))
            .find(el => (el.innerText || '').trim() === 'テキストを追加');
        if (!textOption) {{
            return {{ success: false, reason: "テキストを追加 option not found" }};
        }}
        textOption.click();
        await new Promise(r => setTimeout(r, 1000));

        // 4. Set text in textarea
        const textarea = document.querySelector('textarea, input[type="text"]');
        if (!textarea) {{
            return {{ success: false, reason: "Textarea input element not found in modal" }};
        }}
        textarea.focus();
        textarea.value = {json.dumps(body_to_set)};
        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
        await new Promise(r => setTimeout(r, 600));

        // 5. Click "テキストを追加" confirm button inside GEM-BUTTON
        const saveBtn = Array.from(document.querySelectorAll('gem-button button, button'))
            .find(b => (b.innerText || '').trim() === 'テキストを追加' && !b.disabled);
        if (saveBtn) {{
            saveBtn.click();
            await new Promise(r => setTimeout(r, 2500));
            return {{ success: true, action: "COPIED_TEXT_NOTE_INSERTED" }};
        }}
        return {{ success: false, reason: "テキストを追加 confirm button not found or disabled" }};
    }})()
    """
    try:
        res = client.execute_script_on_tab(tab, js_add_text)
        return res if isinstance(res, dict) else {"success": False, "raw": res}
    except Exception as ex:
        return {"success": False, "error": str(ex)}


def add_transcript_source_via_cdp(
    client: CDPClient,
    tab: Dict[str, Any],
    video_id: str,
    transcript_content: str,
    transcript_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Add verbatim transcript OKF source via CDP DOM interaction."""
    title_to_set = transcript_title or f"AI_VIDEO_TRANSCRIPT_RAW:{video_id}"
    body_to_set = (
        transcript_content
        if transcript_content.startswith("---")
        else f"# {title_to_set}\n\n<!-- ID: {title_to_set} -->\n" + transcript_content
    )

    js_add_text = f"""
    (async () => {{
        // 1. Ensure source dialog is open
        let dialog = document.querySelector('mat-dialog-container');
        if (!dialog) {{
            const chip = document.querySelector('gem-source-list-chip, [aria-label*="ソース"]');
            if (chip) {{
                chip.click();
                await new Promise(r => setTimeout(r, 1000));
            }}
        }}

        // 2. Click "ソースを追加" button
        const addBtn = Array.from(document.querySelectorAll('button, [role="button"]'))
            .find(b => (b.getAttribute('aria-label') || '').includes('ソースを追加') || (b.innerText || '').includes('ソースを追加'));
        if (!addBtn) {{
            return {{ success: false, reason: "ソースを追加 button not found" }};
        }}
        addBtn.click();
        await new Promise(r => setTimeout(r, 1000));

        // 3. Select "テキストを追加" option
        const textOption = Array.from(document.querySelectorAll('span, button, div[role="button"], [role="menuitem"]'))
            .find(el => (el.innerText || '').trim() === 'テキストを追加');
        if (!textOption) {{
            return {{ success: false, reason: "テキストを追加 option not found" }};
        }}
        textOption.click();
        await new Promise(r => setTimeout(r, 1000));

        // 4. Set text in textarea
        const textarea = document.querySelector('textarea, input[type="text"]');
        if (!textarea) {{
            return {{ success: false, reason: "Textarea input element not found in modal" }};
        }}
        textarea.focus();
        textarea.value = {json.dumps(body_to_set)};
        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
        await new Promise(r => setTimeout(r, 600));

        // 5. Click "テキストを追加" confirm button inside GEM-BUTTON
        const saveBtn = Array.from(document.querySelectorAll('gem-button button, button'))
            .find(b => (b.innerText || '').trim() === 'テキストを追加' && !b.disabled);
        if (saveBtn) {{
            saveBtn.click();
            await new Promise(r => setTimeout(r, 2500));
            return {{ success: true, action: "TRANSCRIPT_OKF_INSERTED" }};
        }}
        return {{ success: false, reason: "テキストを追加 confirm button not found or disabled" }};
    }})()
    """
    try:
        res = client.execute_script_on_tab(tab, js_add_text)
        return res if isinstance(res, dict) else {"success": False, "raw": res}
    except Exception as ex:
        return {"success": False, "error": str(ex)}


def sync_to_drive_notebook_sources(
    video_id: str,
    video_url: str,
    video_title: str,
    research_md_path: Path,
    target_dir: Path = DEFAULT_NOTEBOOK_SOURCES_DIR,
    transcript_content: Optional[str] = None,
    cues: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Place the sources (YouTube reference, Research Markdown & Transcript OKF) into Drive folder."""
    if not target_dir.parent.exists():
        return {
            "status": "DRIVE_ROOT_NOT_FOUND",
            "message": f"Google Driveマウントパス '{target_dir.parent}' が見つかりません。",
            "synced_files": [],
        }

    target_dir.mkdir(parents=True, exist_ok=True)

    yt_file = target_dir / f"{video_id}_youtube_source.txt"
    yt_content = (
        f"【YouTube元動画資料】\n"
        f"動画ID: {video_id}\n"
        f"タイトル: {video_title}\n"
        f"URL: {video_url}\n"
        f"登録日時: {datetime.now(timezone.utc).isoformat()}\n"
        f"※NotebookLMでYouTubeソースとして追加する場合は、上記URLを直接「YouTube」ソース欄へ投入してください。\n"
    )
    yt_file.write_text(yt_content, encoding="utf-8")

    md_file = target_dir / f"{video_id}_research_note.md"
    if research_md_path.exists():
        md_content = research_md_path.read_text(encoding="utf-8")
        md_file.write_text(md_content, encoding="utf-8")
    else:
        md_content = f"# 研究ノート {video_id}\nURL: {video_url}\n"
        md_file.write_text(md_content, encoding="utf-8")

    # Transcript OKF source
    tr_file = target_dir / f"{video_id}_transcript_okf.md"
    if transcript_content:
        tr_text = transcript_content
    elif cues:
        tr_text = build_transcript_okf_content(
            video_id=video_id,
            video_url=video_url,
            video_title=video_title,
            cues=cues,
        )
    else:
        tr_text = build_transcript_okf_content(
            video_id=video_id,
            video_url=video_url,
            video_title=video_title,
            raw_text="- (字幕発話データ未指定)",
        )
    tr_file.write_text(tr_text, encoding="utf-8")

    yt_sha = hashlib.sha256(yt_file.read_bytes()).hexdigest()
    md_sha = hashlib.sha256(md_file.read_bytes()).hexdigest()
    tr_sha = hashlib.sha256(tr_file.read_bytes()).hexdigest()

    return {
        "status": "DRIVE_SYNC_SUCCESS",
        "target_dir": str(target_dir),
        "synced_files": [
            {
                "kind": "YOUTUBE_SOURCE_REF",
                "path": str(yt_file),
                "sha256": yt_sha,
                "size_bytes": yt_file.stat().st_size,
            },
            {
                "kind": "RESEARCH_NOTE_MARKDOWN",
                "path": str(md_file),
                "sha256": md_sha,
                "size_bytes": md_file.stat().st_size,
            },
            {
                "kind": "TRANSCRIPT_OKF_MARKDOWN",
                "path": str(tr_file),
                "sha256": tr_sha,
                "size_bytes": tr_file.stat().st_size,
            },
        ],
    }


def ingest_and_verify_notebook(
    video_id: str,
    video_url: str,
    video_title: str,
    research_md_path: Path,
    mock_cdp: bool = False,
    mock_sources: Optional[List[str]] = None,
    allow_add: bool = True,
    auto_launch_chrome: bool = True,
    mock_blocked_login: bool = False,
    drive_dir: Path = DEFAULT_NOTEBOOK_SOURCES_DIR,
    cues: Optional[List[Dict[str, Any]]] = None,
    transcript_content: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute complete notebook ingestion workflow: pre-readback, conditional UI ingest & post-readback."""
    print("=" * 60)
    print("AI技術研究室 | Gemini Notebook 自動ソース登録・読み戻し検証 (2-Source OKF)")
    print(f"対象Notebook: {NOTEBOOK_URL}")
    print(f"動画ID: {video_id}")
    print("=" * 60)

    # 0. Build Transcript OKF content
    if transcript_content:
        final_transcript_text = transcript_content
    elif cues:
        final_transcript_text = build_transcript_okf_content(
            video_id=video_id,
            video_url=video_url,
            video_title=video_title,
            cues=cues,
        )
    else:
        final_transcript_text = build_transcript_okf_content(
            video_id=video_id,
            video_url=video_url,
            video_title=video_title,
            raw_text="- (字幕発話データ未指定)",
        )

    # 1. Drive Sync (Guaranteed deterministic channel: YT txt, Research MD & Transcript OKF MD)
    drive_res = sync_to_drive_notebook_sources(
        video_id=video_id,
        video_url=video_url,
        video_title=video_title,
        research_md_path=research_md_path,
        target_dir=drive_dir,
        transcript_content=final_transcript_text,
    )
    print(f"[1/3] Google Drive同期フォルダ連携: {drive_res.get('status')}")

    # 2. CDP Probe and Live DOM Interaction
    client = CDPClient()
    cdp_available = mock_cdp or client.is_port_open()

    # Automatically launch dedicated Chrome if port is closed
    if not mock_cdp and not cdp_available and auto_launch_chrome:
        print(f"[2/3] Chrome CDPポート (Port {DEFAULT_CDP_PORT}) が閉じています。専用Chromeを自動起動します...")
        launch_res = launch_dedicated_chrome()
        if launch_res.get("status") == "CHROME_LAUNCHED":
            print(f"  - 専用Chrome自動起動成功 (PID: {launch_res.get('pid')})。ポート開放を待機中...")
            for _ in range(20):
                time.sleep(0.5)
                if client.is_port_open():
                    cdp_available = True
                    break
        else:
            print(f"  - [WARNING] 専用Chrome自動起動失敗: {launch_res.get('message')}")

    print(f"[2/3] Chrome CDPポートプローブ (Port {DEFAULT_CDP_PORT}): {'OPEN' if cdp_available else 'CLOSED'}")

    actions_taken = []
    readback_res = {
        "status": "NOTEBOOK_READBACK_SKIPPED",
        "youtube_source_found": False,
        "research_note_found": False,
        "transcript_source_found": False,
        "is_2_source_okf_verified": False,
        "message": "CDP port is not open; launch Chrome with dedicated profile.",
    }

    if mock_cdp:
        if mock_blocked_login:
            readback_res = {
                "status": "BLOCKED_INITIAL_GOOGLE_LOGIN",
                "youtube_source_found": False,
                "research_note_found": False,
                "transcript_source_found": False,
                "is_2_source_okf_verified": False,
                "message": "専用Chromeで初回Googleログインが必要です（Mock）。",
            }
        else:
            # Mock mode for deterministic testing
            current_sources = list(mock_sources) if mock_sources is not None else []
            items = [{"index": i, "text": s} for i, s in enumerate(current_sources)]
            okf_pre = evaluate_2_source_okf_independence(items, video_id, video_title)
            yt_found = okf_pre["youtube_found"]
            note_found = okf_pre["research_note_found"]
            transcript_found = okf_pre["transcript_source_found"]

            # Ingest missing sources if allowed
            if allow_add:
                if not yt_found:
                    current_sources.append(f"https://www.youtube.com/watch?v={video_id}")
                    actions_taken.append("YOUTUBE_URL_INSERTED")
                if not note_found:
                    current_sources.append(f"AI_VIDEO_RESEARCH_NOTE:{video_id}")
                    actions_taken.append("COPIED_TEXT_NOTE_INSERTED")
                if not transcript_found and cues is not None:
                    current_sources.append(f"AI_VIDEO_TRANSCRIPT_RAW:{video_id}")
                    actions_taken.append("TRANSCRIPT_OKF_INSERTED")

            # Post-readback
            post_items = [{"index": i, "text": s} for i, s in enumerate(current_sources)]
            okf_post = evaluate_2_source_okf_independence(post_items, video_id, video_title)
            yt_found_post = okf_post["youtube_found"]
            note_found_post = okf_post["research_note_found"]
            transcript_found_post = okf_post["transcript_source_found"]
            is_2_source_post = okf_post["is_2_source_okf_verified"]

            if is_2_source_post:
                status = "SUCCESS_2_SOURCE_OKF"
            elif yt_found_post and note_found_post:
                status = "NOTEBOOK_READBACK_PASS"
            elif yt_found_post or note_found_post or transcript_found_post:
                status = "NOTEBOOK_READBACK_PARTIAL"
            else:
                status = "NOTEBOOK_READBACK_NOT_FOUND"

            readback_res = {
                "status": status,
                "youtube_source_found": yt_found_post,
                "research_note_found": note_found_post,
                "transcript_source_found": transcript_found_post,
                "is_2_source_okf_verified": is_2_source_post,
                "youtube_item_index": okf_post["youtube_item_index"],
                "research_note_item_index": okf_post["research_note_item_index"],
                "transcript_item_index": okf_post["transcript_item_index"],
                "detected_source_count": len(post_items),
                "sources_sample": current_sources[:10],
                "actions_taken": actions_taken,
            }
    elif cdp_available:
        try:
            tabs = client.list_tabs()
            # Detect Google login screen on actual page tabs
            login_tab = next(
                (t for t in tabs if ("accounts.google.com/signin" in t.get("url", "") or "accounts.google.com/ServiceLogin" in t.get("url", "") or "ログイン" in t.get("title", "") or "Sign in" in t.get("title", "")) and "RotateCookiesPage" not in t.get("url", "")),
                None
            )
            notebook_tab = client.find_notebook_tab(NOTEBOOK_ID)

            if not notebook_tab and login_tab:
                print("  - [BLOCKED] Googleアカウントの初回ログイン画面が検出されました。Notebookへアクセスできません。")
                readback_res = {
                    "status": "BLOCKED_INITIAL_GOOGLE_LOGIN",
                    "youtube_source_found": False,
                    "research_note_found": False,
                    "transcript_source_found": False,
                    "is_2_source_okf_verified": False,
                    "message": "専用Chromeで初回Googleログインが必要です。手動ログイン完了後に再実行してください。",
                }
            elif notebook_tab:
                tab_url = notebook_tab.get("url", "")
                if "accounts.google.com" in tab_url and "RotateCookiesPage" not in tab_url:
                    print("  - [BLOCKED] NotebookタブがGoogleログイン画面へリダイレクトされています。")
                    readback_res = {
                        "status": "BLOCKED_INITIAL_GOOGLE_LOGIN",
                        "youtube_source_found": False,
                        "research_note_found": False,
                        "transcript_source_found": False,
                        "is_2_source_okf_verified": False,
                        "message": "Notebookタブがログイン画面へリダイレクトされています。手動ログインが必要です。",
                    }
                else:
                    print(f"  - NotebookLMタブ検出: {notebook_tab.get('title')}")
                    # Step A: Pre-readback
                    pre_rb = readback_notebook_sources_via_cdp(client, notebook_tab, video_id, video_title)
                    yt_already = pre_rb.get("youtube_source_found", False)
                    note_already = pre_rb.get("research_note_found", False)
                    transcript_already = pre_rb.get("transcript_source_found", False)

                    if allow_add:
                        # Step B: Add missing YouTube source if not present
                        if not yt_already:
                            print(f"  - [CDP ACTION] YouTube URLソースを追加します: {video_url}")
                            yt_add_res = add_youtube_source_via_cdp(client, notebook_tab, video_id, video_url)
                            actions_taken.append({"action": "ADD_YOUTUBE", "result": yt_add_res})
                            time.sleep(2.0)
                        else:
                            print("  - [CDP SKIP] YouTube URLソースは既に登録済みです。")

                        # Step C: Add missing Research Note if not present
                        if not note_already:
                            print(f"  - [CDP ACTION] 研究ノート(Copied text)を追加します: AI_VIDEO_RESEARCH_NOTE:{video_id}")
                            note_content = research_md_path.read_text(encoding="utf-8") if research_md_path.exists() else f"# 研究ノート {video_id}\nURL: {video_url}\n"
                            note_add_res = add_copied_text_source_via_cdp(
                                client=client,
                                tab=notebook_tab,
                                video_id=video_id,
                                note_content=note_content,
                            )
                            actions_taken.append({"action": "ADD_RESEARCH_NOTE", "result": note_add_res})
                            time.sleep(2.0)
                        else:
                            print("  - [CDP SKIP] 研究ノートソースは既に登録済みです。")

                        # Step D: Add missing Transcript OKF source if not present
                        if not transcript_already:
                            print(f"  - [CDP ACTION] 字幕原文OKF(Copied text)を追加します: AI_VIDEO_TRANSCRIPT_RAW:{video_id}")
                            tr_add_res = add_transcript_source_via_cdp(
                                client=client,
                                tab=notebook_tab,
                                video_id=video_id,
                                transcript_content=final_transcript_text,
                            )
                            actions_taken.append({"action": "ADD_TRANSCRIPT_OKF", "result": tr_add_res})
                            time.sleep(2.0)
                        else:
                            print("  - [CDP SKIP] 字幕原文OKFソースは既に登録済みです。")
                    else:
                        print("  - [CDP SKIP] allow_add=False のため追加操作をスキップします。")

                    # Step E: Post-readback
                    if actions_taken:
                        time.sleep(1.0)
                        readback_res = readback_notebook_sources_via_cdp(client, notebook_tab, video_id, video_title)
                    else:
                        readback_res = pre_rb

                    readback_res["actions_taken"] = actions_taken
                    print(f"  - Notebook実画面Readbackステータス: {readback_res.get('status')}")
            else:
                readback_res = {
                    "status": "NOTEBOOK_TAB_NOT_FOUND",
                    "youtube_source_found": False,
                    "research_note_found": False,
                    "transcript_source_found": False,
                    "is_2_source_okf_verified": False,
                    "message": f"Chrome is running on port {DEFAULT_CDP_PORT}, but Notebook '{NOTEBOOK_ID}' is not opened.",
                }
        except Exception as ex:
            readback_res = {
                "status": "CDP_INTERACTION_ERROR",
                "youtube_source_found": False,
                "research_note_found": False,
                "transcript_source_found": False,
                "is_2_source_okf_verified": False,
                "message": str(ex),
            }

    print(f"[3/3] Notebook Readback検証結果: {readback_res.get('status')}")
    print(f"  - YouTubeソース検出: {readback_res.get('youtube_source_found')}")
    print(f"  - 研究ノート検出: {readback_res.get('research_note_found')}")
    print(f"  - 字幕原文OKF検出: {readback_res.get('transcript_source_found')}")
    print(f"  - 2ソースOKF完全立証: {readback_res.get('is_2_source_okf_verified')}")
    if actions_taken:
        print(f"  - 実行したUI追加アクション: {actions_taken}")

    is_2_source_okf = readback_res.get("is_2_source_okf_verified", False)
    is_full_success = (
        drive_res.get("status") == "DRIVE_SYNC_SUCCESS"
        and (
            is_2_source_okf
            or (readback_res.get("youtube_source_found") is True and readback_res.get("research_note_found") is True)
        )
    )

    final_status = "SUCCESS_2_SOURCE_OKF" if (is_full_success and is_2_source_okf) else (
        "NOTEBOOK_REGISTRATION_VERIFIED" if is_full_success else "NOTEBOOK_SYNC_PENDING_READBACK"
    )

    return {
        "status": final_status,
        "notebook_id": NOTEBOOK_ID,
        "notebook_url": NOTEBOOK_URL,
        "drive_sync": drive_res,
        "cdp_available": cdp_available,
        "actions_taken": actions_taken,
        "readback": readback_res,
        "is_full_success": is_full_success,
        "is_2_source_okf_verified": is_2_source_okf,
        "transcript_source_found": readback_res.get("transcript_source_found", False),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(description="Gemini Notebook 自動登録・読み戻しモジュール v3.0")
    parser.add_argument("video_id", nargs="?", default=None, help="登録対象のYouTube動画ID (--launch-chrome時は省略可)")
    parser.add_argument("--url", help="YouTube動画URL", default=None)
    parser.add_argument("--title", help="動画タイトル", default="YouTube動画")
    parser.add_argument("--research-md", help="研究ノートMarkdownファイルのパス", default=None)
    parser.add_argument("--launch-chrome", action="store_true", help="専用プロファイルでChromeを起動する")
    parser.add_argument("--mock-cdp", action="store_true", help="テスト用Mock CDPモード")
    return parser


def main(args_list: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(args_list)

    if args.launch_chrome:
        res = launch_dedicated_chrome()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if not args.video_id:
        parser.error("登録処理には video_id が必要です（--launch-chrome 時は不要）")

    v_url = args.url or f"https://www.youtube.com/watch?v={args.video_id}"
    md_p = Path(args.research_md) if args.research_md else Path(f"research/{args.video_id}.md")
    res = ingest_and_verify_notebook(
        video_id=args.video_id,
        video_url=v_url,
        video_title=args.title,
        research_md_path=md_p,
        mock_cdp=args.mock_cdp,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("is_full_success") else 1


if __name__ == "__main__":
    sys.exit(main())
