#!/usr/bin/env python3
"""Tests for build_transcript_okf_content(paragraph_anchors=...): 段落ごとの時刻目印（運用の既定ON・オフライン）."""
import io
import json
import re
import socket
import sys
import unittest
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation" / "gemini-notebook"))
import notebook_auto_ingest as nai  # noqa: E402
import notebooklm_py_ingest as ing  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import branch_pin  # noqa: E402

VID = "vid12345678"
URL = f"https://www.youtube.com/watch?v={VID}"
CUES = [(0.0, 2.0, "最初の発話です。"), (5.0, 7.0, "二つ目の発話。"),
        (61.0, 63.0, "次の段落の発話。"), (3725.5, 3728.0, "三つ目の段落。")]

# T12（c36978e）時点の実装が CUES から出した本文。acquired_at だけ日付を伏せてある。T13 の変更前の形。
GOLDEN_OFF_T12 = """---
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

# T13: v2.0 §3.1 に合わせた意図的な出力変更。本文先頭の見える2行（`ID: AI_VIDEO_TRANSCRIPT_RAW:<id>` と `動画: <URL>`）だけを
# 足す。HTMLコメントはNotebookの読み戻しで消えるため、識別子とURLを見える行でも持たせる。他の行は変えない。
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

ID: AI_VIDEO_TRANSCRIPT_RAW:vid12345678
動画: https://www.youtube.com/watch?v=vid12345678
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
    def test_visible_id_and_url_lines_are_the_only_change_from_t12(self):
        want = GOLDEN_OFF_T12.replace(
            "# 【字幕原文】 テスト動画\n\n",
            "# 【字幕原文】 テスト動画\n\nID: AI_VIDEO_TRANSCRIPT_RAW:vid12345678\n動画: " + URL + "\n", 1)
        self.assertEqual(GOLDEN_OFF, want)
        added = set(GOLDEN_OFF.splitlines()) - set(GOLDEN_OFF_T12.splitlines())
        self.assertEqual(added, {"ID: AI_VIDEO_TRANSCRIPT_RAW:vid12345678", "動画: " + URL})
        self.assertEqual(len(GOLDEN_OFF.splitlines()), len(GOLDEN_OFF_T12.splitlines()) + 2)

    def test_visible_lines_come_first_in_the_body_and_survive_comment_stripping(self):
        body = build().split("\n---\n", 1)[1]
        stripped = re.sub(r"<!--.*?-->", "", body)   # Notebookの読み戻しはHTMLコメントを消す
        visible = [ln for ln in stripped.splitlines() if ln.strip()][:3]
        self.assertEqual(visible[1:], ["ID: AI_VIDEO_TRANSCRIPT_RAW:vid12345678", "動画: " + URL])

    def test_off_is_identical_to_the_previous_output(self):
        self.assertEqual(build(), GOLDEN_OFF)
        self.assertEqual(build(paragraph_anchors=False), GOLDEN_OFF)

    def test_on_adds_one_marker_line_per_paragraph_at_the_head(self):
        text = build(paragraph_anchors=True)
        body = text.split("## 字幕全文 (取得全量・段落先頭に時刻目印)\n\n", 1)[1]
        blocks = body.split("\n\n")
        self.assertEqual(blocks, [
            f"[00:00:00] {URL}&t=0s\n最初の発話です。 二つ目の発話。",
            f"[00:01:01] {URL}&t=61s\n次の段落の発話。",
            f"[01:02:05] {URL}&t=3725s\n三つ目の段落。",
        ])
        # 目印のURLは段落ごとに1つだけ。文の途中（本文の行）には入らない。
        for block in blocks:
            marker, _, speech = block.partition("\n")
            self.assertEqual(marker.count("http"), 1)
            self.assertNotIn("http", speech)
            self.assertIsNone(nai.ANCHOR_LINE_RE.search(speech))
            self.assertNotIn("▶", marker)   # 旧形式は作らない

    def test_anchor_lines_follow_the_fixed_format_and_sit_at_paragraph_heads(self):
        """RUNBOOK「目印行の形式」の仕様：`[HH:MM:SS] <URL>&t=<秒>s` を約1分ごとの段落の先頭に1行だけ。"""
        cues = [(float(t), float(t) + 8.0, f"発話{t}。") for t in range(0, 400, 10)]
        text = nai.build_transcript_okf_content(VID, URL, "t", cues=cues, paragraph_anchors=True)
        body = text.split("## 字幕全文 (取得全量・段落先頭に時刻目印)\n\n", 1)[1]
        paragraphs = body.split("\n\n")
        self.assertEqual(len(paragraphs), len(nai.cues_to_paragraphs(cues)))
        starts = []
        for para in paragraphs:
            first, _, rest = para.partition("\n")
            m = nai.ANCHOR_LINE_RE.match(first)
            self.assertIsNotNone(m, first)
            _old, _new, h, mi, se, link, secs = m.groups()
            self.assertIsNone(_old)   # 出力は新形式だけ
            self.assertEqual(_new, "[")
            self.assertEqual(int(h) * 3600 + int(mi) * 60 + int(se), int(secs))
            self.assertEqual(link, f"{URL}&t={secs}s")
            self.assertIsNone(nai.ANCHOR_LINE_RE.search(rest))          # 段落の途中には入れない
            self.assertNotIn("▶", para)
            starts.append(int(secs))
        self.assertEqual(len(nai.ANCHOR_LINE_RE.findall(body)), len(paragraphs))
        self.assertTrue(all(b - a >= 60 for a, b in zip(starts, starts[1:])), starts)   # 約1分ごと
        self.assertTrue(nai.has_paragraph_anchors(body))
        self.assertFalse(nai.has_paragraph_anchors(build()))   # 目印なし形式には無い
        self.assertTrue(nai.has_paragraph_anchors("[00:01:05]\n\nhttps://www.youtube.com/watch?v=x&t=65s"))   # 読み戻しの揺れは許す
        self.assertTrue(nai.has_paragraph_anchors("▶ 00:01:05\n\nhttps://www.youtube.com/watch?v=x&t=65s"))

    def test_on_changes_only_markers_format_and_the_time_note(self):
        on = build(paragraph_anchors=True)
        restored = re.sub(r"^\[\S+\] \S+\n", "", on, flags=re.M)
        restored = restored.replace('transcript_format: "PARAGRAPHS_WITH_ANCHORS"', 'transcript_format: "UNTIMED_PARAGRAPHS"')
        restored = restored.replace("## 字幕全文 (取得全量・段落先頭に時刻目印)", "## 字幕全文 (取得全量・時刻なし)")
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
        self.assertIsNone(nai.ANCHOR_LINE_RE.search(no_cues))
        ts = nai.build_transcript_okf_content(VID, URL, "t", cues=CUES, timestamped=True, paragraph_anchors=True)
        self.assertIsNone(nai.ANCHOR_LINE_RE.search(ts))
        self.assertIn('transcript_format: "TIMESTAMPED_CUES"', ts)

    def test_paragraph_spans_split_like_before(self):
        spans = nai.cues_to_paragraph_spans(CUES)
        self.assertEqual([s for s, _ in spans], [0.0, 61.0, 3725.5])


class TestBothAnchorFormsAreAccepted(unittest.TestCase):
    """T16: 出力は実機の `[HH:MM:SS] URL` の1形式。読み取り（正規表現・目印の有無・読み戻し一致）は旧 `▶HH:MM:SS URL` も受け入れる。"""

    def test_builder_emits_only_the_real_machine_form(self):
        self.assertEqual(nai.anchor_line(VID, 312.9), f"[00:05:12] {URL}&t=312s")
        self.assertEqual(nai.anchor_line(VID, 3725), f"[01:02:05] {URL}&t=3725s")
        self.assertNotIn("▶", build(paragraph_anchors=True))

    def test_regex_accepts_both_forms_and_reads_the_same_seconds(self):
        new = nai.ANCHOR_LINE_RE.match(f"[00:05:12] {URL}&t=312s")
        old = nai.ANCHOR_LINE_RE.match(f"▶00:05:12 {URL}&t=312s")
        for m in (new, old):
            self.assertIsNotNone(m)
            self.assertEqual(m.groups()[2:], ("00", "05", "12", f"{URL}&t=312s", "312"))
        # 混ざった形・閉じ忘れ・時刻とURLの間に空白がない形は目印行ではない
        for bad in (f"[00:05:12 {URL}&t=312s", f"▶00:05:12] {URL}&t=312s", f"[00:05:12]{URL}&t=312s",
                    f"[00:05:12] {URL}&t=312", f"- [00:05:12]({URL}&t=312s) 発話"):
            self.assertIsNone(nai.ANCHOR_LINE_RE.match(bad), bad)

    def test_has_paragraph_anchors_accepts_both_forms_and_reflowed_readbacks(self):
        for body in (f"[00:05:12] {URL}&t=312s\n本文", f"▶00:05:12 {URL}&t=312s\n本文",
                     f"[00:05:12]\n\n{URL}&t=312s\n\n本文", f"▶ 00:05:12\n\n{URL}&t=312s\n\n本文",
                     f"00:05:12\n\n{URL}&t=312s\n\n本文"):
            self.assertTrue(nai.has_paragraph_anchors(body), body)
        # 時刻リンク（旧・発話ごとの形式／研究ノートの根拠）と、時刻のない本文は目印に数えない
        self.assertFalse(nai.has_paragraph_anchors(f"- [00:05:12]({URL}&t=312s) 発話"))
        self.assertFalse(nai.has_paragraph_anchors(f"{URL}&t=312s 本文だけ"))
        self.assertFalse(nai.has_paragraph_anchors(""))
        self.assertFalse(nai.has_paragraph_anchors(None))

    def test_readback_matches_across_the_two_forms(self):
        """旧形式で登録した字幕が新形式の期待本文と記号・空白を除いて一致する（その逆も）。"""
        cues = [(0.0, 1.0, "最初"), (70.0, 71.0, "次の段落")]
        new = ing.build_transcript_text(VID, "t", cues, "2026-10-01")["text"]
        old = re.sub(r"^\[(\S+)\] ", r"▶\1 ", new, flags=re.M)
        self.assertNotEqual(old, new)
        self.assertTrue(ing.readback_matches(new, old)["match"])
        self.assertTrue(ing.readback_matches(old, new)["match"])
        self.assertFalse(ing.readback_matches(new, old.replace("次の段落", "別の段落"))["match"])


class FakeClient:
    def __init__(self):
        self.add_calls = []

    def auth_check_passive(self):
        return True

    def list_sources(self):
        return []

    def get_fulltext(self, source_id):
        return ""

    def add_text(self, title, text):
        self.add_calls.append((title, text))
        raise AssertionError("dry-run中に書き込まれた")


NOTE = "# 研究ノート\n\n本文\n"


def plan(**kw):
    return ing.run_ingest(FakeClient(), VID, "テスト動画", NOTE, cues=CUES, published_at="2026-08-19", **kw)


def transcript_text(res):
    """dry-run の計画には本文を載せないので、同じ入力から組み立てた本文で確かめる。"""
    return ing.build_transcript_text(VID, "テスト動画", CUES, "2026-08-19", paragraph_anchors=res["paragraph_anchors"])["text"]


class TestParagraphAnchorsWiring(unittest.TestCase):
    """paragraph_anchors を run_ingest / pipeline / CLI から切り替えられる（既定ON。既定は1か所の定数で切り替える）."""

    def setUp(self):
        for target, name in ((urllib.request, "urlopen"), (socket, "create_connection")):
            p = mock.patch.object(target, name, side_effect=AssertionError("network"))
            p.start()
            self.addCleanup(p.stop)
        import auto_research_pipeline as arp
        branch_pin.pin_target_branch(self, arp)      # 実リポジトリの今の枝には依存しない

    def test_default_is_on_and_explicit_off_wins(self):
        """相棒の決定（2026-10-20 02:37 JST）で既定ON。--no-paragraph-anchors / paragraph_anchors=False は常に優先する。"""
        self.assertIs(ing.DEFAULT_PARAGRAPH_ANCHORS, True)
        self.assertIs(plan()["paragraph_anchors"], True)
        self.assertIs(plan(paragraph_anchors=None)["paragraph_anchors"], True)
        self.assertIs(plan(paragraph_anchors=False)["paragraph_anchors"], False)
        self.assertIn("[00:00:00] ", transcript_text(plan()))
        with mock.patch.object(ing, "DEFAULT_PARAGRAPH_ANCHORS", False):
            self.assertIs(plan()["paragraph_anchors"], False)             # 既定の定数だけで全経路が切り替わる
            self.assertIs(plan(paragraph_anchors=True)["paragraph_anchors"], True)

    def test_dry_run_plan_shows_which_one_and_the_text_follows(self):
        for flag in (False, True):
            res = plan(paragraph_anchors=flag)
            self.assertEqual(res["status"], "DRY_RUN_PLAN")
            self.assertIs(res["paragraph_anchors"], flag)
            self.assertEqual("[00:00:00] " in transcript_text(res), flag)
        offline = ing.run_ingest(None, VID, "テスト動画", NOTE, paragraph_anchors=True)
        self.assertEqual((offline["status"], offline["paragraph_anchors"]), ("DRY_RUN_PLAN_OFFLINE", True))

    def test_live_write_uses_the_selected_form(self):
        class Writer(FakeClient):
            def __init__(self):
                super().__init__()
                self.bodies, self.sources = {}, []

            def list_sources(self):
                return [{"id": k, "type": "text", "title": t} for k, (t, _) in self.bodies.items()]

            def get_fulltext(self, sid):
                return self.bodies[sid][1]

            def add_text(self, title, text):
                sid = f"s{len(self.bodies)}"
                self.bodies[sid] = (title, text)
                return sid

        for flag in (False, True):
            c = Writer()
            ing.run_ingest(c, VID, "テスト動画", NOTE, cues=CUES, published_at="2026-08-19", live=True,
                           notebook_id="nb-1", paragraph_anchors=flag)
            texts = [t for ttl, t in c.bodies.values() if "字幕原文" in ttl]
            self.assertEqual(len(texts), 1)
            self.assertEqual("[01:02:05] " in texts[0], flag)

    def test_ingest_cli_flag(self):
        note = ROOT / "research" / "2026-10-10-BStkW1HTfmk-obsidian-preliminary.md"
        for argv, want in (([], None), (["--paragraph-anchors"], True), (["--no-paragraph-anchors"], False)):
            seen = {}

            def fake(client, **kw):
                seen.update(kw)
                return {"status": "DRY_RUN_PLAN_OFFLINE"}

            with mock.patch.object(ing, "run_ingest", fake), redirect_stdout(io.StringIO()):
                rc = ing.main(["--video-id", VID, "--video-title", "t", "--research-md", str(note)] + argv)
            self.assertEqual(rc, 0)
            self.assertIs(seen["paragraph_anchors"], want)

    def test_pipeline_cli_and_dry_run_show_the_choice(self):
        import auto_research_pipeline as arp
        url = f"https://www.youtube.com/watch?v={VID}"
        for argv, want in (([], None), (["--paragraph-anchors"], True), (["--no-paragraph-anchors"], False)):
            seen = {}

            def fake_run(*a, **kw):
                seen.update(kw)
                return {"status": "DRY_RUN_PLAN"}

            with mock.patch.object(arp, "run_pipeline", fake_run), redirect_stdout(io.StringIO()):
                self.assertEqual(arp.main([url] + argv), 0)
            self.assertIs(seen["paragraph_anchors"], want)

        for flag, expect in ((None, True), (False, False)):
            out = io.StringIO()
            with redirect_stdout(out):
                res = arp.run_pipeline(url, dry_run=True, notebook_backend="notebooklm-py", notebook_id="nb-1",
                                       notebook_client=FakeClient(), fetch_video_meta=lambda v: {},
                                       fetch_transcript=lambda v: {"cues": CUES, "published_at": "2026-08-19"},
                                       paragraph_anchors=flag)
            self.assertEqual(res["status"], "DRY_RUN_PLAN")
            self.assertIs(res["notebook_ingest"]["paragraph_anchors"], expect)
            self.assertIn(f"字幕の段落目印（[HH:MM:SS]）: {'ON' if expect else 'OFF'}", out.getvalue())
            self.assertEqual(res["notebook_ingest"]["writes"], [])


if __name__ == "__main__":
    unittest.main()
