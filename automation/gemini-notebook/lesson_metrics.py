#!/usr/bin/env python3
"""research/*.md の件数を数える。標準ライブラリのみ。通信もモデル呼び出しもしない。

字幕全文との突き合わせはしない。字幕ファイルはこのリポジトリに無い。
time_source は新設しない。本文に既にあるラベルだけ数える。ファイルは書かない。
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

CORE5 = (
    "独自要約",
    "動画目次・確認済みタイムライン（チャプター）",
    "詳細技術知識・再利用ノート",
    "主張・一次資料・時刻",
    "限界",
)
EXAMPLE7 = (
    "結論",
    "動画の主張",
    "自分の検索結果",
    "提案",
    "UNKNOWN",
    "不都合な事実",
    "確信度",
)
PRIMARY_HINTS = ("主張", "一次資料", "公式資料", "照合")

DATE_RE = re.compile(r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)")
CHECKED_AT_RE = re.compile(r"checked_at:\s*\"?(20\d{2}-\d{2}-\d{2})")
TIME_SOURCE_RE = re.compile(r"time_source:\s*([A-Za-z0-9_]+)")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
UNKNOWN_BULLET_RE = re.compile(r"^\s*-\s+UNKNOWN\b")
UNKNOWN_FIELD_RE = re.compile(r""":\s*"UNKNOWN"|:\s*UNKNOWN\b""")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
HEADING_RE = re.compile(r"^#{1,3}\s+(.+?)\s*$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def is_youtube(url: str) -> bool:
    host = url.lower()
    return "youtube.com" in host or "youtu.be" in host


def example_hit(heading: str, label: str) -> bool:
    text = heading.strip()
    if label == "結論":
        return text == "結論" or text.startswith("結論（") or text.startswith("結論 ")
    if label == "UNKNOWN":
        return text == "UNKNOWN"
    if label == "提案":
        return text == "提案" or text.startswith("提案（") or text.startswith("提案 ")
    return label in text


def note_has_check_date(lines: list[str]) -> bool:
    for line in lines:
        if CHECKED_AT_RE.search(line):
            return True
        if "確認日" in line and DATE_RE.search(line):
            return True
    return False


def primary_url_counts(lines: list[str]) -> tuple[int, int]:
    in_primary = False
    url_lines = 0
    dated = 0
    for line in lines:
        heading = H2_RE.match(line)
        if heading:
            title = heading.group(1)
            in_primary = any(hint in title for hint in PRIMARY_HINTS)
            continue
        if not in_primary:
            continue
        stripped = line.strip()
        if not (stripped.startswith("-") or stripped.startswith("|")):
            continue
        if stripped.startswith("|---") or set(stripped.replace("|", "").strip()) <= {"-", ":"}:
            continue
        urls = [url.rstrip(".,、。") for url in URL_RE.findall(line)]
        if not any(url and not is_youtube(url) for url in urls):
            continue
        url_lines += 1
        if "確認日" in line or DATE_RE.search(line):
            dated += 1
    return url_lines, dated


def measure(research_dir: Path) -> dict[str, object]:
    paths = sorted(p for p in research_dir.glob("*.md") if p.is_file())
    example_counts = {label: 0 for label in EXAMPLE7}
    time_source: Counter[str] = Counter()
    core5 = 0
    with_check_date = 0
    primary_urls = 0
    primary_dated = 0
    unknown_bullets = 0
    unknown_fields = 0
    notes_without_time_source = 0
    example7_complete = 0

    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        headings = [match.group(1).strip() for match in (HEADING_RE.match(line) for line in lines) if match]
        h2 = [match.group(1).strip() for match in (H2_RE.match(line) for line in lines) if match]
        if all(name in h2 for name in CORE5):
            core5 += 1
        hits = 0
        for label in EXAMPLE7:
            if any(example_hit(heading, label) for heading in headings):
                example_counts[label] += 1
                hits += 1
        if hits == len(EXAMPLE7):
            example7_complete += 1
        if note_has_check_date(lines):
            with_check_date += 1
        url_lines, dated = primary_url_counts(lines)
        primary_urls += url_lines
        primary_dated += dated
        labels = TIME_SOURCE_RE.findall("\n".join(lines))
        if labels:
            time_source.update(labels)
        else:
            notes_without_time_source += 1
        for line in lines:
            if UNKNOWN_BULLET_RE.match(line):
                unknown_bullets += 1
            unknown_fields += len(UNKNOWN_FIELD_RE.findall(line))

    return {
        "notes": len(paths),
        "core5_complete": core5,
        "example7_complete": example7_complete,
        "example7": example_counts,
        "notes_with_check_date": with_check_date,
        "primary_url_lines": primary_urls,
        "primary_url_lines_with_check_date": primary_dated,
        "unknown_bullets": unknown_bullets,
        "unknown_fields": unknown_fields,
        "time_source": dict(sorted(time_source.items())),
        "notes_without_time_source_label": notes_without_time_source,
    }


def render(stats: dict[str, object]) -> str:
    example7 = stats["example7"]
    assert isinstance(example7, dict)
    time_source = stats["time_source"]
    assert isinstance(time_source, dict)
    lines = [
        f"notes={stats['notes']}",
        f"core5_complete={stats['core5_complete']}",
        f"example7_complete={stats['example7_complete']}",
    ]
    for label in EXAMPLE7:
        lines.append(f"example7.{label}={example7[label]}")
    lines.extend(
        [
            f"notes_with_check_date={stats['notes_with_check_date']}",
            f"primary_url_lines={stats['primary_url_lines']}",
            f"primary_url_lines_with_check_date={stats['primary_url_lines_with_check_date']}",
            f"unknown_bullets={stats['unknown_bullets']}",
            f"unknown_fields={stats['unknown_fields']}",
        ]
    )
    if time_source:
        for key, count in time_source.items():
            lines.append(f"time_source.{key}={count}")
    else:
        lines.append("time_source=(none)")
    lines.append(f"notes_without_time_source_label={stats['notes_without_time_source_label']}")
    lines.append("subtitle_quote_check=SKIP")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    root = repo_root()
    research = Path(argv[1]) if len(argv) > 1 else root / "research"
    if not research.is_dir():
        print(f"research dir not found: {research}", file=sys.stderr)
        return 1
    sys.stdout.write(render(measure(research)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
