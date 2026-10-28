"""Offline tests for selection, metadata caching and bounded question payloads."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'automation/subtitle-switch'))
import ask_research
import metadata
import switch_app
import services
import export_icon_png


def test_check_selection_and_rejection():
    checked = switch_app.toggle_checked(set(), 'a')
    assert switch_app.save_targets(SimpleNamespace(data={'videos': {'a': {'rejected': False}}}), 'selected', selected=checked) == {'a'}
    assert not switch_app.toggle_checked(checked, 'a', rejected=True)
    assert not switch_app.toggle_checked(checked, 'a')


def test_notebook_states():
    assert '未実行' in switch_app.notebook_usage({})
    assert switch_app.notebook_usage({'status_reason': 'NOTEBOOK_LOGIN_EXPIRED'}) == 'Notebook 未接続'
    assert '読み取り失敗' in switch_app.notebook_usage({'stage': 'notebook', 'status_reason': 'bad'})
    assert switch_app.notebook_usage({'notebook_sources_used': 42}) == '42'


def test_metadata_cache_and_failures(tmp_path):
    rows = [{'video_id': 'aaaaaaaaaaa', 'url': 'https://example.invalid', 'theme': ''}]
    calls, updates = [], []
    def fake(args):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout=json.dumps({'id': 'aaaaaaaaaaa', 'channel': 'A', 'language': 'ja', 'upload_date': '20261027'}))
    for _ in range(2):
        metadata.refresh_metadata(rows, tmp_path / 'cache.json', fake, sleep=lambda _: None, notify=lambda *args: updates.append(args))
    assert len(calls) == 1
    assert updates[-1][1] == {'channel': 'A', 'lang': 'ja', 'published_at': '2026-10-27', 'ja_dub': '日本語'}
    metadata.refresh_metadata([{'video_id': 'bbbbbbbbbbb', 'url': 'bad'}], tmp_path / 'cache.json', lambda _: SimpleNamespace(returncode=1), notify=lambda *args: updates.append(args))
    assert '取得失敗' in updates[-1][1]['channel']


def test_question_bounds_and_local_research_only(tmp_path):
    repo = tmp_path / 'repo'
    research = repo / 'research'
    research.mkdir(parents=True)
    (research / 'note.md').write_text('根拠 https://www.youtube.com/watch?v=aaaaaaaaaaa&t=4s', encoding='utf-8')
    records = [{'record_path': 'research/note.md'}, {'record_path': 'notes/no.md'}]
    with patch.object(ask_research.knowledge, 'build_video_knowledge_catalog', return_value=({}, records)), patch.object(ask_research.knowledge, 'analyze_query_intent', return_value={}), patch.object(ask_research.knowledge, 'search_github_knowledge', return_value=([records[0]], [])):
        sent = []
        def fake(args, **kwargs):
            sent.append(kwargs['stdin'])
            return SimpleNamespace(returncode=0, stdout='回答 https://www.youtube.com/watch?v=aaaaaaaaaaa&t=999s')
        answer = ask_research.ask('質問', repo, tmp_path / 'log', runner=fake)
        assert 'research/note.md' in answer and '&t=4s' in answer
        assert '&t=999s' not in answer
        assert sent[0] in (tmp_path / 'log/questions.jsonl').read_text(encoding='utf-8') or json.loads((tmp_path / 'log/questions.jsonl').read_text(encoding='utf-8'))['sent'] == sent[0]
        try:
            ask_research.ask('質問', repo, repo / 'log', runner=fake)
            assert False
        except ValueError:
            pass
        assert len(sent) == 1
        try:
            ask_research.build_prompt('x' * 2001, repo)
            assert False
        except ValueError:
            pass
    assert not hasattr(ask_research, 'GROK_REASON')


def test_title_and_control_dimensions():
    import ui_design
    readme = (Path(__file__).resolve().parents[1] / 'automation/subtitle-switch/README.md').read_text(encoding='utf-8')
    assert switch_app.APP_NAME in readme
    for factor in (1, 1.25, 1.5):
        line = round(20 * factor)
        assert ui_design.minimum_control_height(line, round(32 * factor), round(12 * factor)) >= line + 2 * round(12 * factor)


def test_metadata_requests_are_spaced_and_cached(tmp_path):
    rows = [{'video_id': str(n) * 11, 'url': 'https://example.invalid'} for n in range(3)]
    events = []
    def fake(args):
        index = sum(item == 'request' for item in events)
        events.append('request')
        return SimpleNamespace(returncode=0, stdout=json.dumps({'id': rows[index]['video_id']}))
    metadata.refresh_metadata(rows, tmp_path / 'cache.json', fake, sleep=lambda n: events.append(n))
    assert events == ['request', 2, 'request', 2, 'request']


def test_research_note_count_and_text_limits(tmp_path):
    repo = tmp_path / 'repo'
    research = repo / 'research'
    research.mkdir(parents=True)
    records = []
    for index in range(4):
        path = research / f'{index}.md'
        path.write_text(str(index) * 10000, encoding='utf-8')
        records.append({'record_path': f'research/{index}.md'})
    with patch.object(ask_research.knowledge, 'build_video_knowledge_catalog', return_value=({}, records)), patch.object(ask_research.knowledge, 'analyze_query_intent', return_value={}), patch.object(ask_research.knowledge, 'search_github_knowledge', return_value=(records, [])):
        prompt, names, _ = ask_research.build_prompt('質問', repo)
    assert len(names) == 3
    assert 'research/3.md' not in prompt
    assert sum(prompt.count(str(index) * 1000) * 1000 for index in range(3)) == 24000


def test_failed_metadata_is_not_retried_in_same_session(tmp_path):
    row = {'video_id': 'bbbbbbbbbbb', 'url': 'https://example.invalid'}
    calls, failures, values = [], set(), []
    def fake(args):
        calls.append(args)
        return SimpleNamespace(returncode=1)
    for _ in range(2):
        metadata.refresh_metadata([row], tmp_path / 'cache.json', fake, failures=failures, notify=lambda *args: values.append(args))
    assert len(calls) == 1
    assert '原因を直して' in values[-1][1]['channel']


def test_inbox_metadata_avoids_lookup_and_partial_values_show_progress(tmp_path):
    complete = {'video_id': 'aaaaaaaaaaa', 'url': 'unused', 'channel': '受け箱',
                'published_at': '2026-01-01', 'lang': 'ja', 'theme': '研究', 'reason': '理由'}
    calls, updates = [], []
    def fake(args):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            'id': 'bbbbbbbbbbb', 'channel': '取得値', 'upload_date': '20261027', 'language': 'en'}))
    partial = {'video_id': 'bbbbbbbbbbb', 'url': 'unused', 'channel': '既存'}
    metadata.refresh_metadata([complete, partial], tmp_path / 'cache.json', fake,
                              notify=lambda *args: updates.append(args))
    assert len(calls) == 1
    assert updates[0][1] == {**{key: complete[key] for key in ('channel', 'published_at', 'lang')}, 'ja_dub': '日本語'}
    assert updates[1][1]['published_at'] == '取得中…'
    assert updates[-1][1] == {'channel': '既存', 'published_at': '2026-10-27', 'lang': 'en', 'ja_dub': 'なし'}


def test_japanese_dub_track_is_detected_from_audio_formats():
    # Shapes measured with yt-dlp on 2026-10-28 (format_note '日本語 - dubbed-auto', language 'ja').
    dubbed = {'language': 'en-US', 'formats': [
        {'format_id': '234-0', 'vcodec': 'none', 'language': 'en-US', 'format_note': 'English (United States) original (default)'},
        {'format_id': '234-9', 'vcodec': 'none', 'language': 'ja', 'format_note': '日本語 - dubbed-auto'},
        {'format_id': '137', 'vcodec': 'avc1', 'language': None}]}
    plain = {'language': 'en', 'formats': [{'format_id': '140', 'vcodec': 'none', 'language': 'en'}],
             'automatic_captions': {'ja': []}}  # Japanese auto-captions are not dubbing
    assert metadata.japanese_dub(dubbed) == 'あり'
    assert metadata.japanese_dub(plain) == 'なし'
    assert metadata.japanese_dub({'language': 'ja', 'formats': [{'vcodec': 'none', 'language': 'ja'}]}) == '日本語'
    import web_server
    row = {'video_id': 'ccccccccccc', 'title': 'T', 'rejected': False, 'status': 'pending', 'stage': 'intake',
           'rejection_reason': '', 'completed_stages': []}
    cells = web_server.table_row(row, {'lang': 'en-US', 'ja_dub': 'あり'})['cells']
    assert cells[3]['text'] == 'en-US・吹替' and '自動吹き替え音声あり' in cells[3]['full']
    assert '吹き替え音声なし' in web_server.table_row(row, {'lang': 'en', 'ja_dub': 'なし'})['cells'][3]['full']


def test_common_command_uses_windows_no_window_flag():
    with patch.object(services.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True), \
         patch.object(services.subprocess, 'run') as run:
        services.command(['fake'])
    assert run.call_args.kwargs['creationflags'] == 0x08000000


def test_imported_git_and_notebook_adapters_hide_console():
    with patch.object(services.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True), \
         patch.object(services.subprocess, 'run', return_value=SimpleNamespace(stdout='ok')) as run:
        services.receipt.git('status')
        assert run.call_args.kwargs['creationflags'] == 0x08000000
        services.nb.NotebookLmCliClient('fake')._run('list_sources')
        assert run.call_args.kwargs['creationflags'] == 0x08000000


def test_compact_window_geometry_and_restoration():
    assert switch_app.MIN_WINDOW == (1100, 680)
    assert switch_app.window_geometry(1920, 1080) == '1344x760'
    saved = {'width': 1200, 'height': 700, 'x': 100, 'y': 50}
    assert switch_app.window_geometry(1920, 1080, saved) == '1200x700+100+50'
    assert switch_app.window_geometry(1920, 1080, {**saved, 'x': 1800}) == '1344x760'


def test_notebook_column_includes_heading_and_long_value():
    measure = lambda value: len(value) * 12
    assert switch_app.notebook_column_width(measure, []) >= measure('Notebook使用数') + 48
    value = '読み取り失敗：接続を確認してください'
    assert switch_app.notebook_column_width(measure, [value]) >= measure(value) + 24


def test_icon_png_export(tmp_path):
    import ui_design
    output = tmp_path / 'icon.png'
    export_icon_png.write_png(output, ui_design.icon_pixels('book', 32, True))
    data = output.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    assert data[12:16] == b'IHDR' and data[-8:-4] == b'IEND'
