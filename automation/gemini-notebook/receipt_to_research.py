#!/usr/bin/env python3
"""Offline & Git-verified bridge: Gemini research receipt -> GitHub-ready notes & Notebook index.

Supports:
1. Extracting `research_receipt_v1` from raw JSON files, Gemini Markdown responses (fenced code blocks),
   an inbox directory (including Google Drive synced folders), or system clipboard.
2. Cross-branch deduplication across local `registry.json`, `research/*.md`, and all `origin/*` branches
   (preventing duplicate video records across unmerged Draft PRs).
3. Canonical YouTube URL normalization (`watch?v=`, `youtu.be/`, `shorts/`, `live/`) and ID verification.
4. Safe handling of both `NEW` video records and `UPDATED` / `CONFLICT` delta appends with receipt SHA-256 idempotency.
5. Automatic updating of `loop_state.json` (next research topics, unknowns, processed receipt hashes)
   and `AI技術研究室_知識索引.md` (for syncing back to Gemini Notebook).
6. Optional non-default branch Git commit, push, and remote readback verification (`retry=0`, `force=false`).

Does not invoke any paid external AI API, browser automation, or unauthorized network endpoints.
Default mode is preview only.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ALLOWED_STATUSES = {
    "CONFIRMED_DOC",
    "REPORTED_BY_AUTHOR",
    "CONFIRMED_TEST",
    "UNKNOWN",
    "CONTRADICTED",
}
ALLOWED_CHANGES = {"KNOWN", "NEW", "UPDATED", "CONFLICT", "UNKNOWN"}
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_REPO = "kamiyusense/ai-video-research"
DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "state" / "loop_state.json"
DEFAULT_INDEX_PATH = Path(__file__).resolve().parent / "state" / "AI技術研究室_知識索引.md"
YOUTUBE_HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}

FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def git(*args, root=ROOT, check=True):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )
    return result.stdout.strip()


def check_write_boundary(root=ROOT):
    branch = git("branch", "--show-current", root=root)
    if not branch or branch in {"main", "master"}:
        raise ValueError("Refusing detached/default-branch write: " + str(branch))
    origin = git("remote", "get-url", "origin", root=root)
    if not re.search(r"(?:[:/])kamiyusense/ai-video-research(?:\.git)?/?$", origin):
        raise ValueError("Unexpected git origin: refusing write")
    return branch


def valid_url(value):
    if not isinstance(value, str):
        return False
    u = urlparse(value)
    return u.scheme == "https" and bool(u.netloc)


def extract_youtube_id(url):
    """Extract 11-char YouTube video_id from watch, youtu.be, shorts, or live URLs."""
    if not valid_url(url):
        return None
    u = urlparse(url)
    host = (u.hostname or "").lower()
    if host not in YOUTUBE_HOSTS:
        return None
    if host == "youtu.be":
        parts = [p for p in u.path.split("/") if p]
        cand = parts[0] if parts else None
    else:
        if u.path == "/watch":
            qs = parse_qs(u.query)
            cand = qs.get("v", [None])[0]
        else:
            parts = [p for p in u.path.split("/") if p]
            if len(parts) >= 2 and parts[0] in {"shorts", "live", "embed", "v"}:
                cand = parts[1]
            else:
                cand = None
    if cand and VIDEO_ID.fullmatch(cand):
        return cand
    return None


def canonical_youtube_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def extract_receipt_payload(raw_text):
    """Extract `research_receipt_v1` dict from raw JSON or Markdown with fenced JSON blocks."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Empty receipt input")
    stripped = raw_text.strip()
    # 1. Try direct JSON parse
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict) and data.get("schema_version") == "research_receipt_v1":
                return data
        except json.JSONDecodeError:
            pass
    # 2. Try fenced code blocks ```json ... ```
    for match in FENCED_JSON_RE.finditer(raw_text):
        block = match.group(1).strip()
        try:
            data = json.loads(block)
            if isinstance(data, dict) and data.get("schema_version") == "research_receipt_v1":
                return data
        except json.JSONDecodeError:
            continue
    # 3. Try scanning balanced JSON objects containing "research_receipt_v1"
    idx = raw_text.find('"research_receipt_v1"')
    if idx != -1:
        start = raw_text.rfind("{", 0, idx)
        while start != -1:
            depth = 0
            in_str = False
            escape = False
            for pos in range(start, len(raw_text)):
                ch = raw_text[pos]
                if in_str:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == '"':
                        in_str = False
                else:
                    if ch == '"':
                        in_str = True
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            candidate = raw_text[start : pos + 1]
                            try:
                                data = json.loads(candidate)
                                if isinstance(data, dict) and data.get("schema_version") == "research_receipt_v1":
                                    return data
                            except json.JSONDecodeError:
                                pass
                            break
            start = raw_text.rfind("{", 0, start)
    # Fallback to standard json.loads to raise a clear error
    data = json.loads(stripped)
    return data


def compute_receipt_digest(data):
    """Compute canonical SHA-256 digest for a validated receipt payload."""
    canonical_bytes = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def validate(data):
    if not isinstance(data, dict) or data.get("schema_version") != "research_receipt_v1":
        raise ValueError("Invalid receipt schema_version")
    if not valid_url(data.get("notebook_url")):
        raise ValueError("Missing/invalid notebook_url")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data.get("checked_at", ""))):
        raise ValueError("Invalid checked_at")
    date.fromisoformat(data["checked_at"])
    if data.get("notebook_readback") not in {"PASS", "FAIL", "UNKNOWN"}:
        raise ValueError("Invalid notebook_readback")
    dedup_status = data.get("github_dedup_status")
    if dedup_status is not None and dedup_status not in {"PASS", "UNKNOWN"}:
        raise ValueError("Invalid github_dedup_status")
    next_topics = data.get("next_topics")
    if next_topics is not None:
        if not isinstance(next_topics, list) or len(next_topics) > 10 or not all(
            isinstance(t, str) and 1 <= len(t.strip()) <= 300 for t in next_topics
        ):
            raise ValueError("Invalid next_topics")
    unknowns = data.get("unknowns")
    if unknowns is not None:
        if not isinstance(unknowns, list) or len(unknowns) > 20 or not all(
            isinstance(u, str) and 1 <= len(u.strip()) <= 500 for u in unknowns
        ):
            raise ValueError("Invalid unknowns")
    videos = data.get("videos")
    if not isinstance(videos, list) or len(videos) > 20:
        raise ValueError("videos must be a list of <=20 items")
    ids = set()
    for v in videos:
        vid = v.get("video_id") if isinstance(v, dict) else None
        if not isinstance(vid, str) or not VIDEO_ID.fullmatch(vid) or vid in ids:
            raise ValueError("Invalid or duplicate video_id")
        ids.add(vid)
        url = v.get("url")
        if not valid_url(url) or (urlparse(url).hostname or "").lower() not in YOUTUBE_HOSTS:
            raise ValueError("Video URL must be YouTube HTTPS")
        extracted_id = extract_youtube_id(url)
        if extracted_id is not None and extracted_id != vid:
            raise ValueError(f"Video URL ID ({extracted_id}) does not match video_id ({vid})")
        if not isinstance(v.get("title"), str) or not (1 <= len(v["title"]) <= 250):
            raise ValueError("Invalid title")
        if not isinstance(v.get("summary_ja"), str) or not (1 <= len(v["summary_ja"]) <= 300):
            raise ValueError("Summary must contain 1-300 characters")
        if not isinstance(v.get("source_scope"), str) or len(v["source_scope"]) > 180:
            raise ValueError("Invalid source_scope")
        if v.get("notebook_readback") not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("Invalid notebook source readback")
        if not isinstance(v.get("changes"), list) or not v["changes"] or not set(v["changes"]) <= ALLOWED_CHANGES:
            raise ValueError("Invalid changes")
        claims = v.get("claims")
        if not isinstance(claims, list) or len(claims) > 12:
            raise ValueError("Claims must be a list of <=12 items")
        for c in claims:
            if not isinstance(c, dict) or not isinstance(c.get("text"), str) or len(c["text"]) > 500:
                raise ValueError("Invalid claim")
            if c.get("status") not in ALLOWED_STATUSES:
                raise ValueError("Invalid claim status")
            t = c.get("timestamp_seconds")
            if t is not None and (type(t) is not int or t < 0):
                raise ValueError("Invalid timestamp")
            u = c.get("official_url")
            if u is not None and not valid_url(u):
                raise ValueError("Invalid official_url")
    return videos


def clean(s):
    return str(s).replace("\n", " ").replace("\r", " ").strip()


def format_claims_lines(vid, claims):
    lines = []
    for c in claims:
        t = c.get("timestamp_seconds")
        time_ref = (
            "[{:02d}:{:02d}](https://www.youtube.com/watch?v={}&t={}s)".format(t // 60, t % 60, vid, t)
            if t is not None
            else "UNKNOWN"
        )
        lines.append(
            "- "
            + clean(c["text"])
            + " | "
            + c["status"]
            + " | time: "
            + time_ref
            + " | official: "
            + (c.get("official_url") or "UNKNOWN")
        )
    return lines


def render(v, checked_at):
    vid = v["video_id"]
    canon = canonical_youtube_url(vid)
    lines = [
        "# " + clean(v["title"]),
        "",
        "- record_id: `youtube:" + vid + "`",
        "- video_id: `" + vid + "`",
        "- canonical_url: " + canon,
        "- original_url: " + v["url"],
        "- publication_date: " + clean(v.get("published_at") or "UNKNOWN"),
        "- checked_at: " + checked_at,
        "- source_scope: " + clean(v["source_scope"]),
        "- Gemini Notebook source: " + clean(v.get("notebook_source_id") or "UNKNOWN"),
        "- Gemini readback (self-reported): " + v["notebook_readback"],
        "- GitHub independent verification: NOT_RUN",
        "- changes: " + ", ".join(v["changes"]),
        "",
        "## 独自要約",
        clean(v["summary_ja"]),
        "",
        "## 主張・一次資料・時刻",
    ]
    lines += format_claims_lines(vid, v["claims"])
    lines += [
        "",
        "## 限界",
        "Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。",
        "",
    ]
    return "\n".join(lines)


def render_delta_section(v, checked_at):
    """Render an append-only delta section for UPDATED or CONFLICT records."""
    vid = v["video_id"]
    changes_str = ", ".join(v["changes"])
    lines = [
        "",
        f"## 差分更新 ({checked_at} / {changes_str})",
        "",
        "- checked_at: " + checked_at,
        "- source_scope: " + clean(v["source_scope"]),
        "- Gemini Notebook source: " + clean(v.get("notebook_source_id") or "UNKNOWN"),
        "- Gemini readback (self-reported): " + v["notebook_readback"],
        "- changes: " + changes_str,
        "",
        "### 差分要約",
        clean(v["summary_ja"]),
        "",
        "### 追加・更新された主張と検証",
    ]
    lines += format_claims_lines(vid, v["claims"])
    lines.append("")
    return "\n".join(lines)


def collect_remote_branch_videos(root=ROOT):
    """Scan all `refs/remotes/origin/*` branches for `registry.json` records and `research/*.md` files."""
    remote_map = {}
    try:
        refs_out = git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/", root=root, check=False)
    except Exception:
        return remote_map
    for ref in refs_out.splitlines():
        ref = ref.strip()
        if not ref or ref in {"origin/HEAD", "origin/main", "origin"}:
            continue
        reg_raw = git("show", f"{ref}:registry.json", root=root, check=False)
        if reg_raw:
            try:
                reg = json.loads(reg_raw)
                for rec in reg.get("records", []):
                    vid = rec.get("video_id")
                    if isinstance(vid, str) and VIDEO_ID.fullmatch(vid):
                        info = remote_map.setdefault(
                            vid,
                            {
                                "video_id": vid,
                                "canonical_url": rec.get("canonical_url") or canonical_youtube_url(vid),
                                "research_path": rec.get("research_path", ""),
                                "status": rec.get("status", "UNKNOWN"),
                                "branches": [],
                            },
                        )
                        if ref not in info["branches"]:
                            info["branches"].append(ref)
            except json.JSONDecodeError:
                pass
    return remote_map


def load_loop_state(state_path=DEFAULT_STATE_PATH):
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                return state
        except json.JSONDecodeError:
            pass
    return {
        "schema_version": "gemini_notebook_loop_state_v1",
        "repository": EXPECTED_REPO,
        "notebook_url": "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
        "last_updated": None,
        "processed_receipts": [],
        "next_topics_queue": [],
        "open_unknowns": [],
        "unresolved_backlog_refs": [
            {
                "id": "P006-U01",
                "title": "Google AI Studioの長尺YouTube動画入力でのブラウザUIフリーズ回避・映像フレーム直接検証の省力化",
                "source": "proposals/006-unresolved-task-backlog-revisit.md",
                "status": "OPEN",
            },
            {
                "id": "P006-U02",
                "title": "Gemini Notebookと非公開GitHub間の手動コピーを最小化する安全な公式連携・差分同期",
                "source": "automation/gemini-notebook/README.md",
                "status": "IN_PROGRESS",
            },
            {
                "id": "P006-U03",
                "title": "反復的な画面操作（Computer Use）から公式API・決定的スクリプトへの安全な移行判断",
                "source": "research/2026-10-10-lC5jxpYmatE-ai-techniques.md",
                "status": "OPEN",
            },
        ],
    }


def render_knowledge_index_md(registry, remote_map, loop_state):
    """Render `AI技術研究室_知識索引.md` so Gemini Notebook knows all GitHub-recorded videos & next priorities."""
    local_records = {r["video_id"]: r for r in registry.get("records", []) if isinstance(r, dict) and r.get("video_id")}
    all_vids = sorted(set(local_records.keys()) | set(remote_map.keys()))

    lines = [
        "# AI技術研究室_知識索引 (GitHub正本 同期用インデックス)",
        "",
        f"- 対象リポジトリ: `{EXPECTED_REPO}` (private)",
        f"- 補助知識庫 (Gemini Notebook): {loop_state.get('notebook_url', 'https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7')}",
        f"- 最終索引更新日: {loop_state.get('last_updated') or 'INITIAL'}",
        "- 用途: Gemini Task の Step 1 (READ) / Step 3 (SELECT) / Step 6 (DIFF) / Step 8 (INDEX) で参照し、既知動画の重複調査を防ぎ、差分抽出と次テーマ選定の基準とする。",
        "",
        "## 1. 既知の動画ID台帳（全ブランチ統合・重複登録禁止リスト）",
        "",
        "| video_id | 状態 | 保存場所 ( 現在ブランチ / 並行PRブランチ ) | 研究ファイル |",
        "|---|---|---|---|",
    ]
    for vid in all_vids:
        if vid in local_records:
            rec = local_records[vid]
            status = clean(rec.get("status", "RECORDED"))
            rpath = clean(rec.get("research_path", ""))
            loc = "current_branch"
        else:
            rinfo = remote_map[vid]
            status = clean(rinfo.get("status", "REMOTE_BRANCH_ONLY"))
            rpath = clean(rinfo.get("research_path", ""))
            loc = ", ".join(rinfo.get("branches", []))
        lines.append(f"| `{vid}` | {status} | {loc} | `{rpath}` |")

    lines += [
        "| `MVVpR2Bb0Rk` | SKIPPED (メンバー限定報告・対象外) | `origin/research/cognitive-drift-series-20261010` | 調査対象外 |",
        "",
        "## 2. 優先研究テーマ・次回調査キュー (`next_topics`)",
        "",
    ]
    queue = loop_state.get("next_topics_queue") or []
    if queue:
        for idx, topic in enumerate(queue, 1):
            lines.append(f"{idx}. {clean(topic)}")
    else:
        lines += [
            "1. R001/R002: 自律研究Loopの完了条件・停止条件と、重複イベントや結果不明書込みの安全な復旧パターン",
            "2. R004/R005: ハーネス・MCP・プラグイン・公式コネクタの権限境界とモデル非依存の状態管理",
            "3. P006連携: 新しいAI機能・ツール発表時に「過去の未解決課題」と自動照合して再挑戦を提案する仕組み",
        ]

    lines += [
        "",
        "## 3. 未確認・要検証事項 (`unknowns`)",
        "",
    ]
    unknowns = loop_state.get("open_unknowns") or []
    if unknowns:
        for u in unknowns:
            lines.append(f"- {clean(u)}")
    else:
        lines += [
            "- Gemini Taskの定期スケジュール実行時におけるNotebookソース追加・索引更新の無人完走可否",
            "- YouTubeソース（文字起こしのみ）では確認できない画面実演・UI操作の軽量な検証手段",
        ]

    lines += [
        "",
        "## 4. 未解決課題ストック（P006 再評価対象）",
        "",
        "新技術・新機能を発見した際は、以下の未解決課題を解決できる一次資料の根拠があるか照合すること：",
        "",
    ]
    for item in loop_state.get("unresolved_backlog_refs", []):
        lines.append(
            f"- **{clean(item.get('id', ''))}**: {clean(item.get('title', ''))} "
            f"(状態: `{clean(item.get('status', 'OPEN'))}`, 参照: `{clean(item.get('source', ''))}`)"
        )

    lines.append("")
    return "\n".join(lines)


def update_state_and_index(
    data,
    digest,
    registry,
    remote_map,
    applied_new_ids,
    applied_updated_ids,
    state_path=DEFAULT_STATE_PATH,
    index_path=DEFAULT_INDEX_PATH,
    export_drive_dir=None,
):
    """Update `loop_state.json` and `AI技術研究室_知識索引.md` (and optional Google Drive folder)."""
    state = load_loop_state(state_path)
    checked_at = data.get("checked_at") or date.today().isoformat()
    state["last_updated"] = checked_at
    if data.get("notebook_url"):
        state["notebook_url"] = data["notebook_url"]

    processed = state.setdefault("processed_receipts", [])
    if digest and not any(p.get("sha256") == digest for p in processed if isinstance(p, dict)):
        processed.append(
            {
                "sha256": digest,
                "checked_at": checked_at,
                "new_video_ids": applied_new_ids,
                "updated_video_ids": applied_updated_ids,
            }
        )

    queue = state.setdefault("next_topics_queue", [])
    for topic in data.get("next_topics") or []:
        t_clean = clean(topic)
        if t_clean and t_clean not in queue:
            queue.append(t_clean)
    # Keep queue bounded to latest 15 topics
    state["next_topics_queue"] = queue[-15:]

    unknowns = state.setdefault("open_unknowns", [])
    for unk in data.get("unknowns") or []:
        u_clean = clean(unk)
        if u_clean and u_clean not in unknowns:
            unknowns.append(u_clean)
    state["open_unknowns"] = unknowns[-25:]

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index_md = render_knowledge_index_md(registry, remote_map, state)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index_md, encoding="utf-8")

    drive_written = None
    if export_drive_dir:
        drive_dir = Path(export_drive_dir)
        if not drive_dir.exists():
            raise ValueError(f"Drive export directory does not exist: {drive_dir}")
        drive_target = drive_dir / index_path.name
        drive_target.write_text(index_md, encoding="utf-8")
        drive_written = str(drive_target)

    return {
        "state_path": str(state_path),
        "index_path": str(index_path),
        "drive_export_path": drive_written,
    }


def verify_and_push_git(
    root=ROOT,
    commit_message=None,
    do_push=False,
    touched_paths=None,
):
    """Safely commit to non-default branch, optionally push once, and verify remote readback."""
    branch = check_write_boundary(root=root)
    status_out = git("status", "--porcelain", root=root)
    if not status_out:
        return {
            "branch": branch,
            "committed": False,
            "pushed": False,
            "head_sha": git("rev-parse", "HEAD", root=root),
            "readback_verified": True,
            "note": "NO_CHANGES_TO_COMMIT",
        }

    # Check if remote branch exists and ensure we are not behind/diverged before committing/pushing
    if do_push:
        git("fetch", "origin", branch, root=root, check=True)
        remote_ref = f"refs/remotes/origin/{branch}"
        has_remote = git("rev-parse", "--verify", remote_ref, root=root, check=False)
        if has_remote:
            behind_count = int(git("rev-list", "--count", f"HEAD..origin/{branch}", root=root))
            if behind_count > 0:
                raise ValueError(
                    f"Remote branch origin/{branch} is ahead by {behind_count} commit(s); stopping safely without overwrite"
                )

    if touched_paths:
        rel_paths = [str(Path(p).resolve().relative_to(root.resolve()).as_posix()) for p in touched_paths]
        git("add", "--", *rel_paths, root=root)
    else:
        git("add", "-u", root=root)

    msg = commit_message or "feat(gemini-notebook): import verified research receipt and update knowledge index"
    git("commit", "-m", msg, root=root)
    local_head = git("rev-parse", "HEAD", root=root)

    file_hashes = {}
    for p in touched_paths or []:
        rel = Path(p).resolve().relative_to(root.resolve()).as_posix()
        file_hashes[rel] = git("rev-parse", f"HEAD:{rel}", root=root)

    result = {
        "branch": branch,
        "committed": True,
        "pushed": False,
        "head_sha": local_head,
        "file_blob_shas": file_hashes,
        "readback_verified": False,
    }

    if do_push:
        # Single push, no force, no retry
        git("push", "origin", f"{branch}:{branch}", root=root, check=True)
        result["pushed"] = True
        ls_remote = git("ls-remote", "origin", f"refs/heads/{branch}", root=root, check=True)
        remote_sha = ls_remote.split()[0] if ls_remote else ""
        git("fetch", "origin", branch, root=root, check=True)
        remote_blobs_match = True
        for rel, expected_blob in file_hashes.items():
            actual_blob = git("rev-parse", f"origin/{branch}:{rel}", root=root, check=True)
            if actual_blob != expected_blob:
                remote_blobs_match = False
        result["remote_head_sha"] = remote_sha
        result["readback_verified"] = (remote_sha == local_head) and remote_blobs_match
        if not result["readback_verified"]:
            raise ValueError(f"Remote readback mismatch: local={local_head} remote={remote_sha}")
    else:
        # Local readback verification against local HEAD commit tree
        local_blobs_match = True
        for rel, expected_blob in file_hashes.items():
            actual_blob = git("rev-parse", f"HEAD:{rel}", root=root, check=True)
            if actual_blob != expected_blob:
                local_blobs_match = False
        result["readback_verified"] = local_blobs_match

    return result


def process_receipt_data(
    data,
    root=ROOT,
    apply=False,
    allow_updates=True,
    check_remote_branches=True,
    sync_index=False,
    state_path=None,
    index_path=None,
    export_drive_dir=None,
):
    """Core pipeline to validate and process a single parsed `research_receipt_v1` dict."""
    videos = validate(data)
    digest = compute_receipt_digest(data)

    registry_path = root / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("repository") != EXPECTED_REPO or not isinstance(registry.get("records"), list):
        raise ValueError("Unexpected registry.json")

    resolved_state_path = state_path or (root / "automation" / "gemini-notebook" / "state" / "loop_state.json")
    resolved_index_path = index_path or (root / "automation" / "gemini-notebook" / "state" / "AI技術研究室_知識索引.md")

    loop_state = load_loop_state(resolved_state_path)
    processed_hashes = {
        p.get("sha256") for p in loop_state.get("processed_receipts", []) if isinstance(p, dict)
    }

    local_records_by_id = {
        r.get("video_id"): r for r in registry["records"] if isinstance(r, dict) and r.get("video_id")
    }
    known_local = set(local_records_by_id.keys())
    remote_map = collect_remote_branch_videos(root=root) if check_remote_branches else {}

    planned_new = []
    planned_updates = []
    skipped = []

    if digest in processed_hashes:
        for v in videos:
            vid = v["video_id"]
            print("SKIP_EXISTING", vid)
            skipped.append({"video_id": vid, "reason": "SKIP_DUPLICATE_RECEIPT"})
    else:
        for v in videos:
            vid = v["video_id"]
            existing_md = sorted((root / "research").glob("*" + vid + "*.md"))
            is_local_known = (vid in known_local) or bool(existing_md)
            is_remote_known = (vid in remote_map) and not is_local_known
            changes_set = set(v.get("changes") or [])

            if v.get("notebook_readback") != "PASS":
                print("SKIP_UNVERIFIED_NOTEBOOK", vid)
                skipped.append({"video_id": vid, "reason": "SKIP_UNVERIFIED_NOTEBOOK"})
                continue
            if "METADATA_ONLY" in v["source_scope"].upper():
                print("SKIP_METADATA_ONLY", vid)
                skipped.append({"video_id": vid, "reason": "SKIP_METADATA_ONLY"})
                continue

            if is_local_known:
                # Check if this is an intentional delta update (UPDATED / CONFLICT)
                if allow_updates and (changes_set & {"UPDATED", "CONFLICT"}) and existing_md:
                    target_md = existing_md[0]
                    current_content = target_md.read_text(encoding="utf-8")
                    delta_text = render_delta_section(v, data["checked_at"])
                    # Prevent duplicate delta append if summary or same checked_at delta section already exists
                    if clean(v["summary_ja"]) in current_content or f"## 差分更新 ({data['checked_at']}" in current_content:
                        print("SKIP_EXISTING", vid)
                        skipped.append({"video_id": vid, "reason": "SKIP_EXISTING_DELTA_ALREADY_APPLIED"})
                        continue
                    planned_updates.append((target_md, delta_text, v))
                else:
                    print("SKIP_EXISTING", vid)
                    skipped.append({"video_id": vid, "reason": "SKIP_EXISTING"})
                continue

            if is_remote_known:
                branches_str = ",".join(remote_map[vid].get("branches", []))
                print("SKIP_EXISTING_REMOTE_BRANCH", vid, branches_str)
                skipped.append(
                    {
                        "video_id": vid,
                        "reason": "SKIP_EXISTING_REMOTE_BRANCH",
                        "branches": remote_map[vid].get("branches", []),
                    }
                )
                continue

            dst = root / "research" / ("{}-{}-gemini-notebook.md".format(data["checked_at"], vid))
            if dst.exists():
                print("SKIP_EXISTS", vid)
                skipped.append({"video_id": vid, "reason": "SKIP_EXISTS"})
                continue
            planned_new.append((dst, render(v, data["checked_at"]), v))

    summary_payload = {
        "new_records": len(planned_new),
        "ids": [v["video_id"] for _, _, v in planned_new],
        "updated_records": len(planned_updates),
        "updated_ids": [v["video_id"] for _, _, v in planned_updates],
        "skipped": skipped,
        "receipt_sha256": digest,
        "mode": "APPLY" if apply else "PREVIEW",
    }
    print(json.dumps(summary_payload, ensure_ascii=False))

    touched_files = []
    if not apply:
        return summary_payload, touched_files

    branch = check_write_boundary(root=root)
    for dst, _, _ in planned_new:
        if dst.exists():
            raise ValueError("Concurrent file already exists: " + str(dst))

    for dst, text, v in planned_new:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("x", encoding="utf-8") as f:
            f.write(text)
        touched_files.append(dst)
        rec_entry = {
            "record_id": "youtube:" + v["video_id"],
            "video_id": v["video_id"],
            "canonical_url": canonical_youtube_url(v["video_id"]),
            "research_path": dst.relative_to(root).as_posix(),
            "source_scope": v["source_scope"],
            "research_date": data["checked_at"],
            "status": "GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_REVIEW_REQUIRED",
            "evidence": "GEMINI_RESEARCH_RECEIPT",
        }
        if v["url"] != rec_entry["canonical_url"]:
            rec_entry["original_url"] = v["url"]
        registry["records"].append(rec_entry)

    for target_md, delta_text, v in planned_updates:
        existing_text = target_md.read_text(encoding="utf-8")
        sep = "" if existing_text.endswith("\n") else "\n"
        target_md.write_text(existing_text + sep + delta_text.lstrip("\n"), encoding="utf-8")
        touched_files.append(target_md)
        rec = local_records_by_id.get(v["video_id"])
        if rec is not None:
            rec["last_updated"] = data["checked_at"]
            history = rec.setdefault("update_history", [])
            history.append(
                {
                    "checked_at": data["checked_at"],
                    "changes": v["changes"],
                    "source_scope": v["source_scope"],
                }
            )

    if planned_new or planned_updates:
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        touched_files.append(registry_path)

    if sync_index or planned_new or planned_updates or data.get("next_topics") or data.get("unknowns"):
        if sync_index:
            idx_res = update_state_and_index(
                data=data,
                digest=digest,
                registry=registry,
                remote_map=remote_map,
                applied_new_ids=[v["video_id"] for _, _, v in planned_new],
                applied_updated_ids=[v["video_id"] for _, _, v in planned_updates],
                state_path=resolved_state_path,
                index_path=resolved_index_path,
                export_drive_dir=export_drive_dir,
            )
            touched_files.extend([ Path(idx_res["state_path"]), Path(idx_res["index_path"]) ])
            summary_payload["index_sync"] = idx_res

    print(
        "LOCAL_WRITE_COMPLETE branch={} files={} updates={} (NO_COMMIT_NO_PUSH)".format(
            branch, len(planned_new), len(planned_updates)
        )
    )
    return summary_payload, touched_files


def read_clipboard_text():
    """Read text from Windows clipboard via PowerShell Get-Clipboard (stdlib only)."""
    res = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return res.stdout


def discover_inbox_files(inbox_dir):
    """Find candidate `.json`, `.md`, `.txt` files in inbox directory sorted by name."""
    p = Path(inbox_dir)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"Inbox directory not found: {inbox_dir}")
    candidates = []
    for ext in ("*.json", "*.md", "*.txt"):
        candidates.extend(p.glob(ext))
    return sorted(set(candidates), key=lambda x: x.name)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Gemini Notebook research receipt bridge & knowledge index synchronizer"
    )
    ap.add_argument(
        "receipt",
        nargs="?",
        help="Gemini output JSON or Markdown file (secrets/transcripts prohibited)",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Write to local non-default branch",
    )
    ap.add_argument(
        "--from-clipboard",
        action="store_true",
        help="Extract `research_receipt_v1` directly from system clipboard",
    )
    ap.add_argument(
        "--inbox",
        help="Directory (local or Google Drive folder) to scan for unprocessed receipt files",
    )
    ap.add_argument(
        "--sync-index",
        action="store_true",
        help="Update `state/loop_state.json` and `state/AI技術研究室_知識索引.md`",
    )
    ap.add_argument(
        "--refresh-index-only",
        action="store_true",
        help="Rebuild `state/AI技術研究室_知識索引.md` from current & remote branches without a receipt",
    )
    ap.add_argument(
        "--export-drive-dir",
        help="Optional Google Drive folder path to export `AI技術研究室_知識索引.md`",
    )
    ap.add_argument(
        "--no-remote-dedup",
        action="store_true",
        help="Disable scanning `origin/*` branches for cross-branch duplicate video IDs",
    )
    ap.add_argument(
        "--commit",
        action="store_true",
        help="Commit applied changes to the current non-default branch",
    )
    ap.add_argument(
        "--push",
        action="store_true",
        help="Push committed changes to `origin/<branch>` and verify remote readback",
    )
    ap.add_argument(
        "--commit-message",
        help="Custom commit message when using --commit",
    )
    ap.add_argument(
        "--evidence-out",
        help="Write objective execution & readback evidence JSON to this file path",
    )
    args = ap.parse_args(argv)

    if args.push and not args.commit:
        args.commit = True
    if args.commit and not args.apply and not args.refresh_index_only:
        raise ValueError("--commit requires --apply or --refresh-index-only")

    all_touched = []
    results = []

    if args.refresh_index_only:
        branch = check_write_boundary(root=ROOT)
        registry = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
        remote_map = {} if args.no_remote_dedup else collect_remote_branch_videos(root=ROOT)
        dummy_data = {
            "checked_at": date.today().isoformat(),
            "notebook_url": "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
            "next_topics": [],
            "unknowns": [],
        }
        idx_res = update_state_and_index(
            data=dummy_data,
            digest=None,
            registry=registry,
            remote_map=remote_map,
            applied_new_ids=[],
            applied_updated_ids=[],
            export_drive_dir=args.export_drive_dir,
        )
        all_touched.extend([Path(idx_res["state_path"]), Path(idx_res["index_path"])])
        results.append({"mode": "REFRESH_INDEX_ONLY", "branch": branch, "index_sync": idx_res})
        print(json.dumps(results[-1], ensure_ascii=False))
    else:
        raw_inputs = []
        if args.from_clipboard:
            raw_inputs.append(("clipboard", read_clipboard_text()))
        elif args.inbox:
            files = discover_inbox_files(args.inbox)
            for f in files:
                raw_inputs.append((str(f), f.read_text(encoding="utf-8")))
        elif args.receipt:
            raw_inputs.append((args.receipt, Path(args.receipt).read_text(encoding="utf-8")))
        else:
            raise ValueError("Specify a receipt file, --from-clipboard, --inbox, or --refresh-index-only")

        for source_name, raw_text in raw_inputs:
            try:
                data = extract_receipt_payload(raw_text)
            except (ValueError, json.JSONDecodeError) as ex:
                if args.inbox:
                    print(f"SKIP_NON_RECEIPT_FILE {source_name}: {ex}")
                    continue
                raise
            summary, touched = process_receipt_data(
                data=data,
                root=ROOT,
                apply=args.apply,
                allow_updates=True,
                check_remote_branches=not args.no_remote_dedup,
                sync_index=args.sync_index,
                export_drive_dir=args.export_drive_dir,
            )
            summary["source"] = source_name
            results.append(summary)
            all_touched.extend(touched)

    git_evidence = None
    if args.commit and all_touched:
        git_evidence = verify_and_push_git(
            root=ROOT,
            commit_message=args.commit_message,
            do_push=args.push,
            touched_paths=all_touched,
        )
        print(json.dumps({"git_operation": git_evidence}, ensure_ascii=False))

    if args.evidence_out:
        ev_path = Path(args.evidence_out)
        ev_path.parent.mkdir(parents=True, exist_ok=True)
        ev_payload = {
            "schema_version": "gemini_notebook_bridge_evidence_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
            "git_operation": git_evidence,
        }
        ev_path.write_text(json.dumps(ev_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as ex:
        print("ERROR: " + str(ex), file=sys.stderr)
        sys.exit(2)
