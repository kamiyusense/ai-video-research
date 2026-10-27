"""Offline acceptance scenarios using fake service boundaries."""
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / 'automation/subtitle-switch'
sys.path.insert(0, str(APP))
from pipeline import Pipeline, StageFailure, STAGES, InstanceLock
from switch_state import Inventory
from captions import build_okf, parse_json3, select_track
from switch_app import save_session, folders, display_row, save_targets
from services import Services


class FakeServices:
    is_mock = True

    def __init__(self):
        self.calls = []
        self.reads = []
        self.fail = {}
        self.reconcile = {}

    def execute(self, stage, row):
        self.calls.append((row['video_id'], stage))
        result = self.fail.get((row['video_id'], stage), {})
        if isinstance(result, BaseException):
            raise result
        return result

    def readback(self, stage, row):
        self.reads.append((row['video_id'], stage))
        return self.reconcile.get((row['video_id'], stage))


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = Inventory(self.root / 'inventory.json')
        self.state.refresh([{'video_id': vid, 'url': f'https://www.youtube.com/watch?v={vid}',
                             **{key: '' for key in ('title', 'channel', 'published_at', 'lang', 'theme', 'kind', 'reason')}}
                            for vid in ('aaaaaaaaaaa', 'bbbbbbbbbbb')])
        self.fake = FakeServices()

    def test_manual_save_does_not_process_inventory_rows(self):
        targets = save_targets(self.state, 'manual', 'https://youtu.be/ccccccccccc')
        save_session(self.state, self.fake, self.root / 'drive', target_ids=targets)
        self.assertEqual({vid for vid, _ in self.fake.calls}, {'ccccccccccc'})
        self.assertEqual(self.state.data['videos']['aaaaaaaaaaa']['status'], 'pending')
        self.assertEqual(self.state.data['videos']['bbbbbbbbbbb']['status'], 'pending')

    def test_selected_save_ignores_manual_urls_unselected_and_rejected_rows(self):
        self.state.reject('bbbbbbbbbbb', True, '興味なし')
        targets = save_targets(self.state, 'selected', 'invalid manual URL',
                               ('aaaaaaaaaaa', 'bbbbbbbbbbb'))
        save_session(self.state, self.fake, self.root / 'drive', target_ids=targets)
        self.assertEqual({vid for vid, _ in self.fake.calls}, {'aaaaaaaaaaa'})
        self.assertEqual(self.state.data['videos']['bbbbbbbbbbb']['status'], 'pending')

    def test_selected_save_does_not_process_unselected_eligible_row(self):
        targets = save_targets(self.state, 'selected', selected=('aaaaaaaaaaa',))
        save_session(self.state, self.fake, self.root / 'drive', target_ids=targets)
        self.assertEqual({vid for vid, _ in self.fake.calls}, {'aaaaaaaaaaa'})
        self.assertEqual(self.state.data['videos']['bbbbbbbbbbb']['status'], 'pending')

    def test_saved_commit_retry_requires_changed_cause_and_stops_at_two(self):
        row = self.state.data['videos']['aaaaaaaaaaa']
        row.update(inflight='github', github_push_failed=True, failed=True,
                   completed_stages=list(STAGES[:STAGES.index('github')]))
        retries = []
        def retry(row):
            retries.append(row['video_id'])
            raise StageFailure('GITHUB_PUSH_FAILED')
        self.fake.retry_github_push = retry
        pipeline = Pipeline(self.state, self.fake)
        pipeline.run('原因1', {'aaaaaaaaaaa'})
        pipeline.run('原因1', {'aaaaaaaaaaa'})
        pipeline.run('原因2', {'aaaaaaaaaaa'})
        pipeline.run('原因3', {'aaaaaaaaaaa'})
        self.assertEqual(retries, ['aaaaaaaaaaa'] * 2)
        self.assertEqual(row['corrected_retries'], 2)
        self.assertEqual(row['inflight'], 'github')

    def test_no_selection_no_urls_means_no_operations(self):
        targets = save_targets(self.state, 'selected', 'https://youtu.be/ccccccccccc')
        save_session(self.state, self.fake, self.root / 'drive', target_ids=targets)
        self.assertEqual(self.fake.calls, [])
        self.assertFalse((self.root / 'drive').exists())

    def test_running_row_remains_visible_with_stage(self):
        seen = []
        def observe():
            seen.extend((row['video_id'], row['status'], row['stage']) for row in self.state.visible())
        Pipeline(self.state, self.fake, observe).run(target_ids={'aaaaaaaaaaa'})
        self.assertIn(('aaaaaaaaaaa', 'running', 'research'), seen)
        self.assertNotIn(('bbbbbbbbbbb', 'running', 'research'), seen)

    def test_one_click_multiple_videos_complete_and_preferences(self):
        save_session(self.state, self.fake, self.root / 'drive')
        self.assertTrue(all(row['status'] == 'complete' for row in self.state.data['videos'].values()))
        self.assertEqual(len(self.fake.calls), 2 * len(STAGES))
        preferences = list((self.root / 'drive').glob('preferences_*.json'))
        self.assertEqual(len(preferences), 1)
        self.assertEqual(len(json.loads(preferences[0].read_text(encoding='utf-8'))['saved']), 2)
        self.assertEqual(list((self.root / 'preference_outbox').glob('*.json')), [])

    def test_no_subtitles_terminal_and_other_video_continues(self):
        self.fake.fail[('aaaaaaaaaaa', 'captions')] = {'terminal': 'TRANSCRIPT_UNAVAILABLE'}
        Pipeline(self.state, self.fake).run()
        self.assertEqual(self.state.data['videos']['aaaaaaaaaaa']['status'], 'TRANSCRIPT_UNAVAILABLE')
        self.assertNotIn(('aaaaaaaaaaa', 'research'), self.fake.calls)
        self.assertEqual(self.state.data['videos']['bbbbbbbbbbb']['status'], 'complete')

    def test_restart_resumes_without_repeating_completed_stages(self):
        self.fake.fail[('aaaaaaaaaaa', 'research')] = StageFailure('CLAUDE_QUOTA', waiting=True)
        Pipeline(self.state, self.fake).run()
        state = Inventory(self.state.path)
        self.fake.calls.clear()
        self.fake.fail.clear()
        Pipeline(state, self.fake).run('利用枠の回復を確認')
        self.assertEqual(self.fake.calls[0], ('aaaaaaaaaaa', 'research'))
        self.assertEqual(len(self.fake.calls), len(STAGES) - STAGES.index('research'))

    def test_unknown_write_only_reads_back_on_restart(self):
        self.fake.fail[('aaaaaaaaaaa', 'github')] = TimeoutError()
        Pipeline(self.state, self.fake).run()
        state = Inventory(self.state.path)
        self.fake.calls.clear()
        Pipeline(state, self.fake).run()
        self.assertEqual(self.fake.reads, [('aaaaaaaaaaa', 'github')])
        self.assertNotIn(('aaaaaaaaaaa', 'github'), self.fake.calls)
        self.assertEqual(state.data['videos']['aaaaaaaaaaa']['status'], 'waiting')
        self.fake.reconcile[('aaaaaaaaaaa', 'github')] = {'verified': True}
        Pipeline(state, self.fake).run()
        self.assertEqual(state.data['videos']['aaaaaaaaaaa']['status'], 'complete')

    def test_robot_blocks_caption_stage_for_remaining(self):
        self.fake.fail[('aaaaaaaaaaa', 'captions')] = StageFailure('YOUTUBE_ROBOT_CHECK', True, True)
        Pipeline(self.state, self.fake).run()
        self.assertNotIn(('bbbbbbbbbbb', 'captions'), self.fake.calls)
        self.assertEqual(self.state.data['videos']['bbbbbbbbbbb']['status'], 'waiting')

    def test_failed_readback_cannot_clear_original_unknown_write(self):
        self.fake.fail[('aaaaaaaaaaa', 'github')] = TimeoutError()
        Pipeline(self.state, self.fake).run()
        state = Inventory(self.state.path)
        self.fake.calls.clear()
        def failed_readback(stage, row):
            raise StageFailure('GITHUB_COMMAND_FAILED', no_write=True)
        self.fake.readback = failed_readback
        Pipeline(state, self.fake).run()
        self.assertEqual(state.data['videos']['aaaaaaaaaaa']['inflight'], 'github')
        Pipeline(state, self.fake).run('設定を修正')
        self.assertNotIn(('aaaaaaaaaaa', 'github'), self.fake.calls)

    def test_robot_barrier_survives_restart_and_covers_new_candidates(self):
        self.fake.fail[('aaaaaaaaaaa', 'captions')] = StageFailure('YOUTUBE_ROBOT_CHECK', True, True)
        Pipeline(self.state, self.fake).run()
        state = Inventory(self.state.path)
        candidate = dict(state.data['videos']['aaaaaaaaaaa'])
        candidate.update(video_id='ccccccccccc', url='https://www.youtube.com/watch?v=ccccccccccc')
        state.refresh([candidate])
        self.fake.calls.clear()
        self.fake.fail.clear()
        Pipeline(state, self.fake).run()
        self.assertEqual(self.fake.calls, [('ccccccccccc', 'intake')])
        self.assertEqual(state.data['videos']['ccccccccccc']['status_reason'], 'YOUTUBE_ROBOT_CHECK')
        Pipeline(state, self.fake).run('字幕取得条件を修正')
        self.assertTrue(all(row['status'] == 'complete' for row in state.data['videos'].values()))
        self.assertEqual(state.data['blocked_stages'], {})

    def test_same_correction_cannot_clear_a_repeated_global_barrier(self):
        self.fake.fail[('aaaaaaaaaaa', 'captions')] = StageFailure('YOUTUBE_ROBOT_CHECK', True, True)
        Pipeline(self.state, self.fake).run()
        Pipeline(self.state, self.fake).run('設定を修正')
        state = Inventory(self.state.path)
        self.fake.calls.clear()
        Pipeline(state, self.fake).run('設定を修正')
        self.assertEqual(self.fake.calls, [])
        self.assertIn('captions', state.data['blocked_stages'])

    def test_notebook_auth_blocks_only_notebook_remaining(self):
        self.fake.fail[('aaaaaaaaaaa', 'notebook')] = StageFailure('NOTEBOOK_LOGIN_EXPIRED', True, True)
        Pipeline(self.state, self.fake).run()
        self.assertIn(('bbbbbbbbbbb', 'github'), self.fake.calls)
        self.assertNotIn(('bbbbbbbbbbb', 'notebook'), self.fake.calls)

    def test_notebook_barrier_after_restart_still_allows_new_github_save(self):
        self.fake.fail[('aaaaaaaaaaa', 'notebook')] = StageFailure('NOTEBOOK_LOGIN_EXPIRED', True, True)
        Pipeline(self.state, self.fake).run()
        state = Inventory(self.state.path)
        candidate = dict(state.data['videos']['aaaaaaaaaaa'])
        candidate.update(video_id='ccccccccccc', url='https://www.youtube.com/watch?v=ccccccccccc')
        state.refresh([candidate])
        self.fake.calls.clear()
        Pipeline(state, self.fake).run()
        self.assertIn(('ccccccccccc', 'github'), self.fake.calls)
        self.assertNotIn(('ccccccccccc', 'notebook'), self.fake.calls)
        self.assertEqual(state.data['videos']['ccccccccccc']['status_reason'], 'NOTEBOOK_LOGIN_EXPIRED')

    def test_lock_prevents_second_instance(self):
        with InstanceLock(self.root / 'instance.lock'):
            with self.assertRaisesRegex(RuntimeError, 'ALREADY_RUNNING'):
                with InstanceLock(self.root / 'instance.lock'):
                    pass
        with InstanceLock(self.root / 'instance.lock'):
            pass

    def test_preferences_drive_unavailable_does_not_stop_batch(self):
        blocked = self.root / 'not_a_folder'
        blocked.write_text('x', encoding='utf-8')
        save_session(self.state, self.fake, blocked)
        self.assertTrue(all(row['status'] == 'complete' for row in self.state.data['videos'].values()))
        self.assertEqual(len(list((self.root / 'preference_outbox').glob('*.json'))), 1)

    def test_damaged_preference_queue_does_not_stop_batch_or_publish_bad_data(self):
        outbox = self.root / 'preference_outbox'
        outbox.mkdir()
        queued = outbox / 'preferences_20261026.json'
        drive = self.root / 'drive'
        for attempt, damaged in enumerate(({}, {'updated': None}, {'updated': []},
                        {'updated': 'bad-date'}, {'updated': '2026-10-26'},
                        {'updated': '2026-10-26', 'session_id': []}), start=1):
            with self.subTest(damaged=damaged):
                queued.write_text(json.dumps(damaged), encoding='utf-8')
                save_session(self.state, self.fake, drive)
                self.assertTrue(all(row['status'] == 'complete'
                                    for row in self.state.data['videos'].values()))
                self.assertEqual(json.loads(queued.read_text(encoding='utf-8')), damaged)
                self.assertEqual(len(list(drive.glob('preferences_*.json'))), attempt)
        # Preserve the damaged file for inspection; delivery can resume once
        # the owner has repaired it, without replaying the video saves.
        queued.unlink()
        save_session(self.state, self.fake, drive)
        self.assertEqual(len(self.fake.calls), 2 * len(STAGES))
        self.assertEqual(len(list(drive.glob('preferences_*.json'))), 7)

    def test_failure_requires_changed_cause_and_retries_at_most_twice(self):
        self.fake.fail[('aaaaaaaaaaa', 'research')] = StageFailure('RESEARCH_FAILED')
        Pipeline(self.state, self.fake).run()
        before = len(self.fake.calls)
        Pipeline(self.state, self.fake).run()
        self.assertEqual(len(self.fake.calls), before)
        Pipeline(self.state, self.fake).run('設定を修正')
        self.assertEqual(len(self.fake.calls), before + 1)
        Pipeline(self.state, self.fake).run('設定を修正')
        self.assertEqual(len(self.fake.calls), before + 1)
        Pipeline(self.state, self.fake).run('利用枠の回復を確認')
        Pipeline(self.state, self.fake).run('字幕取得条件を修正')
        self.assertEqual(len(self.fake.calls), before + 2)
        self.assertEqual(self.state.data['videos']['aaaaaaaaaaa']['status_reason'], 'RETRY_LIMIT')

    def test_folder_resolution_prefers_new_then_legacy_and_override(self):
        from services import browser
        legacy = self.root / 'AI動画研究室_受け箱'
        legacy.mkdir()
        kwargs = dict(drive_root=self.root, lab_name='AI動画研究室')
        self.assertEqual(browser.lab_folder(legacy.name, **kwargs), legacy)
        preferred = self.root / 'AI動画研究室' / legacy.name
        preferred.mkdir(parents=True)
        self.assertEqual(browser.lab_folder(legacy.name, **kwargs), preferred)
        self.assertEqual(browser.lab_folder(legacy.name, override=self.root / 'custom', **kwargs), self.root / 'custom')

    def test_table_displays_metadata_progress_wait_reason_and_count(self):
        row = self.state.data['videos']['aaaaaaaaaaa']
        row.update(stage='notebook', status='waiting', status_reason='NOTEBOOK_CAPACITY',
                   notebook_sources_used=299, notebook_capacity_warning=True)
        values = display_row(row)
        self.assertEqual(values[:6], ('', '取得中', '取得中', '取得中', '未設定', ''))
        self.assertEqual(values[6], 'Notebook保存・確認')
        self.assertIn('ソース上限', values[7])
        self.assertEqual(values[8], '299（上限前警告）')
        row['status'] = 'ALREADY_REGISTERED'
        self.assertNotIn(row, self.state.visible())
        self.assertIn(row, self.state.visible(show_processed=True))


class CaptionTests(unittest.TestCase):
    def test_manual_preferred_over_automatic_and_empty(self):
        metadata = {'subtitles': {'en': [{'ext': 'json3', 'url': 'manual'}]},
                    'automatic_captions': {'ja': [{'ext': 'json3', 'url': 'automatic'}]}}
        self.assertEqual(select_track(metadata), ('manual', 'en', 'manual'))
        self.assertIsNone(select_track({}))

    def test_automatic_rolling_overlap_only(self):
        document = {'events': [{'tStartMs': i * 83000, 'dDurationMs': 84000, 'segs': [{'utf8': text}]}
                               for i, text in enumerate(('hello world', 'world again', 'world again'))]}
        auto = parse_json3(document, automatic=True)
        manual = parse_json3(document)
        self.assertEqual(auto, [('0', 'hello world'), ('83', ' again')])
        self.assertEqual(len(manual), 3)
        self.assertEqual(manual[1], ('83', 'world again'))
        text, meta = build_okf({'video_id': 'abcdefghijk', 'url': 'https://www.youtube.com/watch?v=abcdefghijk'}, auto, 'automatic', 'en')
        self.assertIn('[83]  again', text)
        self.assertEqual(meta['line_count'], 2)
        self.assertEqual(meta['published_at'], 'UNKNOWN')
        self.assertEqual(meta['deduplication'], 'rolling_overlap_v1')

    def test_no_cues_unavailable(self):
        with self.assertRaisesRegex(ValueError, 'TRANSCRIPT_UNAVAILABLE'):
            build_okf({}, [], 'manual', 'ja')

    def test_nonoverlapping_repeated_words_are_preserved(self):
        events = [{'tStartMs': time, 'dDurationMs': 1000, 'segs': [{'utf8': '同じ言葉'}]}
                  for time in (0, 83000)]
        self.assertEqual(parse_json3({'events': events}, automatic=True),
                         [('0', '同じ言葉'), ('83', '同じ言葉')])


if __name__ == '__main__':
    unittest.main()
