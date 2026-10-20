#!/usr/bin/env python3
"""質問回答の一括実行（相棒PC側で実行する想定）。

qa_check.py の plan（研究ノート1本につき3問、実データで93問）を Notebook に順に質問し、
各回答を qa_check の判定（check_answer）にかけて PASS / PARTIAL / FAIL の件数と動画別の一覧を出す。

安全の作り:
- 既定は dry-run：質問と「実行予定のコマンド」を並べるだけで、Notebookには1回も接続しない。
- 実行は `--live --notebook-id <ID> --out-dir <出力先>` の3つが必須。
- 呼べるコマンドは allowlist（ログイン点検・質問・ソース一覧）だけ。add / delete / login / refresh など書き込み系や
  ログイン系は、コマンドの形を組み立てる段階で拒否する（DisallowedCommand）。
- ログイン切れは検知したら書き込み0のまま即停止（AUTH_EXPIRED、終了コード3）。再ログインはしない。
- 回答は repo に保存しない（字幕全文が混ざりうるため）。`--out-dir` が repo の中なら拒否する。
- 質問プランは研究ノートと台帳から作る（qa_check.plan_for_videos）。字幕全文は使わない。

UNVERIFIED: `notebooklm ask` の引数・出力の形は実CLIで未確認。`NotebookLmCliAskClient.COMMANDS` と
`parse_ask_output` の2か所だけに集約してあり、実機で `notebooklm ask --help` を見て直せば足りる。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple

AUTO_DIR = Path(__file__).resolve().parent
ROOT = AUTO_DIR.parents[1]
if str(AUTO_DIR) not in sys.path:
    sys.path.insert(0, str(AUTO_DIR))

import qa_check  # noqa: E402

PASS, PARTIAL, FAIL = qa_check.PASS, qa_check.PARTIAL, qa_check.FAIL
ERROR = "ERROR"                       # 質問そのものが失敗した（判定できていない）
MAX_CONSECUTIVE_ERRORS = 3            # 質問の失敗がこの回数続いたら止める（ログイン切れ以外の原因）


class AuthExpired(RuntimeError):
    """Notebookのログインが切れている。再ログインは相棒の手でしかしない。"""


class DisallowedCommand(RuntimeError):
    """allowlist にないコマンドを組み立てようとした。"""


class AskError(RuntimeError):
    """1問の質問が失敗した（ログイン切れ以外）。"""


class AskClient(Protocol):
    """Notebookへの質問の差し替え口。書き込み系のメソッドは意図的に持たない。"""

    def auth_check_passive(self) -> bool: ...

    def ask(self, question: str) -> str: ...


# ---------------------------------------------------------------------------
# CLI アダプタ


# 呼んでよいコマンドの先頭部分（argv の前方一致）。ここに無い形は _run が拒否する。
COMMAND_ALLOWLIST: Tuple[Tuple[str, ...], ...] = (
    ("notebooklm", "auth", "check"),
    ("notebooklm", "ask"),
    ("notebooklm", "source", "list"),
)
# allowlist とは別の二重の防御：サブコマンドにこれらが含まれる形は、allowlist に誤って足されても拒否する。
FORBIDDEN_WORDS = frozenset({
    "add", "delete", "remove", "rename", "create", "update", "upload", "import", "login", "logout",
    "refresh", "clear", "reset", "share", "publish", "write", "set",
})


class NotebookLmCliAskClient:
    """notebooklm CLI の ask 系コマンドを subprocess で呼ぶ実機用アダプタ。

    UNVERIFIED：`ask` の引数・出力は notebooklm-py の実CLIで未確認（2026-10-20 時点）。実機で
    `notebooklm ask --help` を見て、COMMANDS の "ask" と parse_ask_output を直すだけにしてある。
    auth_check_passive は notebooklm_py_ingest.NotebookLmCliClient と同じ形（実機で動作確認済み）。
    """

    COMMANDS = {
        "auth_check_passive": ["notebooklm", "auth", "check", "--test", "--passive"],
        "ask": ["notebooklm", "ask", "{question}", "--json", "--notebook", "{notebook_id}"],   # UNVERIFIED
        "list_sources": ["notebooklm", "source", "list", "--json", "--notebook", "{notebook_id}"],
    }

    def __init__(self, notebook_id: str, timeout: int = 120, ask_timeout: int = 300):
        if not notebook_id:
            raise ValueError("notebook_id is required")
        self.notebook_id = notebook_id
        self.timeout = timeout
        self.ask_timeout = ask_timeout

    def build_args(self, key: str, **fmt: str) -> List[str]:
        args = [a.format(notebook_id=self.notebook_id, **fmt) for a in self.COMMANDS[key]]
        ensure_allowed(args)
        return args

    def _run(self, key: str, timeout: Optional[int] = None, **fmt: str) -> subprocess.CompletedProcess:
        args = self.build_args(key, **fmt)
        return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=timeout or self.timeout)

    def auth_check_passive(self) -> bool:
        try:
            return self._run("auth_check_passive").returncode == 0
        except DisallowedCommand:
            raise
        except Exception:
            return False

    def ask(self, question: str) -> str:
        if question.lstrip().startswith("-"):
            raise AskError("質問文が - で始まるため、コマンドの引数と取り違えられる")
        try:
            cp = self._run("ask", timeout=self.ask_timeout, question=question)
        except subprocess.TimeoutExpired as e:
            raise AskError("ask がタイムアウトした") from e
        if cp.returncode != 0:
            # 失敗の理由がログイン切れかどうかは、呼び出し側が auth_check_passive で確かめる
            raise AskError(f"ask failed (rc={cp.returncode})")
        return parse_ask_output(cp.stdout)


def ensure_allowed(args: Sequence[str]) -> None:
    """argv が allowlist の形で、書き込み系・ログイン系の語を含まないことを確かめる。違えば DisallowedCommand。"""
    argv = list(args)
    if not any(tuple(argv[: len(p)]) == p for p in COMMAND_ALLOWLIST):
        raise DisallowedCommand(f"allowlist にないコマンド: {' '.join(argv[:3])}")
    prefix_len = max(len(p) for p in COMMAND_ALLOWLIST if tuple(argv[: len(p)]) == p)
    # allowlist の先頭部分のすぐ後ろ（質問文や値の前）にある語だけを見る。質問文そのものは対象外。
    words = {w for w in argv[1:prefix_len]}
    bad = words & FORBIDDEN_WORDS
    if bad:
        raise DisallowedCommand(f"書き込み系・ログイン系の語を含むコマンド: {', '.join(sorted(bad))}")


def parse_ask_output(stdout: str) -> str:
    """ask の標準出力から回答テキストを取り出す。UNVERIFIED：JSONなら answer / response / text / content、他は全文。"""
    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return stdout or ""
    if isinstance(data, dict):
        for key in ("answer", "response", "text", "content", "output"):
            if isinstance(data.get(key), str):
                return data[key]
        return stdout
    return data if isinstance(data, str) else stdout


# ---------------------------------------------------------------------------
# 出力先の検査


def check_out_dir(out_dir: Path, root: Path = ROOT) -> Path:
    """回答の保存先を検査して絶対パスで返す。repo の中なら ValueError（字幕全文の混入を避けるため）。"""
    p = Path(out_dir).expanduser().resolve()
    r = Path(root).resolve()
    if p == r or r in p.parents:
        raise ValueError(f"回答の保存先が repo の中: {p}（repo の外を指定してください。例: /tmp/qa_answers）")
    return p


# ---------------------------------------------------------------------------
# 計画・dry-run


def select_questions(plan: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    qs = list(plan["questions"])
    return qs[:limit] if limit is not None and limit >= 0 else qs


def dry_run(plan: Dict[str, Any], notebook_id: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    """質問と実行予定のコマンドを並べるだけ。Notebookには接続しない（クライアントも作らない）。"""
    nb = notebook_id or "<notebook_id>"
    template = NotebookLmCliAskClient.COMMANDS["ask"]
    items = []
    for q in select_questions(plan, limit):
        args = [a.format(notebook_id=nb, question=q["question"]) for a in template]
        ensure_allowed(args)
        items.append({"question_id": q["id"], "video_id": q["video_id"], "kind": q["kind"],
                      "question": q["question"], "command": args})
    return {
        "status": "DRY_RUN",
        "connections": 0,
        "files_modified": False,
        "question_count": len(items),
        "plan_question_count": plan["question_count"],
        "allowed_commands": [" ".join(p) for p in COMMAND_ALLOWLIST],
        "unverified": "ask の引数と出力の形は実CLIで未確認（NotebookLmCliAskClient.COMMANDS['ask']）",
        "items": items,
    }


# ---------------------------------------------------------------------------
# 実行（クライアントは差し替え可能）


def run_questions(
    plan: Dict[str, Any],
    videos: Dict[str, Dict[str, Any]],
    client: AskClient,
    out_dir: Path,
    limit: Optional[int] = None,
    root: Path = ROOT,
) -> Dict[str, Any]:
    """質問を順に投げて判定し、集計を返す。回答は out_dir に1問1ファイルで保存する（repo の中は拒否）。"""
    out = check_out_dir(out_dir, root)
    questions = select_questions(plan, limit)
    if not client.auth_check_passive():
        return _auth_expired([], len(questions), 0)
    out.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    consecutive_errors = 0
    for q in questions:
        try:
            answer = client.ask(q["question"])
        except AuthExpired:
            return _auth_expired(results, len(questions), len(results))
        except AskError as e:
            # 失敗の理由がログイン切れなら止める。そうでなければこの問を ERROR にして続ける
            if not client.auth_check_passive():
                return _auth_expired(results, len(questions), len(results))
            consecutive_errors += 1
            results.append({"question_id": q["id"], "video_id": q["video_id"], "kind": q["kind"], "verdict": ERROR,
                            "reasons": [{"check": "-", "level": ERROR, "message": str(e)}]})
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                return summarize(results, len(questions), "ABORTED_TOO_MANY_ERRORS", out)
            continue
        consecutive_errors = 0
        (out / f"{q['id']}.txt").write_text(answer or "", encoding="utf-8")
        res = qa_check.check_answer(answer or "", q, videos)
        results.append({"question_id": q["id"], "video_id": q["video_id"], "kind": q["kind"],
                        "verdict": res["verdict"], "checks": res["checks"], "reasons": res["reasons"]})
    return summarize(results, len(questions), "DONE", out)


def _auth_expired(results: List[Dict[str, Any]], asked_total: int, done: int) -> Dict[str, Any]:
    rep = summarize(results, asked_total, "AUTH_EXPIRED", None)
    rep["user_action"] = "相棒のPCでNotebookLMにログインし直してから、もう一度実行してください（このツールは再ログインしない）。"
    rep["notebook_writes"] = 0
    return rep


def summarize(results: List[Dict[str, Any]], planned: int, status: str, out_dir: Optional[Path]) -> Dict[str, Any]:
    counts = {k: sum(1 for r in results if r["verdict"] == k) for k in (PASS, PARTIAL, FAIL, ERROR)}
    by_video: Dict[str, Dict[str, Any]] = {}
    for r in results:
        d = by_video.setdefault(r["video_id"], {"questions": {}, PASS: 0, PARTIAL: 0, FAIL: 0, ERROR: 0})
        d["questions"][r["question_id"]] = r["verdict"]
        d[r["verdict"]] += 1
    return {
        "status": status,
        "planned": planned,
        "asked": len(results),
        "counts": counts,
        "by_video": by_video,
        "not_pass": [{"question_id": r["question_id"], "verdict": r["verdict"],
                      "reason": (r["reasons"][0]["message"] if r.get("reasons") else "")}
                     for r in results if r["verdict"] != PASS],
        "answers_dir": str(out_dir) if out_dir else None,
        "notebook_writes": 0,
        "repo_files_modified": False,
    }


def format_summary(rep: Dict[str, Any]) -> str:
    c = rep["counts"]
    lines = [f"【質問回答の一括実行】{rep['status']}  質問 {rep['asked']}/{rep['planned']}問  "
             f"PASS {c[PASS]} / PARTIAL {c[PARTIAL]} / FAIL {c[FAIL]} / ERROR {c[ERROR]}"]
    if rep.get("user_action"):
        lines.append(f"要対応: {rep['user_action']}")
    for vid, d in rep["by_video"].items():
        marks = " ".join(f"{qid.rsplit('-', 1)[-1]}={v}" for qid, v in d["questions"].items())
        lines.append(f"  {vid}  {marks}")
    for n in rep["not_pass"]:
        lines.append(f"  - {n['question_id']} {n['verdict']}: {n['reason']}")
    if rep.get("answers_dir"):
        lines.append(f"回答の保存先（repoの外）: {rep['answers_dir']}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="質問回答の一括実行（既定はdry-run。Notebookには書き込まない）")
    ap.add_argument("--live", action="store_true", help="実際にNotebookへ質問する（--notebook-id と --out-dir が必須）")
    ap.add_argument("--notebook-id", help="Notebook ID（--live で必須）")
    ap.add_argument("--out-dir", type=Path, help="回答の保存先。repo の外（例: /tmp/qa_answers）。--live で必須")
    ap.add_argument("--video-id", help="この動画の質問だけに絞る")
    ap.add_argument("--limit", type=int, help="先頭からこの問数だけ（まず数問で試す用）")
    ap.add_argument("--summary", action="store_true", help="JSONではなく人が読める形で出す")
    args = ap.parse_args(argv)

    videos = qa_check.load_videos(ROOT)
    try:
        plan = qa_check.plan_for_videos(videos, args.video_id)
    except KeyError as e:
        print(str(e), file=sys.stderr)
        return 2
    if args.out_dir is not None:
        try:
            check_out_dir(args.out_dir, ROOT)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2

    if not args.live:
        rep = dry_run(plan, args.notebook_id, args.limit)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0
    if not args.notebook_id or args.out_dir is None:
        print("--live には --notebook-id と --out-dir が必須です", file=sys.stderr)
        return 2
    rep = run_questions(plan, videos, NotebookLmCliAskClient(args.notebook_id), args.out_dir, args.limit)
    print(format_summary(rep), end="") if args.summary else print(json.dumps(rep, ensure_ascii=False, indent=2))
    if rep["status"] == "AUTH_EXPIRED":
        return 3
    return 0 if rep["status"] == "DONE" and rep["counts"][PASS] == rep["asked"] else 1


if __name__ == "__main__":
    sys.exit(main())
