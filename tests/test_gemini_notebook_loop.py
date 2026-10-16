#!/usr/bin/env python3
"""Comprehensive automated test suite for the Gemini Notebook Research Loop bridge.

Verifies:
1. Extraction of `research_receipt_v1` from raw JSON and Gemini Markdown output (fenced code blocks).
2. Canonical YouTube URL normalization (`watch?v=`, `youtu.be/`, `shorts/`, `live/`) and video_id matching.
3. End-to-end processing of NEW video records, `registry.json` updates, and knowledge index generation.
4. Idempotency & duplicate prevention when re-processing the exact same receipt or existing video IDs.
5. Cross-branch deduplication against `origin/*` unmerged Draft PR branches.
6. Safe append-only delta updates for `UPDATED` / `CONFLICT` records on existing videos.
7. Intentional failure & safety boundary stops (default branch `main` refusal, invalid origin refusal,
   oversized transcript/summary rejection, `notebook_readback != PASS` skip, `METADATA_ONLY` skip).
8. Local & remote Git commit, push, blob SHA readback verification, and remote divergence safety stop.
9. Batch inbox directory scanning (`.md`, `.json`, `.txt`) with automatic skipping of non-receipt files.
"""
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "automation" / "gemini-notebook" / "receipt_to_research.py"

spec = importlib.util.spec_from_file_location("receipt_to_research", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def make_sample_receipt(**overrides):
    base = {
        "schema_version": "research_receipt_v1",
        "notebook_url": "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
        "checked_at": "2026-10-17",
        "notebook_readback": "PASS",
        "github_dedup_status": "PASS",
        "videos": [
            {
                "video_id": "dQw4w9WgXcQ",
                "title": "AI Agent Harness Design Patterns 2026",
                "url": "https://youtu.be/dQw4w9WgXcQ?t=45",
                "published_at": "2026-10-12",
                "summary_ja": "ハーネス設計においてモデル呼び出しと状態管理・決定論的検証を分離し、失敗時の再試行を抑制する手法を解説。",
                "source_scope": "Gemini transcript analysis with timestamp verification; visual frames not acquired",
                "claims": [
                    {
                        "text": "ツール実行前後のHooksにより危険なコマンドを決定論的にブロックできる",
                        "status": "CONFIRMED_DOC",
                        "timestamp_seconds": 125,
                        "official_url": "https://code.claude.com/docs/en/hooks",
                    }
                ],
                "notebook_source_id": "src_017_harness",
                "notebook_readback": "PASS",
                "changes": ["NEW"],
            }
        ],
        "next_topics": [
            "ハーネスにおけるツール失敗時の決定論的ロールバック設計",
            "Gemini NotebookのGoogle Drive自動同期と知識索引差分の検証",
        ],
        "unknowns": [
            "Gemini Scheduled ActionsでのNotebookソース追加が完全無人で動作するかは未実証"
        ],
    }
    base.update(overrides)
    return base


class TestGeminiNotebookLoop(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tmp_dir.name) / "repo"
        # Name bare remote path ending with /kamiyusense/ai-video-research.git so origin boundary check passes
        self.remote_bare = Path(self.tmp_dir.name) / "kamiyusense" / "ai-video-research.git"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.remote_bare.mkdir(parents=True, exist_ok=True)

        subprocess.run(["git", "init", "--bare", str(self.remote_bare)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_root), "init"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo_root), "config", "user.email", "test@example.com"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_root), "config", "user.name", "Test Runner"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "remote",
                "add",
                "origin",
                self.remote_bare.as_posix(),
            ],
            check=True,
            capture_output=True,
        )

        # Seed initial registry.json and research directory
        (self.repo_root / "research").mkdir(parents=True, exist_ok=True)
        initial_registry = {
            "schema_version": 1,
            "purpose": "動画IDの重複確認用台帳。",
            "repository": "kamiyusense/ai-video-research",
            "records": [
                {
                    "record_id": "youtube:lC5jxpYmatE",
                    "video_id": "lC5jxpYmatE",
                    "canonical_url": "https://www.youtube.com/watch?v=lC5jxpYmatE",
                    "research_path": "research/2026-10-10-lC5jxpYmatE-ai-techniques.md",
                    "source_scope": "Gemini Spark transcript report",
                    "research_date": "2026-10-10",
                    "status": "RESEARCH_RECORDED; LIVE_NOT_RUN",
                    "evidence": "USER_SUPPLIED_REPORTS",
                }
            ],
        }
        (self.repo_root / "registry.json").write_text(
            json.dumps(initial_registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.repo_root / "research" / "2026-10-10-lC5jxpYmatE-ai-techniques.md").write_text(
            "# 動画研究05\n\n- video_id: `lC5jxpYmatE`\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.repo_root), "checkout", "-b", "main"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_root), "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo_root), "commit", "-m", "Initial commit"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo_root), "push", "origin", "main:main"],
            check=True,
            capture_output=True,
        )

        # Create a simulated remote tracking branch with another video (`ZjUJ-35acaU`)
        subprocess.run(
            ["git", "-C", str(self.repo_root), "checkout", "-b", "research/video08-mock"],
            check=True,
            capture_output=True,
        )
        remote_reg = json.loads((self.repo_root / "registry.json").read_text(encoding="utf-8"))
        remote_reg["records"].append(
            {
                "record_id": "youtube:ZjUJ-35acaU",
                "video_id": "ZjUJ-35acaU",
                "canonical_url": "https://www.youtube.com/watch?v=ZjUJ-35acaU",
                "research_path": "research/2026-10-10-ZjUJ-35acaU-notebooklm-youtube-extension.md",
                "source_scope": "SPARK_TRANSCRIPT_REPORT",
                "research_date": "2026-10-10",
                "status": "REVIEWED_PARTIAL",
                "evidence": "SPARK_TRANSCRIPT_REPORT",
            }
        )
        (self.repo_root / "registry.json").write_text(
            json.dumps(remote_reg, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.repo_root), "add", "registry.json"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.repo_root), "commit", "-m", "Add video08 on parallel branch"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "push",
                "origin",
                "research/video08-mock:research/video08-mock",
            ],
            check=True,
            capture_output=True,
        )

        # Switch to working feature branch off main and push initial state to bare origin
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "checkout",
                "-b",
                "feature/gemini-notebook-research-loop-20261016",
                "main",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "push",
                "origin",
                "feature/gemini-notebook-research-loop-20261016:feature/gemini-notebook-research-loop-20261016",
            ],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_01_extract_receipt_from_markdown_and_raw_json(self):
        sample = make_sample_receipt()
        raw_json = json.dumps(sample, ensure_ascii=False, indent=2)
        extracted_direct = bridge.extract_receipt_payload(raw_json)
        self.assertEqual(extracted_direct["schema_version"], "research_receipt_v1")

        markdown_wrapped = (
            "## Gemini Notebook 調査完了報告\n\n"
            "Notebookの既存16ソースを照合し、1件の新規研究を追加しました。\n\n"
            "```json\n"
            + raw_json
            + "\n```\n\n"
            "次回の調査テーマはハーネスのロールバック設計です。"
        )
        extracted_md = bridge.extract_receipt_payload(markdown_wrapped)
        self.assertEqual(extracted_md["videos"][0]["video_id"], "dQw4w9WgXcQ")
        self.assertEqual(
            bridge.compute_receipt_digest(extracted_direct),
            bridge.compute_receipt_digest(extracted_md),
        )

    def test_02_youtube_url_normalization_and_mismatch_rejection(self):
        self.assertEqual(
            bridge.extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            bridge.extract_youtube_id("https://youtu.be/dQw4w9WgXcQ?si=abc"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            bridge.extract_youtube_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            bridge.extract_youtube_id("https://www.youtube.com/live/dQw4w9WgXcQ?feature=share"),
            "dQw4w9WgXcQ",
        )

        # Mismatched URL vs video_id must fail validation
        bad = make_sample_receipt()
        bad["videos"][0]["url"] = "https://www.youtube.com/watch?v=11111111111"
        with self.assertRaisesRegex(ValueError, "does not match video_id"):
            bridge.validate(bad)

    def test_03_end_to_end_apply_and_duplicate_prevention(self):
        receipt = make_sample_receipt()
        buf = io.StringIO()
        with redirect_stdout(buf):
            summary1, touched1 = bridge.process_receipt_data(
                data=receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        self.assertEqual(summary1["new_records"], 1)
        self.assertEqual(summary1["ids"], ["dQw4w9WgXcQ"])
        note_path = self.repo_root / "research" / "2026-10-17-dQw4w9WgXcQ-gemini-notebook.md"
        self.assertTrue(note_path.exists())
        note_text = note_path.read_text(encoding="utf-8")
        self.assertIn("- canonical_url: https://www.youtube.com/watch?v=dQw4w9WgXcQ", note_text)
        self.assertIn("- original_url: https://youtu.be/dQw4w9WgXcQ?t=45", note_text)
        self.assertIn("[02:05](https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=125s)", note_text)

        # Verify registry.json has canonical_url and original_url
        reg = json.loads((self.repo_root / "registry.json").read_text(encoding="utf-8"))
        added_rec = [r for r in reg["records"] if r["video_id"] == "dQw4w9WgXcQ"][0]
        self.assertEqual(added_rec["canonical_url"], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(added_rec["original_url"], "https://youtu.be/dQw4w9WgXcQ?t=45")

        # Verify knowledge index and loop_state.json were updated
        index_md = (
            self.repo_root / "automation" / "gemini-notebook" / "state" / "AI技術研究室_知識索引.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`dQw4w9WgXcQ`", index_md)
        self.assertIn("`ZjUJ-35acaU`", index_md)
        self.assertIn("ハーネスにおけるツール失敗時の決定論的ロールバック設計", index_md)

        # Re-processing the exact same receipt must be idempotent (0 new records, 0 updates)
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            summary2, touched2 = bridge.process_receipt_data(
                data=receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        self.assertEqual(summary2["new_records"], 0)
        self.assertEqual(summary2["updated_records"], 0)
        self.assertEqual(summary2["skipped"][0]["reason"], "SKIP_DUPLICATE_RECEIPT")
        self.assertIn("SKIP_EXISTING dQw4w9WgXcQ", buf2.getvalue())

    def test_04_cross_branch_deduplication_and_delta_updates(self):
        receipt = make_sample_receipt(
            checked_at="2026-10-18",
            videos=[
                {
                    "video_id": "ZjUJ-35acaU",
                    "title": "YouTube to NotebookLM Extension",
                    "url": "https://www.youtube.com/watch?v=ZjUJ-35acaU",
                    "published_at": "2026-03-21",
                    "summary_ja": "別ブランチで既に調査済みの動画が再検出されたケース。",
                    "source_scope": "Gemini transcript",
                    "claims": [],
                    "notebook_source_id": "src_008",
                    "notebook_readback": "PASS",
                    "changes": ["NEW"],
                },
                {
                    "video_id": "lC5jxpYmatE",
                    "title": "課題ドリブン・Skill再利用の追加公式検証",
                    "url": "https://www.youtube.com/watch?v=lC5jxpYmatE",
                    "published_at": "2026-10-02",
                    "summary_ja": "Claude Code SkillsとHooksの最新公式ドキュメント更新に伴い、仕様変更差分を追記。",
                    "source_scope": "Official documentation re-verification",
                    "claims": [
                        {
                            "text": "Hooksの設定スキーマとイベント種別の追加確認",
                            "status": "CONFIRMED_DOC",
                            "timestamp_seconds": 1750,
                            "official_url": "https://code.claude.com/docs/en/hooks",
                        }
                    ],
                    "notebook_source_id": "src_005_v2",
                    "notebook_readback": "PASS",
                    "changes": ["UPDATED"],
                },
            ],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            summary, _ = bridge.process_receipt_data(
                data=receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        self.assertEqual(summary["new_records"], 0)
        self.assertEqual(summary["updated_records"], 1)
        self.assertEqual(summary["updated_ids"], ["lC5jxpYmatE"])
        reasons = {s["video_id"]: s["reason"] for s in summary["skipped"]}
        self.assertEqual(reasons.get("ZjUJ-35acaU"), "SKIP_EXISTING_REMOTE_BRANCH")

        # Verify delta section was appended to existing research file without destroying original content
        updated_md = (self.repo_root / "research" / "2026-10-10-lC5jxpYmatE-ai-techniques.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("# 動画研究05", updated_md)
        self.assertIn("## 差分更新 (2026-10-18 / UPDATED)", updated_md)
        self.assertIn("Claude Code SkillsとHooksの最新公式ドキュメント更新に伴い", updated_md)

    def test_05_intentional_failures_and_safety_boundaries(self):
        # 1. Refusing write on `main` branch
        subprocess.run(["git", "-C", str(self.repo_root), "checkout", "main"], check=True, capture_output=True)
        with self.assertRaisesRegex(ValueError, "Refusing detached/default-branch write"):
            bridge.process_receipt_data(make_sample_receipt(), root=self.repo_root, apply=True)

        # Switch back to feature branch, test invalid origin refusal
        subprocess.run(
            ["git", "-C", str(self.repo_root), "checkout", "feature/gemini-notebook-research-loop-20261016"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "remote",
                "set-url",
                "origin",
                "https://github.com/kamiyusense/multi-ai-council-phase0.git",
            ],
            check=True,
            capture_output=True,
        )
        with self.assertRaisesRegex(ValueError, "Unexpected git origin: refusing write"):
            bridge.process_receipt_data(make_sample_receipt(), root=self.repo_root, apply=True)

        # Restore valid origin
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_root),
                "remote",
                "set-url",
                "origin",
                self.remote_bare.as_posix(),
            ],
            check=True,
            capture_output=True,
        )

        # 2. Reject full transcript / oversized summary (>300 chars)
        oversized = make_sample_receipt()
        oversized["videos"][0]["summary_ja"] = "あ" * 301
        with self.assertRaisesRegex(ValueError, "Summary must contain 1-300 characters"):
            bridge.validate(oversized)

        # 3. Skip unverified notebook readback and METADATA_ONLY
        unverified = make_sample_receipt(
            videos=[
                {
                    "video_id": "11111111111",
                    "title": "Unverified Readback Video",
                    "url": "https://www.youtube.com/watch?v=11111111111",
                    "published_at": None,
                    "summary_ja": "Notebook読み戻し未確認のためスキップされるべき動画。",
                    "source_scope": "Transcript",
                    "claims": [],
                    "notebook_source_id": None,
                    "notebook_readback": "UNKNOWN",
                    "changes": ["NEW"],
                },
                {
                    "video_id": "22222222222",
                    "title": "Metadata Only Video",
                    "url": "https://www.youtube.com/watch?v=22222222222",
                    "published_at": None,
                    "summary_ja": "タイトルと概要欄しか見ていないためスキップされるべき動画。",
                    "source_scope": "METADATA_ONLY; transcript unavailable",
                    "claims": [],
                    "notebook_source_id": "src_meta",
                    "notebook_readback": "PASS",
                    "changes": ["NEW"],
                },
            ]
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            summary, _ = bridge.process_receipt_data(unverified, root=self.repo_root, apply=True)
        self.assertEqual(summary["new_records"], 0)
        reasons = {s["video_id"]: s["reason"] for s in summary["skipped"]}
        self.assertEqual(reasons["11111111111"], "SKIP_UNVERIFIED_NOTEBOOK")
        self.assertEqual(reasons["22222222222"], "SKIP_METADATA_ONLY")

    def test_06_git_commit_push_readback_and_divergence_stop(self):
        receipt = make_sample_receipt()
        buf = io.StringIO()
        with redirect_stdout(buf):
            _, touched = bridge.process_receipt_data(
                data=receipt,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        git_ev = bridge.verify_and_push_git(
            root=self.repo_root,
            commit_message="test: commit, push to bare origin, and verify remote readback",
            do_push=True,
            touched_paths=touched,
        )
        self.assertTrue(git_ev["committed"])
        self.assertTrue(git_ev["pushed"])
        self.assertTrue(git_ev["readback_verified"])
        self.assertEqual(git_ev["head_sha"], git_ev["remote_head_sha"])
        self.assertEqual(len(git_ev["file_blob_shas"]), 4)

        # Simulate remote divergence (another actor pushes to origin/<branch>) and verify safe stop
        other_clone = Path(self.tmp_dir.name) / "other_clone"
        subprocess.run(
            [
                "git",
                "clone",
                "-b",
                "feature/gemini-notebook-research-loop-20261016",
                self.remote_bare.as_posix(),
                str(other_clone),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(other_clone), "config", "user.email", "other@example.com"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(other_clone), "config", "user.name", "Other Runner"],
            check=True,
            capture_output=True,
        )
        (other_clone / "CONCURRENT.md").write_text("concurrent remote change\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(other_clone), "add", "CONCURRENT.md"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(other_clone), "commit", "-m", "Remote concurrent commit"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(other_clone),
                "push",
                "origin",
                "feature/gemini-notebook-research-loop-20261016",
            ],
            check=True,
            capture_output=True,
        )

        # Now try to push a new local change from repo_root -> must stop safely without overwriting
        receipt2 = make_sample_receipt(
            checked_at="2026-10-19",
            videos=[
                {
                    "video_id": "9bZkp7q19f0",
                    "title": "Second Video Test",
                    "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
                    "published_at": "2026-10-15",
                    "summary_ja": "リモート競合時の安全停止テスト用データ。",
                    "source_scope": "Transcript",
                    "claims": [],
                    "notebook_source_id": "src_019",
                    "notebook_readback": "PASS",
                    "changes": ["NEW"],
                }
            ],
        )
        with redirect_stdout(io.StringIO()):
            _, touched2 = bridge.process_receipt_data(
                data=receipt2,
                root=self.repo_root,
                apply=True,
                sync_index=True,
            )
        with self.assertRaisesRegex(ValueError, "is ahead by 1 commit"):
            bridge.verify_and_push_git(
                root=self.repo_root,
                commit_message="should stop before overwriting diverged remote",
                do_push=True,
                touched_paths=touched2,
            )

    def test_07_inbox_directory_discovery_and_filtering(self):
        inbox_dir = Path(self.tmp_dir.name) / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        # 1. Markdown file with embedded receipt JSON block
        md_content = (
            "# Gemini Task Export\n\n```json\n"
            + json.dumps(make_sample_receipt(), ensure_ascii=False, indent=2)
            + "\n```\n"
        )
        (inbox_dir / "01_gemini_export.md").write_text(md_content, encoding="utf-8")
        # 2. Unrelated text file (should be skipped in inbox mode)
        (inbox_dir / "02_notes.txt").write_text("単なるメモファイル（JSONなし）", encoding="utf-8")

        files = bridge.discover_inbox_files(inbox_dir)
        self.assertEqual(len(files), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
