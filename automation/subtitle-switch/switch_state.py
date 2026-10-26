"""Local inventory and preference outbox. No network or model calls.

The inventory is deliberately separate from the canonical research registry.
Only allowlisted candidate metadata enters state or preference documents.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gemini-notebook"))
from intake_url import extract_youtube_id, canonical_youtube_url

FIELDS = ("title", "channel", "published_at", "lang", "theme", "kind", "reason")


def read_inbox(folder: Path):
    """Return normalized unique candidates and per-file errors; ignore non-JSON."""
    candidates, errors = {}, []
    for path in sorted(folder.glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8-sig"))
            rows = document["videos"]
            if not isinstance(rows, list):
                raise ValueError("videos must be a list")
            file_candidates = {}
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("video must be an object")
                vid = extract_youtube_id(row.get("url"))
                if not vid:
                    raise ValueError("invalid YouTube URL")
                file_candidates.setdefault(vid, {
                    "video_id": vid, "url": canonical_youtube_url(vid),
                    **{key: row.get(key, "") if isinstance(row.get(key, ""), str) else ""
                       for key in FIELDS},
                })
            for vid, candidate in file_candidates.items():
                candidates.setdefault(vid, candidate)
        except (OSError, ValueError, KeyError, TypeError):
            # Do not include untrusted file contents or exception text in logs.
            errors.append({"file": path.name, "status": "要確認"})
    return list(candidates.values()), errors


def atomic_json(path: Path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


class Inventory:
    def __init__(self, path: Path):
        self.path = path
        # A corrupt file must never silently erase rejection/progress history.
        self.data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
            "version": 1, "videos": {},
        }
        if self.data.get("version") != 1 or not isinstance(self.data.get("videos"), dict):
            raise ValueError("UNKNOWN: unsupported inventory")

    def save(self):
        atomic_json(self.path, self.data)

    def refresh(self, candidates):
        for candidate in candidates:
            vid = candidate["video_id"]
            row = self.data["videos"].setdefault(vid, {
                "rejected": False, "rejection_reason": "", "stage": "intake",
                "status": "pending", "completed_stages": [],
            })
            for key in ("video_id", "url", *FIELDS):
                # Do not let a manual URL or a later scout file erase the metadata
                # used to build already-checkpointed OKFs.
                if key in ("title", "published_at") and "captions" in row["completed_stages"]:
                    continue
                if candidate[key] or key not in row:
                    row[key] = candidate[key]
        self.save()

    def reject(self, vid, rejected=True, reason=""):
        row = self.data["videos"][vid]
        row.update(rejected=bool(rejected), rejection_reason=reason if rejected else "")
        self.save()

    def visible(self, show_rejected=False, show_processed=False):
        return [row.copy() for row in self.data["videos"].values()
                if (show_rejected or not row["rejected"])
                and (show_processed or row["status"] not in ("complete", "ALREADY_REGISTERED"))]

    def preferences(self, today=None, saved_ids=None):
        document = {"updated": (today or date.today()).isoformat(),
                    "source": "subtitle-switch", "session_id": str(uuid4()), "saved": [], "rejected": [],
                    "liked_channels": []}
        for row in self.data["videos"].values():
            if row["rejected"]:
                document["rejected"].append({
                    **{key: row[key] for key in ("video_id", "channel", "theme")},
                    "reason": row["rejection_reason"],
                })
            elif row["status"] == "complete" and (saved_ids is None or row["video_id"] in saved_ids):
                document["saved"].append({key: row[key] for key in
                                          ("video_id", "channel", "theme", "lang", "kind")})
        return document


def write_preferences(folder: Path, document):
    """Exclusive creation: never overwrite seed or an earlier session."""
    folder.mkdir(parents=True, exist_ok=True)
    stamp = date.fromisoformat(document["updated"]).strftime("%Y%m%d")
    index = 1
    while True:
        suffix = "" if index == 1 else f"_{index}"
        path = folder / f"preferences_{stamp}{suffix}.json"
        try:
            with path.open("x", encoding="utf-8") as stream:
                json.dump(document, stream, ensure_ascii=False, indent=2)
            return path
        except FileExistsError:
            index += 1


def flush_preferences(outbox: Path, destination: Path):
    """Deliver queued documents. Destination failure leaves the local copy intact."""
    delivered = []
    for path in sorted(outbox.glob("preferences_*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(document, dict):
                continue
            # A damaged local queue must not abort the next save session or
            # create an untraceable delivery that cannot be reconciled later.
            date.fromisoformat(document["updated"])
            if not isinstance(document.get("session_id"), str) or not document["session_id"]:
                continue
        except (OSError, ValueError, KeyError, TypeError):
            # Isolate a broken local entry; unrelated sessions can still ship.
            # Destination/readback failures below still stop delivery safely.
            continue
        try:
            matches = []
            for existing in destination.glob("preferences_*.json"):
                if existing.name == "preferences_seed.json":
                    continue
                existing_doc = json.loads(existing.read_text(encoding="utf-8"))
                if not isinstance(existing_doc, dict):
                    raise ValueError("UNKNOWN: unsupported preference document")
                if document.get("session_id") and existing_doc.get("session_id") == document["session_id"]:
                    matches.append(existing)
            if len(matches) > 1:
                break
            if matches:
                if json.loads(matches[0].read_text(encoding="utf-8")) != document:
                    break
                target = matches[0]
            else:
                target = write_preferences(destination, document)
            # If cleanup fails, retain the queue entry. Next time the session ID
            # readback above confirms delivery without creating a second copy.
            path.unlink()
        except (OSError, ValueError, KeyError, TypeError):
            break
        delivered.append(target)
    return delivered
