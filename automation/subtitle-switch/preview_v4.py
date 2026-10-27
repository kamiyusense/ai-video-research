"""Build the file:// preview from the application's actual HTML, CSS and SVG."""
from pathlib import Path

from web_server import ROOT, boot_data, render_page, table_row


def preview():
    examples = [
        ('aaaaaaaaaaa', 'Claude Codeの使い方と、これからのAI研究', 'AIのある暮らし', '2026-10-26', 'ja', 'AIエージェント', '気になる研究テーマ', 'intake', 'pending', None),
        ('bbbbbbbbbbb', '小さな自動化を、確かな仕組みに育てる', 'テクノロジー研究室', '2026-10-25', 'ja', '自動化', '登録チャンネルから', 'review', 'attention', 54),
        ('ccccccccccc', 'Notebookでつながる、学びのライブラリ', '今日のAIノート', '2026-10-24', 'en', '知識管理', '関連する動画の候補', 'notebook', 'waiting', 'UNKNOWN'),
    ]
    rows = []
    for vid, title, channel, published, lang, theme, reason, stage, status, used in examples:
        row = dict(video_id=vid, title=title, channel=channel, published_at=published, lang=lang, theme=theme,
                   reason=reason, stage=stage, status=status, rejected=False, rejection_reason='')
        if used is not None:
            row['notebook_sources_used'] = used
        if status == 'waiting':
            row['status_reason'] = 'NOTEBOOK_LOGIN_EXPIRED'
        rows.append(table_row(row))
    data = {**boot_data(), 'font': 0, 'demo': True, 'state': {
        'rows': rows, 'checked': ['aaaaaaaaaaa'], 'cat': 'idle', 'busy': False, 'answer': '',
        'notice': '気になる動画を選んで、あなたの図書館へ。これは確認用の静止ページです。'}}
    return render_page(data, '../../automation/subtitle-switch/assets/')


if __name__ == '__main__':
    target = ROOT.parents[1] / 'docs/design/preview-v4.html'
    target.write_text(preview(), encoding='utf-8')
