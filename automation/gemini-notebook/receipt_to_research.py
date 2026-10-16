#!/usr/bin/env python3
"""Offline, explicit-import bridge: Gemini research receipt -> GitHub-ready notes.

Does not invoke any model, Google API, browser, network or GitHub write.
Default is preview only. --apply edits only a non-default local checkout.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ALLOWED_STATUSES = {"CONFIRMED_DOC", "REPORTED_BY_AUTHOR", "CONFIRMED_TEST", "UNKNOWN", "CONTRADICTED"}
ALLOWED_CHANGES = {"KNOWN", "NEW", "UPDATED", "CONFLICT", "UNKNOWN"}
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_REPO = "kamiyusense/ai-video-research"


def git(*args):
    result = subprocess.run(["git", "-C", str(ROOT), *args],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def check_write_boundary():
    branch = git("branch", "--show-current")
    if not branch or branch in {"main", "master"}:
        raise ValueError("Refusing detached/default-branch write")
    origin = git("remote", "get-url", "origin")
    if not re.search(r"(?:[:/])kamiyusense/ai-video-research(?:\.git)?/?$", origin):
        raise ValueError("Unexpected git origin: refusing write")
    return branch


def valid_url(value):
    if not isinstance(value, str):
        return False
    u = urlparse(value)
    return u.scheme == "https" and bool(u.netloc)


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
        if not valid_url(url) or urlparse(url).hostname not in {"www.youtube.com", "youtube.com", "youtu.be"}:
            raise ValueError("Video URL must be YouTube HTTPS")
        if not isinstance(v.get("title"), str) or not (1 <= len(v["title"]) <= 250):
            raise ValueError("Invalid title")
        if not isinstance(v.get("summary_ja"), str) or not (1 <= len(v["summary_ja"]) <= 300):
            raise ValueError("Summary must contain 1-300 characters")
        if not isinstance(v.get("source_scope"), str) or len(v["source_scope"]) > 180:
            raise ValueError("Invalid source_scope")
        if v.get("notebook_readback") not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("Invalid notebook source readback")
        if not isinstance(v.get("changes"), list) or not set(v["changes"]) <= ALLOWED_CHANGES:
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


def render(v, checked_at):
    vid = v["video_id"]
    lines = [
        "# " + clean(v["title"]),
        "",
        "- video_id: `" + vid + "`",
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
    for c in v["claims"]:
        t = c.get("timestamp_seconds")
        time_ref = ("[{:02d}:{:02d}](https://www.youtube.com/watch?v={}&t={}s)"
                    .format(t // 60, t % 60, vid, t)) if t is not None else "UNKNOWN"
        lines += ["- " + clean(c["text"]) + " | " + c["status"]
                  + " | time: " + time_ref
                  + " | official: " + (c.get("official_url") or "UNKNOWN")]
    lines += ["", "## 限界", "Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt", help="Gemini output JSON file (secrets/transcripts prohibited)")
    ap.add_argument("--apply", action="store_true", help="Write to local non-default branch; no commit/push")
    args = ap.parse_args()
    data = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    videos = validate(data)
    registry_path = ROOT / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("repository") != EXPECTED_REPO or not isinstance(registry.get("records"), list):
        raise ValueError("Unexpected registry.json")
    known = {r.get("video_id") for r in registry["records"]}
    planned = []
    for v in videos:
        vid = v["video_id"]
        if vid in known or any((ROOT / "research").glob("*" + vid + "*.md")):
            print("SKIP_EXISTING", vid)
            continue
        if v.get("notebook_readback") != "PASS":
            print("SKIP_UNVERIFIED_NOTEBOOK", vid)
            continue
        if "METADATA_ONLY" in v["source_scope"].upper():
            print("SKIP_METADATA_ONLY", vid)
            continue
        dst = ROOT / "research" / ("{}-{}-gemini-notebook.md".format(data["checked_at"], vid))
        if dst.exists():
            print("SKIP_EXISTS", vid)
            continue
        planned.append((dst, render(v, data["checked_at"]), v))
    print(json.dumps({"new_records": len(planned), "ids": [v["video_id"] for _, _, v in planned],
                      "mode": "APPLY" if args.apply else "PREVIEW"}, ensure_ascii=False))
    if not args.apply:
        return
    branch = check_write_boundary()
    for dst, _, _ in planned:
        if dst.exists():
            raise ValueError("Concurrent file already exists: " + str(dst))
    for dst, text, v in planned:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("x", encoding="utf-8") as f:
            f.write(text)
        registry["records"].append({
            "record_id": "youtube:" + v["video_id"],
            "video_id": v["video_id"],
            "canonical_url": v["url"],
            "research_path": dst.relative_to(ROOT).as_posix(),
            "source_scope": v["source_scope"],
            "research_date": data["checked_at"],
            "status": "GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_REVIEW_REQUIRED",
            "evidence": "GEMINI_RESEARCH_RECEIPT"
        })
    if planned:
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    print("LOCAL_WRITE_COMPLETE branch={} files={} (NO_COMMIT_NO_PUSH)".format(branch, len(planned)))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as ex:
        print("ERROR: " + str(ex), file=sys.stderr)
        sys.exit(2)
