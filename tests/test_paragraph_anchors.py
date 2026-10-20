#!/usr/bin/env python3
"""Tests for build_transcript_okf_content(paragraph_anchors=...): 段落ごとの時刻目印（既定OFF・オフライン）."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation" / "gemini-notebook"))
import notebook_auto_ingest as nai  # noqa: E402

VID = "vid12345678"
URL = f"https://www.youtube.com/watch?v={VID}"
CUES = [(0.0, 2.0, "最初の発話です。"), (5.0, 7.0, "二つ目の発話。"),
        (61.0, 63.0, "次の段落の発話。"), (3725.5, 3728.0, "三つ目の段落。")]

# paragraph_anchors を追加する前（T11 5dcfd99）の実装が CUES から出した本文。acquired_at だけ日付を伏せてある。
GOLDEN_OFF = """---
okf_version: "0.2"
type: "TRANSCRIPT"
title: "【字幕原文】 テスト動画"
logical_id: "youtube:vid12345678:transcript"
research_logical_id: "youtube:vid12345678:research"
related_research_id: "youtube:vid12345678:research"
video_id: "vid12345678"
resource: "https://www.youtube.com/watch?v=vid12345678"
url: "https://www.youtube.com/watch?v=vid12345678"
canonical_url: "https://www.youtube.com/watch?v=vid12345678"
original_url: "https://www.youtube.com/watch?v=vid12345678"
notebook_source_id: "UNKNOWN"
published_at: "2026-08-19"
language: "ja"
acquired_at: "DATE"
cue_count: 4
has_actual_cues: true
transcript_status: "UNVERIFIED"
transcript_format: "UNTIMED_PARAGRAPHS"
acquisition_method: "YOUTUBE_TIMEDTEXT_API"
tags:
  - "AI技術研究室"
  - "字幕原文"
  - "一次資料"
---

# 【字幕原文】 テスト動画

<!-- ID: AI_VIDEO_TRANSCRIPT_RAW:vid12345678 -->
<!-- HAS_ACTUAL_CUES: True -->
<!-- CUES_COUNT: 4 -->
<!-- LOGICAL_ID: youtube:vid12345678:transcript -->
<!-- RESEARCH_REF: youtube:vid12345678:research -->
<!-- RELATED_RESEARCH_ID: youtube:vid12345678:research -->
<!-- RESOURCE: https://www.youtube.com/watch?v=vid12345678 -->
<!-- CANONICAL_URL: https://www.youtube.com/watch?v=vid12345678 -->
<!-- ORIGINAL_URL: https://www.youtube.com/watch?v=vid12345678 -->
<!-- NOTEBOOK_SOURCE_ID: UNKNOWN -->
- **動画ID**: `vid12345678`
- **資料論理ID**: `youtube:vid12345678:transcript`
- **対応研究ノート論理ID**: `youtube:vid12345678:research`
- **元YouTube URL**: https://www.youtube.com/watch?v=vid12345678
- **動画URL**: https://www.youtube.com/watch?v=vid12345678
- **投稿日時**: 2026-08-19
- **総Cue数**: 4 件
- **検証状態**: UNVERIFIED
- **原文保持規約**: 発話テキストは要約・清書・改変を行わず、取得全量をそのまま記録しています。
- **場面の時刻**: 本文は読みやすさのため時刻を付けていません。場面の時刻リンクは対応研究ノート（`youtube:vid12345678:research`）の根拠側にあります。
- **Notebook UI制限・参照案内**: NotebookLMのUI上ではソース間直接リンクのクリックジャンプができない仕様です。対応する研究ノートを参照する場合は、上記『対応研究ノート論理ID (`youtube:vid12345678:research`)』または『動画ID (`vid12345678`)』をもとに、Notebookのソース一覧から検索・特定してください。

## 字幕全文 (取得全量・時刻なし)

最初の発話です。 二つ目の発話。

次の段落の発話。

三つ目の段落。"""


def build(**kw):
    text = nai.build_transcript_okf_content(VID, URL, "テスト動画", cues=CUES, published_at="2026-08-19", **kw)
    return re.sub(r'acquired_at: "[^"]+"', 'acquired_at: "DATE"', text)


class TestParagraphAnchors(unittest.TestCase):
    def test_off_is_identical_to_the_previous_output(self):
        self.assertEqual(build(), GOLDEN_OFF)
        self.assertEqual(build(paragraph_anchors=False), GOLDEN_OFF)

    def test_on_adds_one_marker_line_per_paragraph_at_the_head(self):
        text = build(paragraph_anchors=True)
        body = text.split("## 字幕全文 (取得全量・時刻なし)\n\n", 1)[1]
        blocks = body.split("\n\n")
        self.assertEqual(blocks, [
            f"▶00:00:00 {URL}&t=0s\n最初の発話です。 二つ目の発話。",
            f"▶00:01:01 {URL}&t=61s\n次の段落の発話。",
            f"▶01:02:05 {URL}&t=3725s\n三つ目の段落。",
        ])
        # 目印のURLは段落ごとに1つだけ。文の途中（本文の行）には入らない。
        for block in blocks:
            marker, _, speech = block.partition("\n")
            self.assertEqual(marker.count("http"), 1)
            self.assertNotIn("http", speech)
            self.assertNotIn("▶", speech)

    def test_on_changes_only_markers_format_and_the_time_note(self):
        on = build(paragraph_anchors=True)
        restored = re.sub(r"^▶\S+ \S+\n", "", on, flags=re.M)
        restored = restored.replace('transcript_format: "UNTIMED_PARAGRAPHS_WITH_ANCHORS"', 'transcript_format: "UNTIMED_PARAGRAPHS"')
        restored = re.sub(r"- \*\*場面の時刻\*\*: [^\n]*", lambda m: re.search(r"- \*\*場面の時刻\*\*: [^\n]*", GOLDEN_OFF).group(0), restored)
        self.assertEqual(restored, GOLDEN_OFF)

    def test_speech_text_is_unchanged_with_anchors(self):
        spoken_off = [t for _, t in nai.cues_to_paragraph_spans(CUES)]
        self.assertEqual(spoken_off, nai.cues_to_paragraphs(CUES))
        on = build(paragraph_anchors=True)
        for p in spoken_off:
            self.assertIn(p, on)

    def test_anchors_are_ignored_without_cues_or_for_the_timestamped_format(self):
        no_cues = nai.build_transcript_okf_content(VID, URL, "t", raw_text="本文だけ", paragraph_anchors=True)
        no_cues_off = nai.build_transcript_okf_content(VID, URL, "t", raw_text="本文だけ")
        norm = lambda s: re.sub(r'acquired_at: "[^"]+"', "", s)
        self.assertEqual(norm(no_cues), norm(no_cues_off))
        self.assertNotIn("▶", no_cues)
        ts = nai.build_transcript_okf_content(VID, URL, "t", cues=CUES, timestamped=True, paragraph_anchors=True)
        self.assertNotIn("▶", ts)
        self.assertIn('transcript_format: "TIMESTAMPED_CUES"', ts)

    def test_paragraph_spans_split_like_before(self):
        spans = nai.cues_to_paragraph_spans(CUES)
        self.assertEqual([s for s, _ in spans], [0.0, 61.0, 3725.5])


if __name__ == "__main__":
    unittest.main()
