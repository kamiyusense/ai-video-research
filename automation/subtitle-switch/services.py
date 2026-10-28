"""Service adapters for the owner's later execution. Never run by offline tests.

No API keys, alternate models, automatic login, media download or shell strings.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import shutil
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from captions import build_okf, parse_json3
from pipeline import StageFailure
from switch_state import atomic_json

AUTO = Path(__file__).resolve().parents[1] / 'gemini-notebook'
sys.path.insert(0, str(AUTO))
import intake_url
import notebooklm_py_ingest as nb
import notebook_auto_ingest as browser
import query_research as knowledge
import receipt_to_research as receipt

CATALOG = 'automation/gemini-notebook/state/video_knowledge_catalog.json'


def command(args, cwd=None, stdin=None, timeout=180):
    # Never print captured CLI output; it can include private data.
    if args[0] == 'claude' and any(name in os.environ for name in (
        'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL',
        'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY',
    )):
        # Inspect names only, never read key/token values or switch providers.
        raise StageFailure('CLAUDE_API_CONFIGURATION_BLOCKED')
    args = list(args)
    if args[0] in ('claude', 'yt-dlp', 'notebooklm'):
        executable = shutil.which(args[0])
        if executable is None:
            raise StageFailure(args[0].upper().replace('-', '_') + '_COMMAND_NOT_FOUND', no_write=True)
        args[0] = executable
    return subprocess.run(args, cwd=cwd, input=stdin, text=True, encoding='utf-8',
                          capture_output=True, timeout=timeout,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))



def youtube_refusal(stderr):
    """Service-wide YouTube refusals pause the caption stage for every video until the owner retries."""
    text = (stderr or '').lower()
    if any(word in text for word in ('bot', 'sign in to confirm')):
        raise StageFailure('YOUTUBE_ROBOT_CHECK', waiting=True, global_stage=True)
    if '429' in text or 'too many requests' in text:
        raise StageFailure('YOUTUBE_RATE_LIMIT', waiting=True, global_stage=True)

class NotebookClient(nb.NotebookLmCliClient):
    """Route Notebook CLI through the same Windows executable resolver."""
    def auth_check_passive(self):
        try:
            return self._run('auth_check_passive').returncode == 0
        except StageFailure:
            raise
        except Exception:
            return False

    def _run(self, key, stdin=None, timeout=None, **fmt):
        args = [arg.format(notebook_id=self.notebook_id, **fmt) for arg in self.COMMANDS[key]]
        return command(args, stdin=stdin, timeout=timeout or self.timeout)


class Services:
    def __init__(self, config, runner=command, notebook=None, dom=None):
        self.config, self.run = config, runner
        # Injected boundaries are simulation evidence, never live evidence.
        self.is_mock = runner is not command or notebook is not None or dom is not None
        self.repo = Path(config['repository']).resolve()
        self.vault = Path(config['vault']).resolve()
        # Prevent transcripts or scratch model files from entering the repository.
        if self.vault == self.repo or self.repo in self.vault.parents:
            raise ValueError('保管庫はGitHub作業フォルダの外に指定してください')
        self.branch = config.get('save_branch', 'subtitle-switch/saves')
        if not re.fullmatch(r'subtitle-switch/[A-Za-z0-9_-]+', self.branch):
            raise ValueError('保存先はsubtitle-switch/で始まる専用ブランチにしてください')
        self.nb_client = notebook or NotebookClient(config['notebook_id'])
        self.dom = dom or self.dom_readback

    def folder(self, row):
        folder = self.vault / 'jobs' / row['video_id']
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def git(self, *args, check=True):
        cp = self.run(['git', *args], cwd=self.repo)
        if check and cp.returncode:
            raise StageFailure('GITHUB_COMMAND_FAILED', no_write=args[0] != 'push')
        return cp

    def boundary(self):
        origin = self.git('remote', 'get-url', 'origin').stdout.strip()
        if origin not in ('https://github.com/kamiyusense/ai-video-research.git',
                          'https://github.com/kamiyusense/ai-video-research',
                          'git@github.com:kamiyusense/ai-video-research.git'):
            raise StageFailure('REPOSITORY_BOUNDARY', no_write=True)
        branch = self.git('branch', '--show-current').stdout.strip()
        if branch != self.branch or branch in ('main', 'master'):
            raise StageFailure('SAVE_BRANCH_REQUIRED', no_write=True)

    def execute(self, stage, row):
        return getattr(self, stage)(row)

    def intake(self, row):
        self.boundary()
        self.git('fetch', 'origin')
        result = intake_url.check_url_intake(row['url'], root=self.repo)
        if result['status'] == 'ALREADY_REGISTERED':
            return {'terminal': 'ALREADY_REGISTERED'}
        if result['status'] != 'NOT_REGISTERED':
            raise StageFailure('UNKNOWN_INTAKE')
        # Second defense: all fetched remote branches, using existing scanner.
        remote, _ = receipt.collect_remote_branch_videos(root=self.repo, fetch_remote=False)
        if row['video_id'] in remote:
            return {'terminal': 'ALREADY_REGISTERED'}
        return {'checked': True}

    def captions(self, row):
        folder = self.folder(row)
        common = ['yt-dlp', '--ignore-config', '--skip-download', '--no-playlist',
                  '--no-warnings', '--socket-timeout', '30']
        cp = self.run([*common, '--dump-single-json', row['url']], cwd=folder)
        if cp.returncode:
            youtube_refusal(cp.stderr)
            raise StageFailure('CAPTION_FETCH_FAILED', detail=cp.stderr)
        meta = json.loads(cp.stdout)
        if meta.get('id', row['video_id']) != row['video_id']:
            raise StageFailure('CAPTION_VIDEO_MISMATCH')
        from captions import select_track
        selected = select_track(meta)
        if not selected:
            return {'terminal': 'TRANSCRIPT_UNAVAILABLE'}
        kind, language, _ = selected
        if not re.fullmatch(r'[A-Za-z0-9_-]+', language):
            raise StageFailure('CAPTION_LANGUAGE_INVALID')
        cp = self.run([*common, '--write-subs' if kind == 'manual' else '--write-auto-subs',
                       '--sub-langs', language, '--sub-format', 'json3',
                       '-o', 'captions.%(ext)s', row['url']], cwd=folder)
        if cp.returncode:
            youtube_refusal(cp.stderr)
            raise StageFailure('CAPTION_FETCH_FAILED', detail=cp.stderr)
        path = folder / f'captions.{language}.json3'
        if not path.is_file():
            raise StageFailure('CAPTION_FILE_UNKNOWN')
        cues = parse_json3(json.loads(path.read_text(encoding='utf-8')), kind == 'automatic')
        if not cues:
            return {'terminal': 'TRANSCRIPT_UNAVAILABLE'}
        atomic_json(folder / 'cues.json', cues)
        row['title'] = row.get('title') or str(meta.get('title', ''))
        published = meta.get('upload_date')
        if published and re.fullmatch(r'\d{8}', published):
            row['published_at'] = f'{published[:4]}-{published[4:6]}-{published[6:]}'
        atomic_json(folder / 'caption_metadata.json', {'kind': kind, 'language': language})
        return {'caption_kind': kind, 'language': language, 'cue_count': len(cues)}

    def transcript(self, row):
        folder = self.folder(row)
        cues = json.loads((folder / 'cues.json').read_text(encoding='utf-8'))
        caption = json.loads((folder / 'caption_metadata.json').read_text(encoding='utf-8'))
        text, meta = build_okf(row, cues, caption['kind'], caption['language'])
        (folder / 'transcript.md').write_text(text, encoding='utf-8', newline='\n')
        return {'sha256': meta['sha256'], 'line_count': meta['line_count']}

    def research(self, row):
        self.verify_transcript(row)
        folder = self.folder(row)
        template = (Path(__file__).parent / 'research_prompt.md').read_text(encoding='utf-8')
        cp = self.run(['claude', '-p', '--model', 'sonnet', '--effort', 'medium',
                       '--tools', 'Read,Write', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                       '--setting-sources', '',
                       '--permission-mode', 'acceptEdits', '--output-format', 'json'],
                      cwd=folder, stdin=template, timeout=1200)
        try:
            response = json.loads(cp.stdout)
        except ValueError:
            response = None
        model_error = isinstance(response, dict) and (response.get('is_error') or
                      str(response.get('subtype', '')).startswith('error'))
        if cp.returncode or model_error:
            # Ignore usage/accounting metadata present in every JSON result.
            details = [cp.stdout, cp.stderr] if not isinstance(response, dict) else [
                str(response.get(key, '')) for key in ('subtype', 'error', 'errors', 'result', 'message')]
            details.append(cp.stderr)
            quota = bool(re.search(r'quota|rate[_ -]?limit|usage[_ -]?limit|limit[_ -]?reached|'
                                   r'out of (?:credits|usage)|utilization limit', ' '.join(details), re.I))
            raise StageFailure('CLAUDE_QUOTA' if quota else 'RESEARCH_FAILED', waiting=quota, detail=cp.stderr)
        if not (folder / 'research.md').is_file():
            raise StageFailure('RESEARCH_FILE_MISSING')
        return {'created': True}

    def verify_transcript(self, row):
        folder = self.folder(row)
        cues = json.loads((folder / 'cues.json').read_text(encoding='utf-8'))
        caption = json.loads((folder / 'caption_metadata.json').read_text(encoding='utf-8'))
        expected, metadata = build_okf(row, cues, caption['kind'], caption['language'])
        actual = (folder / 'transcript.md').read_text(encoding='utf-8')
        receipt = row.get('receipts', {}).get('transcript', {})
        if actual != expected or receipt.get('sha256') != metadata['sha256']:
            raise StageFailure('TRANSCRIPT_INTEGRITY_MISMATCH')
        return cues

    def review(self, row):
        verified_cues = self.verify_transcript(row)
        folder = self.folder(row)
        text = (folder / 'research.md').read_text(encoding='utf-8')
        try:
            receipt.scan_forbidden_keys(text)
        except ValueError:
            raise StageFailure('FORBIDDEN_PUBLISH_CONTENT') from None
        fm, _ = knowledge.parse_yaml_frontmatter(text)
        valid, errors = knowledge.validate_okf_frontmatter(fm)
        vid = row['video_id']
        required = {'type': 'RESEARCH_NOTE', 'video_id': vid,
                    'logical_id': f'youtube:{vid}:research',
                    'transcript_logical_id': f'youtube:{vid}:transcript',
                    'resource': row['url'], 'canonical_url': row['url'],
                    'published_at': row.get('published_at') or 'UNKNOWN'}
        if not valid or any(fm.get(k) != value for k, value in required.items()):
            raise StageFailure('RESEARCH_OKF_INVALID')
        times = re.findall(re.escape(row['url']) + r'&t=(\d+(?:\.\d+)?)s', text)
        if not times:
            raise StageFailure('RESEARCH_EVIDENCE_MISSING')
        # Links carry whole seconds while caption starts are fractional (e.g. 35 for 35.668),
        # so a time counts when a caption starts within two seconds of it (notes round either way).
        starts = [Decimal(start) for start, _ in verified_cues]
        unmatched = [time for time in times if not any(abs(Decimal(time) - start) < 2 for start in starts)]
        if unmatched:
            raise StageFailure('RESEARCH_EVIDENCE_TIME_UNVERIFIED',
                               detail='字幕と合わない時刻：' + '、'.join(f'{t}秒' for t in unmatched[:8]))
        transcript = (folder / 'transcript.md').read_text(encoding='utf-8')
        body = transcript.split('---\n', 2)[-1]
        # Reject wholesale caption copying and multiple timestamped caption lines.
        if body.strip() in text or len(re.findall(r'^\[\d+(?:\.\d+)?\] ', text, re.M)) > 1:
            raise StageFailure('TRANSCRIPT_IN_RESEARCH')
        cues = json.loads((folder / 'cues.json').read_text(encoding='utf-8'))
        normalized_note = re.sub(r'\s+', '', text)
        copied = [cue for _, cue in cues if len(re.sub(r'\s+', '', cue)) >= 40
                  and re.sub(r'\s+', '', cue) in normalized_note]
        if len(copied) >= 3 or any(len(cue) >= 120 for cue in copied):
            raise StageFailure('LONG_CAPTION_COPY_IN_RESEARCH')
        if len(text) > 24000:
            raise StageFailure('RESEARCH_TOO_LONG')
        return {'okf_valid': True}

    def catalog(self, row):
        self.boundary()
        self.git('fetch', 'origin')
        remote, _ = receipt.collect_remote_branch_videos(root=self.repo, fetch_remote=False)
        if row['video_id'] in remote:
            raise StageFailure('REMOTE_DUPLICATE_BEFORE_SAVE')
        folder = self.folder(row)
        intent = folder / 'catalog_intent.json'
        if intent.exists():
            rel = json.loads(intent.read_text(encoding='utf-8'))
        else:
            rel = f'research/{date.today().isoformat()}-{row["video_id"]}-subtitle-switch.md'
            atomic_json(intent, rel)
        if not re.fullmatch(r'research/\d{4}-\d{2}-\d{2}-' + re.escape(row['video_id']) + r'-subtitle-switch\.md', rel):
            raise StageFailure('RESEARCH_PATH_INVALID')
        row['research_path'] = rel
        path = self.repo / rel
        path.parent.mkdir(exist_ok=True)
        text = (folder / 'research.md').read_text(encoding='utf-8')
        if path.exists() and path.read_text(encoding='utf-8') != text:
            raise StageFailure('RESEARCH_CONFLICT')
        registry = json.loads((self.repo / 'registry.json').read_text(encoding='utf-8'))
        matching = [r for r in registry['records'] if r.get('video_id') == row['video_id']]
        if len(matching) > 1 or (matching and matching[0].get('research_path') != rel):
            raise StageFailure('REGISTRY_CONFLICT')
        if not matching:
            registry['records'].append({
                'record_id': f'youtube:{row["video_id"]}', 'video_id': row['video_id'],
                'canonical_url': row['url'], 'research_path': rel,
                'research_date': date.today().isoformat(),
                'status': 'RESEARCH_RECORDED; NOTEBOOK_PENDING',
                'transcript_sha256': row['receipts']['transcript']['sha256'],
            })
        path.write_text(text, encoding='utf-8', newline='\n')
        atomic_json(self.repo / 'registry.json', registry)
        knowledge.build_video_knowledge_catalog(root=self.repo, write_path=self.repo / CATALOG)
        return {'research_path': rel}

    def github(self, row):
        self.boundary()
        try:
            self.review(row)
        except StageFailure as exc:
            exc.no_write = True
            raise
        paths = [row['research_path'], 'registry.json', CATALOG]
        local_note = (self.repo / row['research_path']).read_text(encoding='utf-8')
        reviewed_note = (self.folder(row) / 'research.md').read_text(encoding='utf-8')
        if local_note != reviewed_note:
            raise StageFailure('PUBLISH_NOTE_DIFFERS_FROM_REVIEW', no_write=True)
        try:
            for rel in paths:
                text = (self.repo / rel).read_text(encoding='utf-8')
                receipt.scan_forbidden_keys(json.loads(text) if rel.endswith('.json') else text)
        except ValueError:
            raise StageFailure('FORBIDDEN_PUBLISH_CONTENT', no_write=True) from None
        staged = self.git('diff', '--cached', '--name-only').stdout.splitlines()
        changed = self.git('diff', '--name-only').stdout.splitlines()
        if any(path not in paths for path in staged + changed):
            raise StageFailure('UNRELATED_GIT_CHANGES', no_write=True)
        manifest = {path: hashlib.sha256((self.repo / path).read_text(encoding='utf-8').replace('\r\n', '\n').encode('utf-8')).hexdigest() for path in paths}
        atomic_json(self.folder(row) / 'github_manifest.json', manifest)
        self.git('add', '--', *paths)
        diff = self.git('diff', '--cached', '--quiet', check=False)
        if diff.returncode == 1:
            self.git('commit', '-m', f'Save research {row["video_id"]}\n\nAI-Agent: codex')
        elif diff.returncode != 0:
            raise StageFailure('GIT_DIFF_FAILED')
        head = self.git('rev-parse', 'HEAD').stdout.strip()
        atomic_json(self.folder(row) / 'github_head.json', head)
        # Ordinary push only, no force or default-branch target.
        pushed = self.git('push', 'origin', f'{head}:refs/heads/{self.branch}', check=False)
        if pushed.returncode:
            row['github_push_failed'] = True
            raise StageFailure('GITHUB_PUSH_FAILED')
        row.pop('github_push_failed', None)
        result = self.readback('github', row)
        if result is None:
            raise StageFailure('WRITE_RESULT_UNKNOWN', waiting=True)
        return result

    def readback(self, stage, row):
        if stage == 'notebook':
            # First reconcile every previously attempted source. Only a source
            # without a persisted send marker may be added; unknown sends are
            # never repeated. This also resumes a crash between the two adds.
            self.review(row)
            return self.notebook_step(row, allow_add=True)
        folder = self.folder(row)
        if not (folder / 'github_manifest.json').exists() or not (folder / 'github_head.json').exists():
            return None
        self.boundary()
        self.git('fetch', 'origin')
        head = json.loads((folder / 'github_head.json').read_text(encoding='utf-8'))
        remote = self.git('rev-parse', f'origin/{self.branch}', check=False)
        if remote.returncode:
            return None
        actual = remote.stdout.strip()
        if head != actual:
            ancestor = self.git('merge-base', '--is-ancestor', head, f'origin/{self.branch}', check=False)
            if ancestor.returncode != 0:
                return None
        manifest = json.loads((folder / 'github_manifest.json').read_text(encoding='utf-8'))
        for path, digest in manifest.items():
            body = self.git('show', f'{head}:{path}').stdout
            if hashlib.sha256(body.replace('\r\n', '\n').encode('utf-8')).hexdigest() != digest:
                return None
        if head != actual:
            note_path = row['research_path']
            current_note = self.git('show', f'origin/{self.branch}:{note_path}').stdout
            digest = hashlib.sha256(current_note.replace('\r\n', '\n').encode('utf-8')).hexdigest()
            if digest != manifest[note_path]:
                return None
        return {'remote_head': actual, 'verified_commit': head, 'files_verified': len(manifest)}

    def retry_github_push(self, row):
        """Retry only the saved commit after a definite nonzero push and readback."""
        if not row.get('github_push_failed'):
            raise StageFailure('WRITE_RESULT_UNKNOWN', waiting=True)
        self.boundary()
        folder = self.folder(row)
        head = json.loads((folder / 'github_head.json').read_text(encoding='utf-8'))
        if not isinstance(head, str) or not re.fullmatch(r'[0-9a-f]{40}', head):
            raise StageFailure('GITHUB_SAVED_HEAD_INVALID')
        manifest = json.loads((folder / 'github_manifest.json').read_text(encoding='utf-8'))
        for path, digest in manifest.items():
            body = self.git('show', f'{head}:{path}').stdout
            if hashlib.sha256(body.replace('\r\n', '\n').encode('utf-8')).hexdigest() != digest:
                raise StageFailure('GITHUB_SAVED_COMMIT_MISMATCH')
        remote = self.git('ls-remote', '--heads', 'origin', f'refs/heads/{self.branch}').stdout.strip()
        if remote:
            remote_head = remote.split()[0]
            if self.git('merge-base', '--is-ancestor', remote_head, head, check=False).returncode:
                raise StageFailure('GITHUB_NON_FAST_FORWARD')
        pushed = self.git('push', 'origin', f'{head}:refs/heads/{self.branch}', check=False)
        if pushed.returncode:
            raise StageFailure('GITHUB_PUSH_FAILED')
        row.pop('github_push_failed', None)
        result = self.readback('github', row)
        if result is None:
            raise StageFailure('WRITE_RESULT_UNKNOWN', waiting=True)
        return result

    def notebook(self, row):
        try:
            self.review(row)
        except StageFailure as exc:
            exc.no_write = True
            raise
        result = self.notebook_step(row, allow_add=True)
        if result is None:
            raise StageFailure('WRITE_RESULT_UNKNOWN', waiting=True)
        return result

    def notebook_step(self, row, allow_add):
        if not self.nb_client.auth_check_passive():
            raise StageFailure('NOTEBOOK_LOGIN_EXPIRED', waiting=True, global_stage=True, no_write=True)
        sources = self.nb_client.list_sources()
        pre = nb.classify_sources(sources, row['video_id'], row['title'], self.nb_client)
        if pre['ambiguous'] or pre['youtube_source_id']:
            raise StageFailure('NOTEBOOK_EXISTING_SOURCES_NEED_REVIEW', no_write=True)
        folder = self.folder(row)
        plans = [('transcript', pre['transcript_source_id'], nb.transcript_title, 'transcript.md'),
                 ('research', pre['research_note_source_id'], nb.research_note_title, 'research.md')]
        missing = sum(sid is None for _, sid, _, _ in plans)
        limit = int(self.config.get('source_limit', 300))
        row['notebook_sources_used'] = len(sources)
        row['notebook_capacity_warning'] = len(sources) + missing >= limit - 20
        # No additions at all when the pair would exceed capacity.
        if len(sources) + missing > limit:
            raise StageFailure('NOTEBOOK_CAPACITY', waiting=True, no_write=True)
        # Do not send an unattempted remainder while another add is unknown.
        # Validate all existing documents before any new addition.
        for kind, sid, _, filename in plans:
            if sid is None and (folder / f'notebook_{kind}_inflight.json').exists():
                return None
            if sid is not None:
                expected = (folder / filename).read_text(encoding='utf-8')
                if not nb.readback_matches(expected, self.nb_client.get_fulltext(sid))['match']:
                    raise StageFailure('NOTEBOOK_READBACK_MISMATCH')
        receipts = {}
        for kind, sid, title_fn, filename in plans:
            expected = (folder / filename).read_text(encoding='utf-8')
            marker = folder / f'notebook_{kind}_inflight.json'
            if sid is None:
                if not allow_add or marker.exists():
                    return None
                atomic_json(marker, {'sent': True})
                try:
                    self.nb_client.add_text(title_fn(row['video_id'], row['title']), expected)
                except Exception:
                    pass  # Always reconcile by reading, even if add returned an ID.
                after = self.nb_client.list_sources()
                post = nb.classify_sources(after, row['video_id'], row['title'], self.nb_client)
                sid = post['transcript_source_id' if kind == 'transcript' else 'research_note_source_id']
                if post['ambiguous'] or not sid:
                    raise StageFailure('WRITE_RESULT_UNKNOWN', waiting=True)
            actual = self.nb_client.get_fulltext(sid)
            if not nb.readback_matches(expected, actual)['match']:
                raise StageFailure('NOTEBOOK_READBACK_MISMATCH')
            receipts[kind] = sid
        if receipts['transcript'] == receipts['research']:
            raise StageFailure('NOTEBOOK_SOURCES_NOT_DISTINCT')
        indices = self.dom(row)
        if not indices or indices[0] == indices[1] or None in indices:
            raise StageFailure('DOM_READBACK_UNKNOWN', waiting=True)
        row['notebook_sources_used'] = len(self.nb_client.list_sources())
        return {'source_ids': receipts, 'Index_note': indices[0], 'Index_transcript': indices[1],
                'sources_used': row['notebook_sources_used'], 'is_mock': self.is_mock}

    def dom_readback(self, row):
        client = browser.CDPClient(port=int(self.config.get('cdp_port', 9222)))
        tabs = client.list_tabs()
        # Never accept a tab from another notebook or automatically launch/login.
        tabs = [tab for tab in tabs if self.config['notebook_id'] in tab.get('url', '')]
        if len(tabs) != 1:
            return None
        result = browser.readback_notebook_sources_via_cdp(client, tabs[0], row['video_id'], row['title'])
        if not result.get('independent_sources_distinct'):
            return None
        return result.get('research_note_item_index'), result.get('transcript_item_index')
