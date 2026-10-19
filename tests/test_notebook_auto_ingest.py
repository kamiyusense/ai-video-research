#!/usr/bin/env python3
"""Tests for notebook_auto_ingest.py v3.0."""
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTO_DIR = ROOT / "automation" / "gemini-notebook"

import sys
sys.path.insert(0, str(AUTO_DIR))
import notebook_auto_ingest


class TestNotebookAutoIngest(unittest.TestCase):
    def test_cdp_port_probe(self):
        client = notebook_auto_ingest.CDPClient()
        is_open = client.is_port_open(timeout=0.2)
        self.assertIsInstance(is_open, bool)

    def test_sync_to_drive_notebook_sources(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_research_md = tmp_path / "fake_research.md"
            fake_research_md.write_text("# Fake Research Note\n", encoding="utf-8")

            res = notebook_auto_ingest.sync_to_drive_notebook_sources(
                video_id="testVid1234",
                video_url="https://www.youtube.com/watch?v=testVid1234",
                video_title="テスト動画",
                research_md_path=fake_research_md,
                target_dir=tmp_path / "sync_target",
            )
            self.assertEqual(res["status"], "DRIVE_SYNC_SUCCESS")
            self.assertEqual(len(res["synced_files"]), 3)
            
            files = [Path(f["path"]) for f in res["synced_files"]]
            self.assertTrue(all(f.exists() for f in files))
            self.assertTrue(any(f.name.endswith("_youtube_source.txt") for f in files))
            self.assertTrue(any(f.name.endswith("_research_note.md") for f in files))
            self.assertTrue(any(f.name.endswith("_transcript_okf.md") for f in files))

    def test_ingest_and_verify_readback_pass(self):
        """Mock mode: Both YouTube and Research Note present results in is_full_success=True."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy note", encoding="utf-8")

            res = notebook_auto_ingest.ingest_and_verify_notebook(
                video_id="dummy123456",
                video_url="https://www.youtube.com/watch?v=dummy123456",
                video_title="Dummy Video",
                research_md_path=fake_md,
                mock_cdp=True,
                mock_sources=["dummy123456", "研究ノート_dummy123456"],
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertEqual(res["status"], "NOTEBOOK_REGISTRATION_VERIFIED")
            self.assertTrue(res["is_full_success"])
            self.assertTrue(res["readback"]["youtube_source_found"])
            self.assertTrue(res["readback"]["research_note_found"])

    def test_ingest_and_verify_readback_fail(self):
        """Mock mode: Missing YouTube or Note results in is_full_success=False."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy note", encoding="utf-8")

            res = notebook_auto_ingest.ingest_and_verify_notebook(
                video_id="dummy123456",
                video_url="https://www.youtube.com/watch?v=dummy123456",
                video_title="Dummy Video",
                research_md_path=fake_md,
                mock_cdp=True,
                mock_sources=["unrelated_source_item"],  # Missing target sources
                allow_add=False,
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertNotEqual(res["status"], "NOTEBOOK_REGISTRATION_VERIFIED")
            self.assertFalse(res["is_full_success"])
            self.assertFalse(res["readback"]["youtube_source_found"])
            self.assertFalse(res["readback"]["research_note_found"])

    def test_single_element_with_video_id_does_not_pass_both(self):
        """1つのvideo_id表示または単一要素だけで2ソースPASSにならないこと。"""
        # Case A: Only 1 item containing video_id
        items_single = [{"index": 0, "text": "YouTube Video dummy123456"}]
        yt_found, note_found, yt_idx, note_idx = notebook_auto_ingest.evaluate_sources_independence(
            items_single, "dummy123456", "Dummy Video"
        )
        self.assertTrue(yt_found)
        self.assertFalse(note_found, "Single YouTube item must not satisfy research note")

        # Case B: Only 1 item containing research note
        items_note_only = [{"index": 0, "text": "AI_VIDEO_RESEARCH_NOTE:dummy123456"}]
        yt_found, note_found, yt_idx, note_idx = notebook_auto_ingest.evaluate_sources_independence(
            items_note_only, "dummy123456", "Dummy Video"
        )
        self.assertFalse(yt_found, "Note identifier item must not satisfy YouTube source")
        self.assertTrue(note_found)

        # Case C: Both distinct items present -> PASS
        items_both = [
            {"index": 0, "text": "YouTube Video dummy123456"},
            {"index": 1, "text": "AI_VIDEO_RESEARCH_NOTE:dummy123456"},
        ]
        yt_found, note_found, yt_idx, note_idx = notebook_auto_ingest.evaluate_sources_independence(
            items_both, "dummy123456", "Dummy Video"
        )
        self.assertTrue(yt_found)
        self.assertTrue(note_found)
        self.assertNotEqual(yt_idx, note_idx, "YouTube and Note must be distinct DOM elements")

    def test_youtube_and_note_add_are_distinct_functions(self):
        """YouTube追加と研究ノート追加が別処理・別関数であること。"""
        self.assertTrue(callable(notebook_auto_ingest.add_youtube_source_via_cdp))
        self.assertTrue(callable(notebook_auto_ingest.add_copied_text_source_via_cdp))
        self.assertIsNot(
            notebook_auto_ingest.add_youtube_source_via_cdp,
            notebook_auto_ingest.add_copied_text_source_via_cdp,
        )

    def test_cdp_client_handles_out_of_order_events(self):
        """CDPイベントが先に届いてもmessage id一致レスポンスを取得できること。"""
        class FakeWebSocket:
            def __init__(self, frames):
                self.frames = list(frames)
                self.sent = []

            def connect(self):
                pass

            def send_text(self, text):
                self.sent.append(text)

            def recv_text(self):
                if self.frames:
                    return self.frames.pop(0)
                return ""

            def close(self):
                pass

        # Simulate: Event 1 -> Event 2 -> Command Response with id=1
        frames = [
            json.dumps({"method": "Page.loadEventFired", "params": {"timestamp": 12345}}),
            json.dumps({"method": "Network.requestWillBeSent", "params": {"requestId": "r1"}}),
            json.dumps({"id": 1, "result": {"result": {"type": "string", "value": "SUCCESS_VALUE"}}}),
        ]
        fake_ws = FakeWebSocket(frames)

        client = notebook_auto_ingest.CDPClient()
        fake_tab = {"webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/test"}

        # Patch MinimalWebSocket
        orig_cls = notebook_auto_ingest.MinimalWebSocket
        try:
            notebook_auto_ingest.MinimalWebSocket = lambda h, p, path: fake_ws
            val = client.execute_script_on_tab(fake_tab, "console.log('test')")
            self.assertEqual(val, "SUCCESS_VALUE")
        finally:
            notebook_auto_ingest.MinimalWebSocket = orig_cls

    def test_ingest_adds_missing_sources_conditionally(self):
        """不足しているソースだけが追加され、両方揃っていれば追加が走らないこと。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy note", encoding="utf-8")

            # Case A: Only YouTube exists -> adds Copied text note only
            res_partial_yt = notebook_auto_ingest.ingest_and_verify_notebook(
                video_id="vidA",
                video_url="https://www.youtube.com/watch?v=vidA",
                video_title="Video A",
                research_md_path=fake_md,
                mock_cdp=True,
                mock_sources=["https://www.youtube.com/watch?v=vidA"],
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertEqual(res_partial_yt["status"], "NOTEBOOK_REGISTRATION_VERIFIED")
            self.assertIn("COPIED_TEXT_NOTE_INSERTED", res_partial_yt["actions_taken"])
            self.assertNotIn("YOUTUBE_URL_INSERTED", res_partial_yt["actions_taken"])

            # Case B: Both already exist -> no additions taken
            res_both = notebook_auto_ingest.ingest_and_verify_notebook(
                video_id="vidB",
                video_url="https://www.youtube.com/watch?v=vidB",
                video_title="Video B",
                research_md_path=fake_md,
                mock_cdp=True,
                mock_sources=["https://www.youtube.com/watch?v=vidB", "AI_VIDEO_RESEARCH_NOTE:vidB"],
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertEqual(res_both["status"], "NOTEBOOK_REGISTRATION_VERIFIED")
            self.assertEqual(len(res_both["actions_taken"]), 0, "No actions should be taken when both exist")

    def test_cli_launch_chrome_without_video_id(self):
        """--launch-chrome が video_id なしで引数解析を通ること。"""
        parser = notebook_auto_ingest.build_parser()
        args = parser.parse_args(["--launch-chrome"])
        self.assertTrue(args.launch_chrome)
        self.assertIsNone(args.video_id)

    def test_cli_regular_mode_requires_video_id(self):
        """通常登録モードで video_id なしは安全にエラーとなること。"""
        with self.assertRaises(SystemExit):
            notebook_auto_ingest.main([])

    def test_auto_launch_chrome_called_when_port_closed(self):
        """CDPポートCLOSED時に専用Chrome自動起動処理が呼び出されること。"""
        calls = []
        orig_launch = notebook_auto_ingest.launch_dedicated_chrome
        orig_is_open = notebook_auto_ingest.CDPClient.is_port_open

        try:
            notebook_auto_ingest.launch_dedicated_chrome = lambda **k: (calls.append("LAUNCHED"), {"status": "CHROME_LAUNCHED", "pid": 9999})[1]
            # Simulate: closed at first, then open
            port_states = [False, True]
            notebook_auto_ingest.CDPClient.is_port_open = lambda s, **k: port_states.pop(0) if port_states else True

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                fake_md = tmp_path / "note.md"
                fake_md.write_text("dummy", encoding="utf-8")

                # mock_cdp=False to trigger auto launch check
                res = notebook_auto_ingest.ingest_and_verify_notebook(
                    video_id="testAutoLaunch",
                    video_url="https://www.youtube.com/watch?v=testAutoLaunch",
                    video_title="Auto Launch Test",
                    research_md_path=fake_md,
                    mock_cdp=False,
                    auto_launch_chrome=True,
                    drive_dir=tmp_path / "drive_sync",
                )
                self.assertIn("LAUNCHED", calls, "launch_dedicated_chrome must be called when port is closed")
        finally:
            notebook_auto_ingest.launch_dedicated_chrome = orig_launch
            notebook_auto_ingest.CDPClient.is_port_open = orig_is_open

    def test_blocked_initial_google_login(self):
        """初回未ログイン状態は BLOCKED_INITIAL_GOOGLE_LOGIN 扱いになること。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy", encoding="utf-8")

            res = notebook_auto_ingest.ingest_and_verify_notebook(
                video_id="testLogin",
                video_url="https://www.youtube.com/watch?v=testLogin",
                video_title="Login Test",
                research_md_path=fake_md,
                mock_cdp=True,
                mock_blocked_login=True,
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertEqual(res["readback"]["status"], "BLOCKED_INITIAL_GOOGLE_LOGIN")
            self.assertFalse(res["is_full_success"])


    def test_2_source_okf_evaluation(self):
        """字幕原文OKFと研究ノートOKFの独立存在を検出して is_2_source_okf_verified=True になること。"""
        items = [
            {"index": 0, "text": "YouTube Video testVid999"},
            {"index": 1, "text": "AI_VIDEO_RESEARCH_NOTE:testVid999"},
            {"index": 2, "text": "AI_VIDEO_TRANSCRIPT_RAW:testVid999"},
        ]
        res = notebook_auto_ingest.evaluate_2_source_okf_independence(items, "testVid999", "Test Video 999")
        self.assertTrue(res["youtube_found"])
        self.assertTrue(res["research_note_found"])
        self.assertTrue(res["transcript_source_found"])
        self.assertTrue(res["is_2_source_okf_verified"])
        self.assertEqual(res["research_note_item_index"], 1)
        self.assertEqual(res["transcript_item_index"], 2)

    def test_ingest_and_verify_2_source_okf_success(self):
        """Mock mode: 字幕原文OKFと研究ノートOKFが揃っている場合 SUCCESS_2_SOURCE_OKF になること。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_md = tmp_path / "note.md"
            fake_md.write_text("dummy note", encoding="utf-8")

            res = notebook_auto_ingest.ingest_and_verify_notebook(
                video_id="okfVid123",
                video_url="https://www.youtube.com/watch?v=okfVid123",
                video_title="OKF Video",
                research_md_path=fake_md,
                mock_cdp=True,
                mock_sources=[
                    "AI_VIDEO_RESEARCH_NOTE:okfVid123",
                    "AI_VIDEO_TRANSCRIPT_RAW:okfVid123",
                ],
                drive_dir=tmp_path / "drive_sync",
            )
            self.assertEqual(res["status"], "SUCCESS_2_SOURCE_OKF")
            self.assertTrue(res["is_full_success"])
            self.assertTrue(res["is_2_source_okf_verified"])
            self.assertTrue(res["readback"]["research_note_found"])
            self.assertTrue(res["readback"]["transcript_source_found"])


    def test_infer_semantic_related_records(self):
        """動画内容から意味付き関連リンク（CANDIDATE）が客観的根拠付きで動的推論されること。"""
        import auto_research_pipeline

        # Test Case 1: OKF and RAG keywords present
        rels = auto_research_pipeline.infer_semantic_related_records(
            video_id="newVid123",
            title="OKFによる知識管理とRAG探索の最前線",
            summary_ja="オープンナレッジ形式(OKF)で資料を構造化し、RAG検索を最適化する手法。",
            detailed_findings_ja="【詳細】荷札による体系化とベクトル検索のハイブリッド探索。",
        )
        target_ids = [r["target_id"] for r in rels]
        self.assertIn("youtube:u3ka_AAb8qE", target_ids)
        self.assertIn("youtube:pRfC1DILDEM", target_ids)
        for r in rels:
            self.assertEqual(r["status"], "CANDIDATE")
            self.assertTrue(r["evidence"].startswith("キーワード一致:"))

        # Test Case 2: Self-link prevention
        rels_self = auto_research_pipeline.infer_semantic_related_records(
            video_id="u3ka_AAb8qE",
            title="OKF解説動画",
            summary_ja="OKFの概要",
        )
        self.assertNotIn("youtube:u3ka_AAb8qE", [r["target_id"] for r in rels_self])

    def test_build_transcript_okf_content(self):
        """字幕原文OKFのYAMLフロントマターおよびコメントヘッダーに所定のプロパティが含まれること。"""
        cues = [
            {"start": 0.0, "duration": 2.5, "text": "こんにちは世界"},
            {"start": 2.5, "duration": 3.0, "text": "テスト字幕です"},
        ]
        content = notebook_auto_ingest.build_transcript_okf_content(
            video_id="abc123xyz",
            video_url="https://www.youtube.com/watch?v=abc123xyz",
            video_title="テスト動画タイトル",
            cues=cues,
            language="ja",
        )
        self.assertIn('logical_id: "youtube:abc123xyz:transcript"', content)
        self.assertIn('research_logical_id: "youtube:abc123xyz:research"', content)
        self.assertIn('related_research_id: "youtube:abc123xyz:research"', content)
        self.assertIn('resource: "https://www.youtube.com/watch?v=abc123xyz"', content)
        self.assertIn('url: "https://www.youtube.com/watch?v=abc123xyz"', content)
        self.assertIn('canonical_url: "https://www.youtube.com/watch?v=abc123xyz"', content)
        self.assertIn('original_url: "https://www.youtube.com/watch?v=abc123xyz"', content)
        self.assertIn('type: "TRANSCRIPT"', content)
        self.assertIn('transcript_status: "UNVERIFIED"', content)
        self.assertIn('<!-- RELATED_RESEARCH_ID: youtube:abc123xyz:research -->', content)
        self.assertIn('- **元YouTube URL**: https://www.youtube.com/watch?v=abc123xyz', content)
        self.assertIn('- **[00:00]** (0.0s) こんにちは世界', content)
        self.assertIn('- **[00:02]** (2.5s) テスト字幕です', content)


if __name__ == "__main__":
    unittest.main()
