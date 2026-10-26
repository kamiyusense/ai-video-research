"""字幕保存スイッチのWindows起動入口。

直接起動はswitch_appの1ボタン画面を使う。
以下の旧2ボタン試作関数は既存テスト・移行参照用として残す。
新アプリはPowerShell試作のprocess()を呼び出さない。
"""
from __future__ import annotations

import queue
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

TOOLS = Path(__file__).resolve().parent
VAULT = Path(r"C:\Users\yuuki\Documents\AI動画研究室")
SCRIPT = TOOLS / "research_from_url.ps1"
PUBLISH = TOOLS / "publish_to_github.ps1"
LOG_FILE = TOOLS / "subtitle_switch.log"
MAX_VIDEOS = 10   # 1回に処理する上限（research_batch.ps1 と同じ）
WAIT_SEC = 20     # 1本ごとの待ち時間（YouTube/Googleへの負荷を避ける。research_batch.ps1 と同じ）

VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|live/|embed/)([A-Za-z0-9_-]{11})")
BARE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

WAIT_MANUAL = 9
ABORT_CODES = {3, 4}   # ログイン不可・Notebook登録失敗は同じ原因で全部失敗するので残りを中止
EXIT_LABELS = {
    2: "NG: 動画IDを読み取れません",
    3: "NG: Notebookにログインできません → 残りを中止",
    4: "NG: Notebook登録に失敗 → 残りを中止",
    5: "NG: 字幕を取り込めません（字幕なし／ライブ配信の可能性）",
    6: "NG: 字幕が短すぎるか、保存済み字幕の指紋が合いません",
    7: "NG: 研究ノートが作成されませんでした",
    8: "NG: GitHub保存に失敗（PCには保存済み）",
    WAIT_MANUAL: "研究ノート待ち（手動で頼む）",
}

MANUAL_PROMPT = """あなたは「AI技術研究室」の研究ノート作成係です。インターネット検索やコマンド実行は使わないでください。

## やること
作業フォルダ「AI動画研究室」の `transcripts/` にある字幕原文OKF（`youtube-<動画ID>-transcript.md`）のうち、`research/` に同じ動画IDの研究ノート（`youtube-<動画ID>-research.md`）がまだ無いものを全部探し、1本ずつ研究ノートOKFを作って `research/` に新規保存してください。既にある研究ノートと字幕原文OKFは変更・削除しないこと。
ファイルを読み書きできない場合（チャットだけの場合）は、相棒が貼った字幕原文OKF 1本分について研究ノートを作り、保存するファイル名と中身の全文を1つのコードブロックで返してください。

## 値の写し方
次の値は、その動画の字幕原文OKFの荷札（先頭の --- から --- まで）から写す。分からないものは "UNKNOWN"。
- VIDEO_ID = 荷札の video_id
- TITLE = 荷札の title から、先頭の「【字幕原文】」と末尾の「 [動画ID]」を除いたもの
- SHA256 = 荷札の sha256 をそのまま写す（1文字でも違うと検品で不合格）
- DATE = 今日の日付（YYYY-MM-DD）
- CREATED_BY = あなたの名前（例: "ChatGPT"、"Antigravity (Gemini)"）

## 研究ノートの形式（OKF v0.2）
先頭に次の荷札（YAML）を付ける。<...> は上の値に置き換える。
```
---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "【研究ノート】<TITLE> [<VIDEO_ID>]"
description: "<200字以内の要約>"
resource: "https://www.youtube.com/watch?v=<VIDEO_ID>"
tags:
  - "AI技術研究室"
  - "動画研究"
logical_id: "youtube:<VIDEO_ID>:research"
record_id: "youtube:<VIDEO_ID>"
video_id: "<VIDEO_ID>"
created_at: "<DATE>"
created_by: "<CREATED_BY>"
source_transcript: "youtube:<VIDEO_ID>:transcript"
source_transcript_sha256: "<SHA256>"
time_source: "NONE"
related_records:
  - target_id: "youtube:<VIDEO_ID>:transcript"
    relation: "DERIVED_FROM"
    note: "本ノートの元になった字幕原文"
---
```
既存の研究ノートと内容がはっきり関係する場合だけ、related_records に次の形で追加してよい（無ければ追加しない）:
```
  - target_id: "<相手ノートの logical_id>"
    relation: "COMPLEMENTS か EXTENDS か CONTRADICTS"
    note: "<関係の説明>"
    evidence: "<この動画の字幕にある根拠の言葉（20字以内・原文のまま）>"
```

本文の見出し（この順番で）:
1. `# 【研究ノート】<TITLE> [<VIDEO_ID>]`
2. 冒頭に一文: 「本ノートは字幕原文 [[youtube-<VIDEO_ID>-transcript]] を元にした二次分析です。」
3. `## 独自要約`（300字以内）
4. `## 内容の流れ`（話の順番を5〜10項目。字幕に時刻が無いので時刻は書かない）
5. `## 重要な知見`（箇条書き。各項目の末尾に根拠となる字幕の言葉を「」で20字以内、字幕の原文のまま（空白も含めてそのまま）引用）
6. `## この研究室への応用`（AI動画の研究図書館づくりに使える点を3つまで）
7. `## 限界・未確認`（字幕に時刻が無いこと、自動生成字幕の誤変換の可能性、映像は未確認であること等）

## 守ること
- 字幕に書いていないことを足さない。推測は書かない。分からないことは UNKNOWN。
- 字幕の長い引用はしない（1か所20字以内）。
- 作成後、作ったファイル名の一覧だけを答える。
"""


def video_id(text: str) -> Optional[str]:
    """URL（通常・短縮・shorts・live・embed）または11文字の動画IDから動画IDを取り出す。"""
    text = text.strip()
    m = VIDEO_ID_RE.search(text)
    if m:
        return m.group(1)
    return text if BARE_ID_RE.match(text) else None


def parse_urls(text: str) -> List[Tuple[str, Optional[str]]]:
    """1行1URL。空行と # で始まる行は無視。同じ動画は1回だけ。動画IDが読めない行は (行, None)。"""
    seen = set()
    out: List[Tuple[str, Optional[str]]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        vid = video_id(line)
        if vid is None:
            out.append((line, None))
        elif vid not in seen:
            seen.add(vid)
            out.append((line, vid))
    return out


def vault_status(vault: Path) -> Dict[str, List[str]]:
    """保管庫の状態。waiting=研究ノート待ち（字幕だけある）、finalize=研究ノートはあるが台帳に未記録（仕上げ待ち）。"""
    import json

    tr_dir, rn_dir = vault / "transcripts", vault / "research"
    if not tr_dir.is_dir():
        return {"waiting": [], "finalize": []}
    registered = set()
    reg_path = vault / "registry.json"
    if reg_path.exists():
        try:
            rows = json.loads(reg_path.read_text(encoding="utf-8-sig"))
            if isinstance(rows, dict):
                rows = [rows]
            registered = {r.get("video_id") for r in rows if isinstance(r, dict)}
        except (OSError, ValueError):
            registered = set()
    waiting, finalize = [], []
    for f in sorted(tr_dir.glob("youtube-*-transcript.md")):
        vid = f.name[len("youtube-"):-len("-transcript.md")]
        if not (rn_dir / f"youtube-{vid}-research.md").exists():
            waiting.append(vid)
        elif vid not in registered:
            finalize.append(vid)
    return {"waiting": waiting, "finalize": finalize}


def script_args(target: str, writer: str) -> List[str]:
    return ["pwsh", "-NoProfile", "-File", str(SCRIPT), target, "-NoGitHub", "-Writer", writer]


def result_label(code: int, log: str) -> str:
    if code == 0:
        if "SKIP: 過去に研究済み" in log:
            return "研究済み（過去の台帳・スキップ）"
        if "SKIP:" in log:
            return "保存済み（スキップ）"
        if "完了: SUCCESS" in log:
            return "成功"
        return "成功（検品に要確認あり）"
    return EXIT_LABELS.get(code, f"NG: 失敗（コード {code}）")


def run_command(args: List[str], on_line: Callable[[str], None]) -> Tuple[int, str]:
    """コマンドを実行し、出力を1行ずつ on_line に渡す。(終了コード, 全出力) を返す。"""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.Popen(
        args, cwd=str(TOOLS), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", creationflags=flags,
    )
    lines = []
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip("\r\n")
        lines.append(line)
        on_line(line)
    return proc.wait(), "\n".join(lines)


def process(
    text: str,
    writer: str,
    say: Callable[[str], None],
    vault: Path = VAULT,
    runner: Callable[[List[str], Callable[[str], None]], Tuple[int, str]] = run_command,
    sleep: Callable[[float], None] = time.sleep,
) -> Dict[str, object]:
    """仕上げ待ち → 入力URL（最大10本）→ 1本でも完了があればGitHub保存（1回だけ）。"""
    results: List[Tuple[str, str]] = []
    completed = 0

    def run_one(target: str) -> Tuple[int, str]:
        nonlocal completed
        code, log = runner(script_args(target, writer), say)
        if code == 0 and "完了:" in log:
            completed += 1
        return code, log

    # 1. 手動で書かれた研究ノートの仕上げ（検品・台帳・目次）
    pending = vault_status(vault)["finalize"]
    for vid in pending:
        say(f"===== 仕上げ: {vid}（手動で書いた研究ノート） =====")
        code, log = run_one(vid)
        results.append((vid, "仕上げ " + result_label(code, log)))

    # 2. 入力された動画
    targets = parse_urls(text)
    if len(targets) > MAX_VIDEOS:
        say(f"上限 {MAX_VIDEOS} 本を超えているため、先頭 {MAX_VIDEOS} 本だけ処理します（残り {len(targets) - MAX_VIDEOS} 本は次回）")
        targets = targets[:MAX_VIDEOS]
    abort = False
    for i, (url, vid) in enumerate(targets, 1):
        if vid is None:
            results.append((url, EXIT_LABELS[2]))
            continue
        if abort:
            results.append((vid, "中止（前の失敗が原因）"))
            continue
        say(f"===== [{i}/{len(targets)}] {vid} =====")
        code, log = run_one(url)
        results.append((vid, result_label(code, log)))
        if code in ABORT_CODES:
            abort = True
        elif i < len(targets) and "SKIP:" not in log:
            sleep(WAIT_SEC)

    # 3. GitHubへ保存（研究ノートと台帳だけ。字幕原文は publish_to_github.ps1 のガードで送らない）
    published = None
    if completed:
        say("===== GitHubへ保存 =====")
        code, _ = runner(["pwsh", "-NoProfile", "-File", str(PUBLISH)], say)
        published = code == 0
        if not published:
            say(f"WARN: GitHub保存に失敗（コード {code}）。PCとドライブには保存済み")

    status = vault_status(vault)
    say("=============== まとめ ===============")
    for name, label in results:
        say(f"{name:<14} {label}")
    if not results:
        say("処理する動画はありませんでした")
    say(f"研究ノート待ち: {len(status['waiting'])} 本")
    return {"results": results, "published": published, "waiting": status["waiting"]}


def _legacy_main() -> None:
    import tkinter as tk
    from tkinter import scrolledtext

    root = tk.Tk()
    root.title("AI技術研究室・字幕保存スイッチ")
    root.geometry("760x620")
    lines: "queue.Queue[str]" = queue.Queue()

    tk.Label(root, text="YouTubeのURLを1行に1本ずつ貼ってください（最大10本）", anchor="w").pack(fill="x", padx=10, pady=(10, 2))
    url_box = tk.Text(root, height=6)
    url_box.pack(fill="x", padx=10)

    buttons = tk.Frame(root)
    buttons.pack(fill="x", padx=10, pady=8)
    status = tk.Label(root, text="", anchor="w", fg="#555")
    status.pack(fill="x", padx=10)
    log_box = scrolledtext.ScrolledText(root, height=20, state="disabled")
    log_box.pack(fill="both", expand=True, padx=10, pady=(4, 10))

    def say(msg: str) -> None:
        lines.put(msg)

    def write_log_file(msg: str) -> None:
        try:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
        except OSError:
            pass

    def drain() -> None:
        while not lines.empty():
            msg = lines.get()
            write_log_file(msg)
            log_box.configure(state="normal")
            log_box.insert("end", msg + "\n")
            log_box.see("end")
            log_box.configure(state="disabled")
        root.after(200, drain)

    def refresh_status(extra: str = "") -> None:
        s = vault_status(VAULT)
        text = f"研究ノート待ち: {len(s['waiting'])} 本 ／ 仕上げ待ち: {len(s['finalize'])} 本"
        status.configure(text=f"{text}　{extra}".rstrip())

    def start(writer: str) -> None:
        text = url_box.get("1.0", "end")
        for b in (full_btn, manual_btn):
            b.configure(state="disabled")

        def work() -> None:
            try:
                process(text, writer, say)
            except Exception as e:  # 画面が固まらないよう、想定外の失敗も表示して止める
                say(f"STOP: 想定外のエラー: {e}")
            finally:
                root.after(0, finish)

        threading.Thread(target=work, daemon=True).start()

    def finish() -> None:
        for b in (full_btn, manual_btn):
            b.configure(state="normal")
        url_box.delete("1.0", "end")
        refresh_status()

    def copy_prompt() -> None:
        root.clipboard_clear()
        root.clipboard_append(MANUAL_PROMPT)
        root.update()
        refresh_status("← 手動用の指示文をコピーしました")

    full_btn = tk.Button(buttons, text="① Claudeで最後まで", width=22, command=lambda: start("claude"))
    manual_btn = tk.Button(buttons, text="② 字幕OKFまでで止める", width=22, command=lambda: start("manual"))
    copy_btn = tk.Button(buttons, text="手動用の指示文をコピー", width=22, command=copy_prompt)
    full_btn.pack(side="left")
    manual_btn.pack(side="left", padx=8)
    copy_btn.pack(side="right")

    refresh_status()
    drain()
    root.mainloop()


if __name__ == "__main__":
    from switch_app import main as launch
    launch(sys.argv[1] if len(sys.argv) > 1 else TOOLS / "config.local.json")
