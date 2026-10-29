"""Exercise actual adapters with command, Notebook, and DOM fakes only."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation/subtitle-switch'))
from services import Services, CATALOG, command
from pipeline import Pipeline, StageFailure
from switch_state import Inventory
import notebooklm_py_ingest as nb
import query_research


def note_for(row):
    metadata = {'okf_version': '0.2', 'type': 'RESEARCH_NOTE',
                'title': '【研究ノート】デモ [' + row['video_id'] + ']',
                'description': '独自の短い解説',
                'logical_id': f'youtube:{row["video_id"]}:research',
                'transcript_logical_id': f'youtube:{row["video_id"]}:transcript',
                'video_id': row['video_id'], 'resource': row['url'], 'canonical_url': row['url'],
                'published_at': row.get('published_at') or 'UNKNOWN'}
    text = '---\n' + '\n'.join(f'{key}: {json.dumps(value, ensure_ascii=False)}' for key, value in metadata.items())
    return text + '\ntags:\n  - "AI技術研究室"\n---\n## 独自要約\n独自の短い解説。\n## 内容の流れ\n' + row['url'] + '&t=0s\n## 限界・未確認\n映像・公式資料未確認。\n'


class FrontmatterListTests(unittest.TestCase):
    def test_all_app_text_io_has_explicit_utf8(self):
        import ast
        app = ROOT / 'automation/subtitle-switch'
        for path in [*app.glob('*.py'), *app.glob('*.pyw')]:
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if not isinstance(node, ast.Call):
                    continue
                name = getattr(node.func, 'attr', getattr(node.func, 'id', ''))
                if name not in ('read_text', 'write_text', 'open'):
                    continue
                if name == 'open':
                    index = 0 if isinstance(node.func, ast.Attribute) else 1
                    mode = next((k.value for k in node.keywords if k.arg == 'mode'),
                                node.args[index] if len(node.args) > index else None)
                    if isinstance(mode, ast.Constant) and 'b' in str(mode.value):
                        continue
                encoding = next((k.value for k in node.keywords if k.arg == 'encoding'), None)
                self.assertIsInstance(encoding, ast.Constant, f'{path.name}:{node.lineno}')
                self.assertIn(encoding.value.lower(), ('utf-8', 'utf-8-sig'), f'{path.name}:{node.lineno}')

    def test_inline_tags_match_existing_block_tags(self):
        block, body = query_research.parse_yaml_frontmatter(
            '---\ntags:\n  - "日本語"\n  - "a,b"\nrelated_records:\n'
            '  - logical_id: "youtube:example:research"\n'
            '    evidence: "確認済み"\n---\n本文')
        inline, inline_body = query_research.parse_yaml_frontmatter(
            '---\ntags: ["日本語", "a,b"]\n---\n本文')
        self.assertEqual(inline['tags'], block['tags'])
        self.assertEqual(inline_body, body)
        self.assertEqual(block['related_records'][0]['evidence'], '確認済み')
        self.assertEqual(query_research.parse_yaml_scalar('[]'), [])
        self.assertEqual(query_research.parse_yaml_scalar('[invalid'), '[invalid')



class NotebookFake:
    def __init__(self):
        self.sources, self.bodies, self.adds = [], {}, []
        self.auth = True
        self.uncertain = False

    def auth_check_passive(self):
        return self.auth

    def list_sources(self):
        return self.sources.copy()

    def get_fulltext(self, sid):
        return self.bodies[sid]

    def add_text(self, title, text):
        sid = str(len(self.sources))
        self.sources.append({'id': sid, 'type': 'text', 'title': title})
        self.bodies[sid] = text
        self.adds.append(title)
        if self.uncertain:
            raise TimeoutError()
        return sid


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        (self.repo / 'registry.json').write_text('{"records": []}', encoding='utf-8')
        self.vault = self.root / 'vault'
        self.notebook = NotebookFake()
        self.commands = []
        self.remote = {}
        self.caption_available = True
        self.caption_start_ms = 0
        self.ytdlp_error = ''
        self.config = {'repository': str(self.repo), 'vault': str(self.vault),
                       'save_branch': 'subtitle-switch/saves', 'notebook_id': 'test-notebook', 'source_limit': 300}
        self.services = Services(self.config, runner=self.runner, notebook=self.notebook, dom=lambda row: (1, 2))
        self.row = {'video_id': 'abcdefghijk', 'url': 'https://www.youtube.com/watch?v=abcdefghijk',
                    'title': 'デモ', 'published_at': '2026-10-27', 'receipts': {}}

    def runner(self, args, cwd=None, stdin=None, timeout=None):
        self.commands.append(args)
        result = SimpleNamespace(returncode=0, stdout='', stderr='')
        if args[0] == 'yt-dlp':
            if self.ytdlp_error:
                result.returncode, result.stderr = 1, self.ytdlp_error
                return result
            if '--dump-single-json' in args:
                result.stdout = json.dumps({'upload_date': '20261027', 'subtitles': {
                    'ja': [{'ext': 'json3', 'url': 'FAKE'}]} if self.caption_available else {}})
            else:
                (Path(cwd) / 'captions.ja.json3').write_text(json.dumps({'events': [
                    {'tStartMs': self.caption_start_ms, 'dDurationMs': 1000, 'segs': [{'utf8': '架空の字幕です。'}]}]}), encoding='utf-8')
        elif args[0] == 'claude':
            vid = Path(cwd).name
            row = dict(self.row, video_id=vid, url=f'https://www.youtube.com/watch?v={vid}')
            (Path(cwd) / 'research.md').write_text(note_for(row), encoding='utf-8')
        elif args[0] == 'git':
            if args[1:4] == ['remote', 'get-url', 'origin']:
                result.stdout = 'https://github.com/kamiyusense/ai-video-research.git\n'
            elif args[1:3] == ['branch', '--show-current']:
                result.stdout = 'subtitle-switch/saves\n'
            elif args[1:4] == ['diff', '--cached', '--quiet']:
                result.returncode = 1
            elif args[1] == 'rev-parse':
                result.stdout = 'a' * 40 + '\n'
            elif args[1] == 'push':
                self.remote = {p.relative_to(self.repo).as_posix(): p.read_text(encoding='utf-8')
                               for p in self.repo.rglob('*') if p.is_file()}
            elif args[1] == 'show':
                path = args[2].split(':', 1)[1]
                result.stdout = self.remote[path]
        else:
            self.fail('Unexpected executable: ' + args[0])
        return result

    def prepare(self):
        self.services.captions(self.row)
        self.row['receipts']['transcript'] = self.services.transcript(self.row)
        self.services.research(self.row)

    def test_real_adapters_end_to_end_two_videos_fake_boundaries(self):
        inventory = Inventory(self.root / 'state.json')
        inventory.refresh([{'video_id': vid, 'url': f'https://www.youtube.com/watch?v={vid}',
                            **{key: self.row.get(key, '') for key in
                               ('title', 'channel', 'published_at', 'lang', 'theme', 'kind', 'reason')}}
                           for vid in ('abcdefghijk', 'lmnopqrstuv')])
        with patch('receipt_to_research.collect_remote_branch_videos', return_value=({}, 'fresh')):
            Pipeline(inventory, self.services).run()
        self.assertEqual([r['status'] for r in inventory.data['videos'].values()], ['complete', 'complete'])
        for args in self.commands:
            if args[:2] == ['git', 'add']:
                self.assertEqual(set(args[3:]) - {'registry.json', CATALOG},
                                 {next(p for p in args if p.startswith('research/'))})
                self.assertFalse(any('transcript' in p or 'cues' in p for p in args))
            if args[:2] == ['git', 'push']:
                self.assertEqual(args[-1], 'a' * 40 + ':refs/heads/subtitle-switch/saves')
                self.assertNotIn('--force', args)
        self.assertFalse(any('架空の字幕です。' in body for body in self.remote.values()))
        self.assertEqual(len(self.notebook.adds), 4)
        self.assertTrue(all('【字幕原文】' in title or '【研究ノート】' in title for title in self.notebook.adds))

    def test_actual_caption_adapter_no_subtitles(self):
        self.caption_available = False
        self.assertEqual(self.services.captions(self.row), {'terminal': 'TRANSCRIPT_UNAVAILABLE'})
        self.assertEqual(len(self.commands), 1)

    def test_research_cli_constrained_sonnet_medium_no_fallback(self):
        self.prepare()
        call = next(args for args in self.commands if args[0] == 'claude')
        self.assertEqual(call[call.index('--model') + 1], 'sonnet')
        self.assertEqual(call[call.index('--effort') + 1], 'medium')
        self.assertEqual(call[call.index('--tools') + 1], 'Read,Write')
        self.assertIn('--strict-mcp-config', call)
        self.services.review(self.row)

    def test_long_subtitle_cannot_be_published_as_research(self):
        self.prepare()
        folder = self.services.folder(self.row)
        caption = '架空の長い字幕本文。' * 20
        (folder / 'cues.json').write_text(json.dumps([['0', caption]]), encoding='utf-8')
        self.row['receipts']['transcript'] = self.services.transcript(self.row)
        with (folder / 'research.md').open('a', encoding='utf-8') as stream:
            stream.write(caption)
        with self.assertRaisesRegex(StageFailure, 'LONG_CAPTION_COPY'):
            self.services.review(self.row)
        self.assertFalse(any(args[:2] == ['git', 'push'] for args in self.commands))

    def test_capacity_stops_only_notebook_no_partial_add(self):
        self.prepare()
        self.config['source_limit'] = 1
        with self.assertRaisesRegex(StageFailure, 'NOTEBOOK_CAPACITY'):
            self.services.notebook(self.row)
        self.assertEqual(self.notebook.adds, [])
        self.assertTrue(self.row['notebook_capacity_warning'])

    def test_notebook_postreadback_and_noop(self):
        self.prepare()
        result = self.services.notebook(self.row)
        self.assertTrue(result['is_mock'])
        self.assertNotEqual(result['Index_note'], result['Index_transcript'])
        self.assertNotEqual(result['source_ids']['research'], result['source_ids']['transcript'])
        self.services.notebook(self.row)
        self.assertEqual(len(self.notebook.adds), 2)

    def test_notebook_uncertain_response_read_back_without_resend(self):
        self.prepare()
        self.notebook.uncertain = True
        self.services.notebook(self.row)
        self.assertEqual(len(self.notebook.adds), 2)
        self.services.readback('notebook', self.row)
        self.assertEqual(len(self.notebook.adds), 2)

    def test_same_dom_element_cannot_complete(self):
        self.prepare()
        self.services.dom = lambda row: (1, 1)
        with self.assertRaisesRegex(StageFailure, 'DOM_READBACK_UNKNOWN'):
            self.services.notebook(self.row)

    def test_fulltext_mismatch_cannot_complete(self):
        self.prepare()
        self.services.notebook(self.row)
        self.notebook.bodies['0'] = 'truncated'
        with self.assertRaisesRegex(StageFailure, 'NOTEBOOK_READBACK_MISMATCH') as caught:
            self.services.notebook(self.row)
        self.assertEqual(len(self.notebook.adds), 2)
        self.assertIn('transcript', caught.exception.detail)
        self.assertIn('Notebook9字', caught.exception.detail)  # 'truncated', whitespace-free

    def test_notebook_dash_rules_for_front_matter_still_match(self):
        self.prepare()
        self.services.notebook(self.row)
        body = self.notebook.bodies['0']
        self.notebook.bodies['0'] = body.replace('---\n', '-' * 40 + '\n')
        self.services.notebook(self.row)  # readback passes; nothing is sent again
        self.assertEqual(len(self.notebook.adds), 2)

    def test_readback_waits_for_processing_before_reading(self):
        self.prepare()
        order = []
        self.notebook.wait_ready = lambda sid: order.append(('wait', sid)) or True
        reading = self.notebook.get_fulltext
        self.notebook.get_fulltext = lambda sid: order.append(('read', sid)) or reading(sid)
        self.services.notebook(self.row)
        self.assertEqual(order[:2], [('wait', '0'), ('read', '0')])

    def test_vault_inside_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            Services(dict(self.config, vault=str(self.repo / 'transcripts')), runner=self.runner, notebook=self.notebook)

    def test_main_branch_config_is_rejected(self):
        with self.assertRaises(ValueError):
            Services(dict(self.config, save_branch='main'), runner=self.runner, notebook=self.notebook)

    def test_changed_transcript_is_rejected_before_model_or_publish(self):
        self.prepare()
        (self.services.folder(self.row) / 'transcript.md').write_text('changed', encoding='utf-8')
        self.commands.clear()
        with self.assertRaisesRegex(StageFailure, 'TRANSCRIPT_INTEGRITY_MISMATCH'):
            self.services.research(self.row)
        with self.assertRaisesRegex(StageFailure, 'TRANSCRIPT_INTEGRITY_MISMATCH'):
            self.services.github(self.row)
        self.assertFalse(any(args[0] == 'claude' or args[:2] == ['git', 'push']
                             for args in self.commands))

    def test_invented_research_timestamp_is_rejected(self):
        self.prepare()
        path = self.services.folder(self.row) / 'research.md'
        path.write_text(path.read_text(encoding='utf-8').replace('&t=0s', '&t=999s'), encoding='utf-8')
        with self.assertRaisesRegex(StageFailure, 'RESEARCH_EVIDENCE_TIME_UNVERIFIED'):
            self.services.review(self.row)

    def test_whole_second_link_matches_fractional_caption_start(self):
        # Real notes link &t=35s for a caption starting at 35.668 (measured 2026-10-28).
        self.caption_start_ms = 35668
        self.prepare()
        path = self.services.folder(self.row) / 'research.md'
        path.write_text(path.read_text(encoding='utf-8').replace('&t=0s', '&t=35s'), encoding='utf-8')
        self.services.review(self.row)
        path.write_text(path.read_text(encoding='utf-8').replace('&t=35s', '&t=38s'), encoding='utf-8')
        with self.assertRaisesRegex(StageFailure, 'RESEARCH_EVIDENCE_TIME_UNVERIFIED'):
            self.services.review(self.row)

    def test_youtube_rate_limit_pauses_caption_stage(self):
        self.ytdlp_error = 'ERROR: Unable to download video subtitles: HTTP Error 429: Too Many Requests'
        with self.assertRaises(StageFailure) as caught:
            self.services.captions(self.row)
        self.assertEqual(caught.exception.reason, 'YOUTUBE_RATE_LIMIT')
        self.assertTrue(caught.exception.waiting and caught.exception.global_stage)

    def test_japanese_notes_roundtrip_with_cp932_default_text_io(self):
        import io
        original = io.open
        def cp932_default(file, mode='r', buffering=-1, encoding=None, *args, **kwargs):
            if 'b' not in mode and encoding is None:
                encoding = 'cp932'
            return original(file, mode, buffering, encoding, *args, **kwargs)
        with patch('io.open', side_effect=cp932_default):
            self.prepare()
            with patch('receipt_to_research.collect_remote_branch_videos', return_value=({}, 'fresh')):
                self.services.catalog(self.row)
            result = self.services.github(self.row)
        self.assertEqual(result['files_verified'], 3)
        self.assertIn('独自の短い解説', self.remote[self.row['research_path']])

    def test_error_with_usage_metadata_is_not_quota(self):
        self.prepare()
        self.services.run = lambda *a, **kw: SimpleNamespace(returncode=1, stderr='', stdout=json.dumps({
            'is_error': True, 'subtype': 'error_during_execution', 'result': 'Cannot write research.md',
            'usage': {'input_tokens': 100, 'output_tokens': 5}}))
        with self.assertRaisesRegex(StageFailure, '^RESEARCH_FAILED$') as error:
            self.services.research(self.row)
        self.assertFalse(error.exception.waiting)

    def test_definite_push_failure_retries_only_saved_commit_after_correction(self):
        inventory = Inventory(self.root / 'retry.json')
        inventory.refresh([dict(self.row, **{key: self.row.get(key, '') for key in
            ('title', 'channel', 'published_at', 'lang', 'theme', 'kind', 'reason')})])
        original = self.services.run
        pushes = []
        def runner(args, **kw):
            if args[:2] == ['git', 'push']:
                pushes.append(args[-1])
                if len(pushes) == 1:
                    return SimpleNamespace(returncode=1, stdout='', stderr='')
            if args[:2] == ['git', 'rev-parse'] and args[-1].startswith('origin/') and not self.remote:
                return SimpleNamespace(returncode=0, stdout='b'*40, stderr='')
            if args[:3] == ['git', 'merge-base', '--is-ancestor'] and args[3] == 'a'*40 and not self.remote:
                return SimpleNamespace(returncode=1, stdout='', stderr='')
            if args[:2] == ['git', 'show'] and not self.remote:
                path = args[-1].split(':', 1)[1]
                return SimpleNamespace(returncode=0, stdout=(self.repo / path).read_text(encoding='utf-8'), stderr='')
            return original(args, **kw)
        self.services.run = runner
        with patch('receipt_to_research.collect_remote_branch_videos', return_value=({}, 'fresh')):
            Pipeline(inventory, self.services).run()
            row = inventory.data['videos'][self.row['video_id']]
            self.assertEqual(row['status_reason'], 'GITHUB_PUSH_FAILED')
            self.assertTrue(row['github_push_failed'])
            Pipeline(inventory, self.services).run()
            self.assertEqual(len(pushes), 1)
            Pipeline(inventory, self.services).run('設定を修正')
        self.assertEqual(row['status'], 'complete')
        self.assertEqual(pushes, ['a'*40 + ':refs/heads/subtitle-switch/saves'] * 2)
        self.assertEqual(sum(args[:2] == ['git', 'commit'] for args in self.commands), 1)

    def test_retry_rejects_non_fast_forward(self):
        self.prepare()
        with patch('receipt_to_research.collect_remote_branch_videos', return_value=({}, 'fresh')):
            self.services.catalog(self.row)
        self.services.github(self.row)
        self.commands.clear()
        self.row['github_push_failed'] = True
        original = self.services.run
        def runner(args, **kw):
            if args[:2] == ['git', 'ls-remote']:
                return SimpleNamespace(returncode=0, stdout='b'*40 + '\trefs/heads/subtitle-switch/saves', stderr='')
            if args[:3] == ['git', 'merge-base', '--is-ancestor']:
                return SimpleNamespace(returncode=1, stdout='', stderr='')
            return original(args, **kw)
        self.services.run = runner
        with self.assertRaisesRegex(StageFailure, 'GITHUB_NON_FAST_FORWARD'):
            self.services.retry_github_push(self.row)
        self.assertFalse(any(args[:2] == ['git', 'push'] for args in self.commands))

    def test_zero_exit_quota_error_still_waits_without_fallback(self):
        self.prepare()
        self.services.run = lambda *a, **kw: SimpleNamespace(
            returncode=0, stdout='{"is_error": true, "result": "usage limit"}', stderr='')
        with self.assertRaisesRegex(StageFailure, 'CLAUDE_QUOTA') as raised:
            self.services.research(self.row)
        self.assertTrue(raised.exception.waiting)

    def test_crash_between_notebook_adds_only_adds_unsent_remainder(self):
        self.prepare()
        folder = self.services.folder(self.row)
        self.notebook.add_text(nb.transcript_title(self.row['video_id'], self.row['title']),
                               (folder / 'transcript.md').read_text(encoding='utf-8'))
        (folder / 'notebook_transcript_inflight.json').write_text('{"sent":true}', encoding='utf-8')
        result = self.services.readback('notebook', self.row)
        self.assertEqual(len(self.notebook.adds), 2)
        self.assertIn('【研究ノート】', self.notebook.adds[-1])
        self.assertNotEqual(result['source_ids']['research'], result['source_ids']['transcript'])

    def test_unknown_notebook_send_does_not_resend_or_add_remainder(self):
        self.prepare()
        folder = self.services.folder(self.row)
        (folder / 'notebook_transcript_inflight.json').write_text('{"sent":true}', encoding='utf-8')
        self.assertIsNone(self.services.readback('notebook', self.row))
        self.assertEqual(self.notebook.adds, [])

    def prepare_catalog(self):
        self.prepare()
        with patch('receipt_to_research.collect_remote_branch_videos', return_value=({}, 'fresh')):
            self.services.catalog(self.row)

    def test_actual_repository_note_must_equal_reviewed_note(self):
        self.prepare_catalog()
        (self.repo / self.row['research_path']).write_text('unreviewed replacement', encoding='utf-8')
        with self.assertRaisesRegex(StageFailure, 'PUBLISH_NOTE_DIFFERS_FROM_REVIEW'):
            self.services.github(self.row)
        self.assertFalse(any(args[:2] == ['git', 'add'] for args in self.commands))

    def test_registry_forbidden_payload_cannot_be_published(self):
        self.prepare_catalog()
        registry = json.loads((self.repo / 'registry.json').read_text(encoding='utf-8'))
        registry['full_transcript'] = '架空の禁止フィールド'
        (self.repo / 'registry.json').write_text(json.dumps(registry), encoding='utf-8')
        with self.assertRaisesRegex(StageFailure, 'FORBIDDEN_PUBLISH_CONTENT'):
            self.services.github(self.row)
        self.assertFalse(any(args[:2] == ['git', 'add'] for args in self.commands))

    def test_catalog_path_survives_restart_on_another_day(self):
        self.prepare_catalog()
        first = self.row['research_path']
        with patch('receipt_to_research.collect_remote_branch_videos', return_value=({}, 'fresh')), \
                patch('services.date') as fake_date:
            fake_date.today.return_value.isoformat.return_value = '2099-01-01'
            self.row.pop('research_path')
            self.services.catalog(self.row)
        self.assertEqual(self.row['research_path'], first)
        self.assertEqual(len(list((self.repo / 'research').glob('*.md'))), 1)

    def test_later_remote_commit_does_not_make_confirmed_write_unknown(self):
        self.prepare_catalog()
        self.services.github(self.row)
        previous_pushes = sum(args[:2] == ['git', 'push'] for args in self.commands)
        def later_head(args, **kw):
            if args[:2] == ['git', 'rev-parse'] and args[-1].startswith('origin/'):
                return SimpleNamespace(returncode=0, stdout='b' * 40, stderr='')
            return self.runner(args, **kw)
        self.services.run = later_head
        result = self.services.readback('github', self.row)
        self.assertEqual(result['remote_head'], 'b' * 40)
        self.assertEqual(result['verified_commit'], 'a' * 40)
        self.assertEqual(sum(args[:2] == ['git', 'push'] for args in self.commands), previous_pushes)

    def test_api_configuration_blocks_model_before_any_subprocess(self):
        with patch.dict(os.environ, {'CLAUDE_CODE_USE_VERTEX': '1'}), \
                patch('services.subprocess.run', side_effect=AssertionError('must not start')):
            with self.assertRaisesRegex(StageFailure, 'CLAUDE_API_CONFIGURATION_BLOCKED'):
                command(['claude', '-p'])


if __name__ == '__main__':
    unittest.main()


class CommandResolutionTests(unittest.TestCase):
    def test_cmd_executables_are_resolved_without_shell(self):
        from services import NotebookClient
        with patch.dict(os.environ, {}, clear=True), patch('services.shutil.which', return_value='C:/Tools/claude.cmd'), patch('services.subprocess.run') as run:
            command(['claude', '-p'])
            self.assertEqual(run.call_args.args[0][0], 'C:/Tools/claude.cmd')
            self.assertNotIn('shell', run.call_args.kwargs)
        for name in ('claude', 'yt-dlp', 'notebooklm'):
            with self.subTest(name=name), patch.dict(os.environ, {}, clear=True), patch('services.shutil.which', return_value=None), patch('services.subprocess.run') as run:
                with self.assertRaisesRegex(StageFailure, name.upper().replace('-', '_') + '_COMMAND_NOT_FOUND'):
                    command([name])
                run.assert_not_called()
        with patch('services.shutil.which', return_value=None):
            with self.assertRaisesRegex(StageFailure, 'NOTEBOOKLM_COMMAND_NOT_FOUND'):
                NotebookClient('fixture').auth_check_passive()
        with patch('services.shutil.which', return_value='C:/Tools/notebooklm.cmd'), patch('services.subprocess.run') as run:
            NotebookClient('fixture')._run('list_sources')
            self.assertEqual(run.call_args.args[0][0], 'C:/Tools/notebooklm.cmd')
