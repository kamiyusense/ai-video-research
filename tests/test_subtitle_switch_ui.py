"""Web page contract and entry point; no GUI, model or browser is launched."""
import sys
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

APP = Path(__file__).resolve().parents[1] / 'automation/subtitle-switch'
sys.path.insert(0, str(APP))
import switch_app
import web_server
import preview_v4


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.tags = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        self.tags.append((tag, attrs))


def test_web_entry_delegates_without_tk_or_services():
    with patch.object(web_server, 'run') as run:
        switch_app.main('fake-config.json')
    run.assert_called_once_with('fake-config.json')


def test_page_contains_all_controls_and_accessible_checkboxes():
    page = web_server.render_page(web_server.boot_data(), auth='?key=fixture')
    parser = Elements()
    parser.feed(page)
    assert len(parser.ids) == len(set(parser.ids))
    for identity in ('title', 'rows', 'check-all', 'urls', 'correction', 'reject-reason',
                     'question-panel', 'question', 'answer', 'grok', 'body-cat', 'face-cat'):
        assert identity in parser.ids
    assert sum(attrs.get('id') == 'check-all' for _, attrs in parser.tags) == 1
    saves = [a['data-action'] for t, a in parser.tags if t == 'button' and a.get('class') == 'save']
    assert saves == ['manual', 'selected']
    assert all(a.get('src', '').startswith('/') for t, a in parser.tags if t in ('script', 'img') and 'src' in a)
    assert 'AI動画字幕図書館司書猫さん' in page
    assert 'AI動画字幕図書館司書さん' not in page
    assert 'fonts/ZenMaruGothic-Black-title.ttf?key=fixture' in page
    assert any(t == 'button' and a.get('id') == 'grok' and 'disabled' in a for t, a in parser.tags)


def test_preview_is_exact_application_artwork_without_network_calls():
    path = APP.parents[1] / 'docs/design/preview-v4.html'
    page = path.read_text(encoding='utf-8')
    assert page == preview_v4.preview()
    assert (APP / 'web/style.css').read_text(encoding='utf-8') in page
    assert (APP / 'web/icons.svg').read_text(encoding='utf-8') in page
    assert '"demo": true' in page
    assert 'https://fonts.' not in page
    assert 'cdn.' not in page


def test_svg_icons_are_local_and_have_all_used_symbols():
    source = (APP / 'web/icons.svg').read_text(encoding='utf-8')
    ET.fromstring(source)
    page = (APP / 'web/index.html').read_text(encoding='utf-8')
    import re
    assert set(re.findall('href="#([^"]+)"', page)) <= set(re.findall('id="([^"]+)"', source))
    assert 'image' not in source
