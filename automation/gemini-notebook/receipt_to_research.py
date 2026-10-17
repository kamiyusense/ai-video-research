#!/usr/bin/env python3
"""Offline, Cloud-Action & Git-verified bridge: Gemini research receipt -> GitHub notes (v0.4).

Key v0.4 guarantees:
1. Shared Contract & Cross-Language Parity: loads `contract_spec_v1.json` so Python (`receipt_to_research.py`)
   and Google Apps Script (`cloud_relay_gas.js`) enforce identical schema validation, forbidden-key rejection,
   SHA-256 canonicalization, deduplication, and Markdown rendering.
2. Forbidden Key Rejection: recursively scans receipt payloads and immediately rejects raw transcripts,
   subtitles, or credential keys (`transcript`, `subtitles`, `api_key`, `secret`, etc.).
3. Fresh & Incremental Remote Branch Deduplication: runs `git fetch --prune origin` before scanning `origin/*`,
   uses branch commit SHA caching + filename-first extraction to scale cleanly as records grow, and checks
   both `registry.json` and `research/*.md` / `notes/*.md`.
4. State Corruption Protection: if `loop_state.json` exists but is unreadable, invalid JSON, or
   violates schema, raises ValueError immediately and NEVER silently resets existing history.
5. Explicit Index Distinction & Honest Sync Status: generates `state/github_knowledge_index_export.md`
   separately from Gemini Notebook's internal `AI技術研究室_知識索引.md`, and strictly separates
   `github_write_status` from `notebook_sync_status` (`"NOT_SYNCED_FROM_GITHUB"`).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CONTRACT_PATH = Path(__file__).resolve().parent / "contract_spec_v1.json"
CONTRACT = (
    json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if CONTRACT_PATH.exists()
    else {}
)

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ALLOWED_STATUSES = set(
    CONTRACT.get(
        "allowed_statuses",
        [
            "CONFIRMED_DOC",
            "REPORTED_BY_AUTHOR",
            "CONFIRMED_TEST",
            "UNKNOWN",
            "CONTRADICTED",
        ],
    )
)
ALLOWED_CHANGES = set(
    CONTRACT.get("allowed_changes", ["KNOWN", "NEW", "UPDATED", "CONFLICT", "UNKNOWN"])
)
FORBIDDEN_PAYLOAD_KEYS = {
    k.lower()
    for k in CONTRACT.get(
        "forbidden_payload_keys",
        [
            "transcript",
            "full_transcript",
            "raw_transcript",
            "subtitles",
            "captions",
            "full_text",
            "video_binary",
            "api_key",
            "apikey",
            "access_token",
            "refresh_token",
            "private_key",
            "secret",
            "password",
            "authorization",
        ],
    )
}
FORBIDDEN_VALUE_PATTERNS = [
    (
        item["id"],
        re.compile(item["pattern"], re.MULTILINE),
    )
    for item in CONTRACT.get(
        "forbidden_value_patterns",
        [
            {
                "id": "GITHUB_TOKEN",
                "pattern": r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b",
            },
            {
                "id": "GOOGLE_API_OR_OAUTH_TOKEN",
                "pattern": r"\bAIza[0-9A-Za-z_-]{30,}\b|\bya29\.[0-9A-Za-z_-]{20,}\b",
            },
            {
                "id": "LLM_OR_SAAS_SECRET_KEY",
                "pattern": r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}\b|\bxox[baprs]-[0-9A-Za-z-]{10,}\b",
            },
            {
                "id": "PRIVATE_KEY_BLOCK",
                "pattern": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
            },
            {
                "id": "BEARER_AUTH_HEADER",
                "pattern": r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b",
            },
            {
                "id": "SUBTITLE_TIMECODE_BLOCK",
                "pattern": r"\bWEBVTT\b|\d{1,2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}",
            },
            {
                "id": "MULTILINE_TIMESTAMP_TRANSCRIPT",
                "pattern": r"(?:^|\n)\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s+[^\n]+\n\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s+[^\n]+\n\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s+",
            },
        ],
    )
]
MAX_NEWLINES_PER_TEXT_FIELD = CONTRACT.get("limits", {}).get("max_newlines_per_text_field", 3)
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_REPO = CONTRACT.get("expected_repo", "kamiyusense/ai-video-research")
DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "state" / "loop_state.json"
DEFAULT_GITHUB_INDEX_EXPORT_PATH = (
    Path(__file__).resolve().parent / "state" / "github_knowledge_index_export.md"
)
NOTEBOOK_INTERNAL_MASTER_INDEX_NAME = CONTRACT.get(
    "notebook_internal_master_index_name", "AI技術研究室_知識索引.md"
)
YOUTUBE_HOSTS = set(
    CONTRACT.get(
        "youtube_hosts",
        ["www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"],
    )
)

FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
FILENAME_VID_RE = re.compile(r"(?:^|/)\d{4}-\d{2}-\d{2}-([A-Za-z0-9_-]{11})-[^/]+\.md$")
BODY_VID_PATTERNS = [
    re.compile(r"^\s*-\s*video_id:\s*`?([A-Za-z0-9_-]{11})`?\s*$", re.MULTILINE),
    re.compile(r"^\s*-\s*record_id:\s*`?youtube:([A-Za-z0-9_-]{11})`?\s*$", re.MULTILINE),
    re.compile(r"^###\s+\d+[｜|]([A-Za-z0-9_-]{11})\s*$", re.MULTILINE),
    re.compile(r"^\s*-\s*`([A-Za-z0-9_-]{11})`:\s+", re.MULTILINE),
]


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
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict) and data.get("schema_version") == "research_receipt_v1":
                return data
        except json.JSONDecodeError:
            pass
    for match in FENCED_JSON_RE.finditer(raw_text):
        block = match.group(1).strip()
        try:
            data = json.loads(block)
            if isinstance(data, dict) and data.get("schema_version") == "research_receipt_v1":
                return data
        except json.JSONDecodeError:
            continue
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
    data = json.loads(stripped)
    return data


def compute_receipt_digest(data):
    """Compute canonical SHA-256 digest for a validated receipt payload."""
    canonical_bytes = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def scan_forbidden_keys(val, path="root"):
    """Recursively scan receipt payload and reject forbidden keys or secret/transcript value patterns."""
    if isinstance(val, dict):
        for k, v in val.items():
            k_str = str(k).strip().lower()
            if k_str in FORBIDDEN_PAYLOAD_KEYS:
                raise ValueError(f"Forbidden key in receipt payload: {path}.{k}")
            scan_forbidden_keys(v, f"{path}.{k}")
    elif isinstance(val, list):
        for idx, item in enumerate(val):
            scan_forbidden_keys(item, f"{path}[{idx}]")
    elif isinstance(val, str):
        for rule_id, pat in FORBIDDEN_VALUE_PATTERNS:
            if pat.search(val):
                raise ValueError(
                    f"Forbidden content pattern ({rule_id}) in receipt payload at {path}"
                )


def validate(data):
    if not isinstance(data, dict) or data.get("schema_version") != "research_receipt_v1":
        raise ValueError("Invalid receipt schema_version")
    scan_forbidden_keys(data)
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
        if v["summary_ja"].count("\n") > MAX_NEWLINES_PER_TEXT_FIELD:
            raise ValueError("Summary contains too many line breaks (possible transcript dump)")
        if not isinstance(v.get("source_scope"), str) or len(v["source_scope"]) > 180:
            raise ValueError("Invalid source_scope")
        if v.get("notebook_readback") not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("Invalid notebook source readback")
        if (
            not isinstance(v.get("changes"), list)
            or not v["changes"]
            or not set(v["changes"]) <= ALLOWED_CHANGES
        ):
            raise ValueError("Invalid changes")
        claims = v.get("claims")
        if not isinstance(claims, list) or len(claims) > 12:
            raise ValueError("Claims must be a list of <=12 items")
        for c in claims:
            if not isinstance(c, dict) or not isinstance(c.get("text"), str) or len(c["text"]) > 500:
                raise ValueError("Invalid claim")
            if c["text"].count("\n") > MAX_NEWLINES_PER_TEXT_FIELD:
                raise ValueError("Claim text contains too many line breaks (possible transcript dump)")
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
            "[{:02d}:{:02d}](https://www.youtube.com/watch?v={}&t={}s)".format(
                t // 60, t % 60, vid, t
            )
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
        "- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB",
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
        "Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。",
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
        "- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB",
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


def extract_video_ids_from_markdown_text(md_text):
    """Extract video_ids referenced inside a research/note markdown body."""
    found = set()
    if not isinstance(md_text, str):
        return found
    for pat in BODY_VID_PATTERNS:
        for m in pat.finditer(md_text):
            vid = m.group(1)
            if VIDEO_ID.fullmatch(vid):
                found.add(vid)
    return found


def collect_local_research_videos(root=ROOT):
    """Scan local `registry.json`, `research/*.md`, and `notes/*.md` (both filenames and bodies)."""
    local_map = {}
    registry_path = root / "registry.json"
    if registry_path.exists():
        reg = json.loads(registry_path.read_text(encoding="utf-8"))
        for r in reg.get("records", []):
            if isinstance(r, dict):
                vid = r.get("video_id")
                if isinstance(vid, str) and VIDEO_ID.fullmatch(vid):
                    local_map[vid] = {
                        "video_id": vid,
                        "source": "registry.json",
                        "research_path": r.get("research_path", ""),
                        "status": r.get("status", "RECORDED"),
                    }

    for folder_name in ("research", "notes"):
        folder = root / folder_name
        if not folder.exists():
            continue
        for md_file in sorted(folder.rglob("*.md")):
            rel_path = md_file.relative_to(root).as_posix()
            m_name = FILENAME_VID_RE.search(rel_path)
            if m_name:
                vid = m_name.group(1)
                if vid not in local_map:
                    local_map[vid] = {
                        "video_id": vid,
                        "source": f"filename:{rel_path}",
                        "research_path": rel_path,
                        "status": "RECORDED_IN_RESEARCH_FILE_UNREGISTERED",
                    }
            try:
                body = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
            for vid in extract_video_ids_from_markdown_text(body):
                if vid not in local_map:
                    local_map[vid] = {
                        "video_id": vid,
                        "source": f"body:{rel_path}",
                        "research_path": rel_path,
                        "status": "REFERENCED_IN_RESEARCH_OR_NOTE_BODY",
                    }
    return local_map


def refresh_remote_refs(root=ROOT, allow_stale=False):
    """Fetch latest remote-tracking branches from `origin` so stale local refs are never trusted."""
    res = subprocess.run(
        ["git", "-C", str(root), "fetch", "--prune", "origin"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode == 0:
        return "FRESH_FETCHED"
    if allow_stale:
        return "STALE_LOCAL_REFS_ALLOWED"
    raise ValueError(
        "Failed to fetch fresh remote refs from origin (refusing to trust potentially stale local refs): "
        + (res.stderr.strip() or res.stdout.strip() or f"exit={res.returncode}")
    )


def collect_remote_branch_videos(
    root=ROOT, fetch_remote=True, allow_stale_remotes=False, branch_cache=None
):
    """Scan `refs/remotes/origin/*` branches after fetching fresh refs.

    Uses `branch_cache` (keyed by remote branch commit SHA) so unchanged branches do not
    need to re-read every markdown body as the repository scales.
    """
    freshness = "UNFETCHED_LOCAL_REFS"
    if fetch_remote:
        freshness = refresh_remote_refs(root=root, allow_stale=allow_stale_remotes)

    remote_map = {}
    refs_out = git(
        "for-each-ref",
        "--format=%(refname:short) %(objectname)",
        "refs/remotes/origin/",
        root=root,
        check=False,
    )
    for line in refs_out.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        ref = parts[0]
        commit_sha = parts[1] if len(parts) > 1 else ""
        if not ref or ref in {"origin/HEAD", "origin/main", "origin"}:
            continue

        if isinstance(branch_cache, dict) and commit_sha:
            cached = branch_cache.get(ref)
            if (
                isinstance(cached, dict)
                and cached.get("commit_sha") == commit_sha
                and cached.get("scan_complete") is True
            ):
                for entry in cached.get("videos", []):
                    vid = entry.get("video_id")
                    if vid and VIDEO_ID.fullmatch(vid):
                        info = remote_map.setdefault(
                            vid,
                            {
                                "video_id": vid,
                                "canonical_url": entry.get("canonical_url")
                                or canonical_youtube_url(vid),
                                "research_path": entry.get("research_path", ""),
                                "status": entry.get("status", "UNKNOWN"),
                                "detected_via": entry.get("detected_via", "cache"),
                                "branches": [],
                            },
                        )
                        if ref not in info["branches"]:
                            info["branches"].append(ref)
                continue

        branch_entries = {}
        # 1. Check registry.json on this remote branch
        reg_raw = git("show", f"{ref}:registry.json", root=root, check=False)
        if reg_raw:
            try:
                reg = json.loads(reg_raw)
                for rec in reg.get("records", []):
                    vid = rec.get("video_id")
                    if isinstance(vid, str) and VIDEO_ID.fullmatch(vid):
                        entry = {
                            "video_id": vid,
                            "canonical_url": rec.get("canonical_url")
                            or canonical_youtube_url(vid),
                            "research_path": rec.get("research_path", ""),
                            "status": rec.get("status", "UNKNOWN"),
                            "detected_via": "registry.json",
                        }
                        branch_entries.setdefault(vid, entry)
                        info = remote_map.setdefault(
                            vid, {**entry, "branches": []}
                        )
                        if ref not in info["branches"]:
                            info["branches"].append(ref)
            except json.JSONDecodeError:
                pass

        # 2. Check research/*.md and notes/*.md filenames and bodies on this remote branch
        tree_files = git(
            "ls-tree", "-r", "--name-only", ref, "research/", "notes/", root=root, check=False
        )
        for rel_path in tree_files.splitlines():
            rel_path = rel_path.strip()
            if not rel_path.endswith(".md"):
                continue
            m_name = FILENAME_VID_RE.search(rel_path)
            if m_name:
                vid = m_name.group(1)
                entry = {
                    "video_id": vid,
                    "canonical_url": canonical_youtube_url(vid),
                    "research_path": rel_path,
                    "status": "REMOTE_RESEARCH_FILE",
                    "detected_via": f"filename:{rel_path}",
                }
                branch_entries.setdefault(vid, entry)
                info = remote_map.setdefault(vid, {**entry, "branches": []})
                if ref not in info["branches"]:
                    info["branches"].append(ref)

            body = git("show", f"{ref}:{rel_path}", root=root, check=False)
            for vid in extract_video_ids_from_markdown_text(body):
                entry = {
                    "video_id": vid,
                    "canonical_url": canonical_youtube_url(vid),
                    "research_path": rel_path,
                    "status": "REMOTE_MARKDOWN_REFERENCE",
                    "detected_via": f"body:{rel_path}",
                }
                branch_entries.setdefault(vid, entry)
                info = remote_map.setdefault(vid, {**entry, "branches": []})
                if ref not in info["branches"]:
                    info["branches"].append(ref)

        if isinstance(branch_cache, dict) and commit_sha:
            branch_cache[ref] = {
                "commit_sha": commit_sha,
                "scan_complete": True,
                "videos": list(branch_entries.values()),
            }

    return remote_map, freshness


def default_initial_loop_state():
    return {
        "schema_version": "gemini_notebook_loop_state_v1",
        "repository": EXPECTED_REPO,
        "notebook_url": "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
        "notebook_internal_master_index_name": NOTEBOOK_INTERNAL_MASTER_INDEX_NAME,
        "github_index_export_file": "automation/gemini-notebook/state/github_knowledge_index_export.md",
        "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
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


def validate_loop_state_schema(state, state_path):
    if not isinstance(state, dict):
        raise ValueError(
            f"Corrupted loop_state.json at {state_path}: root must be a JSON object (refusing to reset existing state)"
        )
    if state.get("schema_version") != "gemini_notebook_loop_state_v1":
        raise ValueError(
            f"Corrupted loop_state.json at {state_path}: unexpected schema_version={state.get('schema_version')!r} (refusing to reset existing state)"
        )
    for list_key in ("processed_receipts", "next_topics_queue", "open_unknowns"):
        if not isinstance(state.get(list_key), list):
            raise ValueError(
                f"Corrupted loop_state.json at {state_path}: '{list_key}' must be a list (refusing to reset existing state)"
            )
    return state


def load_loop_state(state_path=DEFAULT_STATE_PATH):
    """Load `loop_state.json`. If file exists but is corrupted/unreadable, raise ValueError and NEVER reset."""
    if state_path.exists():
        try:
            raw = state_path.read_text(encoding="utf-8")
        except OSError as ex:
            raise ValueError(
                f"Unreadable loop_state.json at {state_path}: {ex} (refusing to reset existing state)"
            ) from ex
        try:
            state = json.loads(raw)
        except json.JSONDecodeError as ex:
            raise ValueError(
                f"Corrupted JSON in loop_state.json at {state_path}: {ex} (refusing to reset existing state)"
            ) from ex
        return validate_loop_state_schema(state, state_path)
    return default_initial_loop_state()


def render_github_knowledge_index_export_md(registry, local_map, remote_map, loop_state, freshness):
    """Render `github_knowledge_index_export.md` (GitHub-side ledger & delta snapshot).

    Explicitly distinguishes this GitHub export from Gemini Notebook's internal master index
    (`AI技術研究室_知識索引.md`) so the Notebook master index is never blindly overwritten.
    """
    reg_records = {
        r["video_id"]: r
        for r in registry.get("records", [])
        if isinstance(r, dict) and r.get("video_id")
    }
    all_vids = sorted(set(reg_records.keys()) | set(local_map.keys()) | set(remote_map.keys()))

    lines = [
        "# GitHub正本 知識索引・差分エクスポート (`github_knowledge_index_export.md`)",
        "",
        "> **【重要：索引の区別と上書き禁止】**",
        f"> - このファイルは **GitHub 正本（`{EXPECTED_REPO}`）側の既知動画台帳・未解決課題・次回テーマの差分エクスポート** です。",
        f"> - Gemini Notebook 内に既存の総合索引ソース **`{NOTEBOOK_INTERNAL_MASTER_INDEX_NAME}`**（先行16ソース等の蓄積を含む総合索引）とは**別物**です。",
        f"> - Notebook 内の `{NOTEBOOK_INTERNAL_MASTER_INDEX_NAME}` をこのファイルで丸ごと上書き置換しないでください。Notebook 側では既存内容を維持したまま差分追記（または別ソースとして参照）してください。",
        "> - **GitHub への保存成功は、Gemini Notebook への同期完了を意味しません** (`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`)。",
        "",
        f"- 対象リポジトリ: `{EXPECTED_REPO}` (private)",
        f"- 補助知識庫 (Gemini Notebook): {loop_state.get('notebook_url', 'https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7')}",
        f"- GitHub側エクスポート更新日: {loop_state.get('last_updated') or 'INITIAL'}",
        f"- リモートブランチ照合鮮度: `{freshness}`",
        f"- Notebook側への逆同期状態: `{loop_state.get('notebook_sync_status', 'NOT_SYNCED_FROM_GITHUB')}`",
        "",
        "## 1. GitHub全ブランチ横断・既知の動画ID台帳（重複登録禁止リスト）",
        "",
        "`registry.json` だけでなく、`research/*.md` および `notes/*.md` のファイル名・本文から検出された動画IDを含みます。",
        "",
        "| video_id | 状態 | 検出元 (現在ブランチ / 並行PRブランチ) | 参照パス |",
        "|---|---|---|---|",
    ]
    for vid in all_vids:
        if vid in reg_records:
            rec = reg_records[vid]
            status = clean(rec.get("status", "RECORDED"))
            rpath = clean(rec.get("research_path", ""))
            loc = "current_branch (registry.json)"
        elif vid in local_map:
            linfo = local_map[vid]
            status = clean(linfo.get("status", "LOCAL_MARKDOWN"))
            rpath = clean(linfo.get("research_path", ""))
            loc = f"current_branch ({linfo.get('source', 'markdown')})"
        else:
            rinfo = remote_map[vid]
            status = clean(rinfo.get("status", "REMOTE_BRANCH_ONLY"))
            rpath = clean(rinfo.get("research_path", ""))
            via = rinfo.get("detected_via", "remote")
            branches = ", ".join(rinfo.get("branches", []))
            loc = f"{branches} ({via})"
        lines.append(f"| `{vid}` | {status} | {loc} | `{rpath}` |")

    lines += [
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
    local_map,
    remote_map,
    freshness,
    applied_new_ids,
    applied_updated_ids,
    state_path=DEFAULT_STATE_PATH,
    index_path=DEFAULT_GITHUB_INDEX_EXPORT_PATH,
    export_drive_dir=None,
):
    """Update `loop_state.json` and `github_knowledge_index_export.md`.

    Never claims that Gemini Notebook itself has been synchronized.
    """
    state = load_loop_state(state_path)
    checked_at = data.get("checked_at") or date.today().isoformat()
    state["last_updated"] = checked_at
    state["notebook_internal_master_index_name"] = NOTEBOOK_INTERNAL_MASTER_INDEX_NAME
    state["github_index_export_file"] = "automation/gemini-notebook/state/github_knowledge_index_export.md"
    state["notebook_sync_status"] = "NOT_SYNCED_FROM_GITHUB"
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
                "github_write_status": "APPLIED_LOCAL",
                "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
            }
        )

    queue = state.setdefault("next_topics_queue", [])
    for topic in data.get("next_topics") or []:
        t_clean = clean(topic)
        if t_clean and t_clean not in queue:
            queue.append(t_clean)
    state["next_topics_queue"] = queue[-15:]

    unknowns = state.setdefault("open_unknowns", [])
    for unk in data.get("unknowns") or []:
        u_clean = clean(unk)
        if u_clean and u_clean not in unknowns:
            unknowns.append(u_clean)
    state["open_unknowns"] = unknowns[-25:]

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index_md = render_github_knowledge_index_export_md(
        registry, local_map, remote_map, state, freshness
    )
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
        "github_index_export_path": str(index_path),
        "notebook_internal_master_index_name": NOTEBOOK_INTERNAL_MASTER_INDEX_NAME,
        "github_index_export_status": "WRITTEN_LOCAL",
        "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
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
            "github_write_status": "NO_CHANGES",
            "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
        }

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
        rel_paths = [
            str(Path(p).resolve().relative_to(root.resolve()).as_posix()) for p in touched_paths
        ]
        git("add", "--", *rel_paths, root=root)
    else:
        git("add", "-u", root=root)

    msg = (
        commit_message
        or "feat(gemini-notebook): import verified research receipt and export GitHub knowledge index"
    )
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
        "github_write_status": "COMMITTED_LOCAL_ONLY",
        "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
    }

    if do_push:
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
        result["github_write_status"] = "PUSHED_AND_READBACK_VERIFIED"
    else:
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
    fetch_remote=True,
    allow_stale_remotes=False,
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

    resolved_state_path = state_path or (
        root / "automation" / "gemini-notebook" / "state" / "loop_state.json"
    )
    resolved_index_path = index_path or (
        root / "automation" / "gemini-notebook" / "state" / "github_knowledge_index_export.md"
    )

    # Load and validate loop_state.json BEFORE doing any work (raises ValueError if corrupted)
    loop_state = load_loop_state(resolved_state_path)
    processed_hashes = {
        p.get("sha256") for p in loop_state.get("processed_receipts", []) if isinstance(p, dict)
    }

    local_records_by_id = {
        r.get("video_id"): r
        for r in registry["records"]
        if isinstance(r, dict) and r.get("video_id")
    }
    local_map = collect_local_research_videos(root=root)

    if check_remote_branches:
        remote_map, freshness = collect_remote_branch_videos(
            root=root,
            fetch_remote=fetch_remote,
            allow_stale_remotes=allow_stale_remotes,
        )
    else:
        remote_map, freshness = {}, "DISABLED"

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
            is_local_known = (vid in local_records_by_id) or (vid in local_map) or bool(existing_md)
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
                if allow_updates and (changes_set & {"UPDATED", "CONFLICT"}) and existing_md:
                    target_md = existing_md[0]
                    current_content = target_md.read_text(encoding="utf-8")
                    delta_text = render_delta_section(v, data["checked_at"])
                    if (
                        clean(v["summary_ja"]) in current_content
                        or f"## 差分更新 ({data['checked_at']}" in current_content
                    ):
                        print("SKIP_EXISTING", vid)
                        skipped.append(
                            {"video_id": vid, "reason": "SKIP_EXISTING_DELTA_ALREADY_APPLIED"}
                        )
                        continue
                    planned_updates.append((target_md, delta_text, v))
                else:
                    source_detail = local_map.get(vid, {}).get("source", "local")
                    print("SKIP_EXISTING", vid)
                    skipped.append(
                        {"video_id": vid, "reason": "SKIP_EXISTING", "detected_via": source_detail}
                    )
                continue

            if is_remote_known:
                branches_str = ",".join(remote_map[vid].get("branches", []))
                detected_via = remote_map[vid].get("detected_via", "remote")
                print("SKIP_EXISTING_REMOTE_BRANCH", vid, branches_str)
                skipped.append(
                    {
                        "video_id": vid,
                        "reason": "SKIP_EXISTING_REMOTE_BRANCH",
                        "branches": remote_map[vid].get("branches", []),
                        "detected_via": detected_via,
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
        "remote_dedup_freshness": freshness,
        "github_write_status": "PREVIEW_ONLY" if not apply else "PENDING_WRITE",
        "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
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
            "status": "GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE",
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

    if sync_index:
        # Re-collect local research videos after applying new/updated records
        updated_local_map = collect_local_research_videos(root=root)
        idx_res = update_state_and_index(
            data=data,
            digest=digest,
            registry=registry,
            local_map=updated_local_map,
            remote_map=remote_map,
            freshness=freshness,
            applied_new_ids=[v["video_id"] for _, _, v in planned_new],
            applied_updated_ids=[v["video_id"] for _, _, v in planned_updates],
            state_path=resolved_state_path,
            index_path=resolved_index_path,
            export_drive_dir=export_drive_dir,
        )
        touched_files.extend([Path(idx_res["state_path"]), Path(idx_res["github_index_export_path"])])
        summary_payload["github_index_export"] = idx_res

    summary_payload["github_write_status"] = "LOCAL_WORKTREE_WRITTEN"
    print(
        "LOCAL_WRITE_COMPLETE branch={} files={} updates={} (NO_COMMIT_NO_PUSH; NOTEBOOK_SYNC=NOT_SYNCED_FROM_GITHUB)".format(
            branch, len(planned_new), len(planned_updates)
        )
    )
    return summary_payload, touched_files


def read_clipboard_text():
    """Read text from Windows clipboard via PowerShell Get-Clipboard (stdlib only)."""
    res = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw",
        ],
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
        description="Gemini Notebook research receipt bridge & GitHub knowledge index exporter (v0.3)"
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
        "--payload-string",
        help="Raw receipt JSON or Markdown text passed directly (e.g. from cloud workflow_dispatch)",
    )
    ap.add_argument(
        "--payload-env",
        help="Environment variable name holding raw receipt JSON or Markdown (e.g. RECEIPT_PAYLOAD in GitHub Actions)",
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
        help="Update `state/loop_state.json` and `state/github_knowledge_index_export.md`",
    )
    ap.add_argument(
        "--refresh-index-only",
        action="store_true",
        help="Rebuild `state/github_knowledge_index_export.md` from current & freshly fetched remote branches",
    )
    ap.add_argument(
        "--export-drive-dir",
        help="Optional Google Drive folder path to export `github_knowledge_index_export.md`",
    )
    ap.add_argument(
        "--no-remote-dedup",
        action="store_true",
        help="Disable scanning `origin/*` branches for cross-branch duplicate video IDs",
    )
    ap.add_argument(
        "--allow-stale-remotes",
        action="store_true",
        help="Allow fallback to cached remote refs if `git fetch --prune origin` fails (offline mode)",
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
        local_map = collect_local_research_videos(root=ROOT)
        if args.no_remote_dedup:
            remote_map, freshness = {}, "DISABLED"
        else:
            remote_map, freshness = collect_remote_branch_videos(
                root=ROOT,
                fetch_remote=True,
                allow_stale_remotes=args.allow_stale_remotes,
            )
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
            local_map=local_map,
            remote_map=remote_map,
            freshness=freshness,
            applied_new_ids=[],
            applied_updated_ids=[],
            export_drive_dir=args.export_drive_dir,
        )
        all_touched.extend(
            [Path(idx_res["state_path"]), Path(idx_res["github_index_export_path"])]
        )
        results.append(
            {
                "mode": "REFRESH_INDEX_ONLY",
                "branch": branch,
                "remote_dedup_freshness": freshness,
                "github_index_export": idx_res,
                "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
            }
        )
        print(json.dumps(results[-1], ensure_ascii=False))
    else:
        raw_inputs = []
        if args.payload_env:
            env_val = os.environ.get(args.payload_env, "")
            if not env_val.strip():
                raise ValueError(f"Environment variable {args.payload_env!r} is empty or not set")
            raw_inputs.append((f"env:{args.payload_env}", env_val))
        elif args.payload_string:
            raw_inputs.append(("payload_string", args.payload_string))
        elif args.from_clipboard:
            raw_inputs.append(("clipboard", read_clipboard_text()))
        elif args.inbox:
            files = discover_inbox_files(args.inbox)
            for f in files:
                raw_inputs.append((str(f), f.read_text(encoding="utf-8")))
        elif args.receipt:
            raw_inputs.append((args.receipt, Path(args.receipt).read_text(encoding="utf-8")))
        else:
            raise ValueError(
                "Specify a receipt file, --payload-env, --payload-string, --from-clipboard, --inbox, or --refresh-index-only"
            )

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
                fetch_remote=True,
                allow_stale_remotes=args.allow_stale_remotes,
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
            "notebook_sync_status": "NOT_SYNCED_FROM_GITHUB",
        }
        ev_path.write_text(
            json.dumps(ev_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as ex:
        print("ERROR: " + str(ex), file=sys.stderr)
        sys.exit(2)
