# 教訓カード

試したあとに指標が動かなければ、カードは消さない。状態を「取り消し」にする。

実行（通信なし、モデルなし）: `python3 automation/gemini-notebook/lesson_metrics.py`

スクリプトは `research/*.md` だけを数える。既存の Python は `automation/gemini-notebook/` にある。

## カードの型（5行まで）

- id / 日付: LC-（番号） / YYYY-MM-DD
- 教訓: （1行）
- 根拠: （研究ノートのパスなど）
- 効いたかの見方: （下の指標名）
- 状態: 試行中 / 採用 / 取り消し

## 指標名

- `core5_complete`: 見出しが「独自要約 / 動画目次・確認済みタイムライン（チャプター） / 詳細技術知識・再利用ノート / 主張・一次資料・時刻 / 限界」の5つ揃ったノート数。今の研究ノートの形。
- `example7_complete`: 「結論 / 動画の主張 / 自分の検索結果 / 提案 / UNKNOWN / 不都合な事実 / 確信度」が見出しとして全部あるノート数。この7つは現行ノートの型ではない。
- `notes_with_check_date`: `checked_at` の日付、または「確認日」と日付が同じ行にあるノート数。
- `primary_url_lines_with_check_date`: 主張・一次資料・公式資料の節で、YouTube以外のURLと確認日（または日付）が同じ行にある数。
- `unknown_bullets`: 行頭が `- UNKNOWN` の行数。
- `unknown_fields`: `: UNKNOWN` の数。`time_source: UNKNOWN` もここに入る。
- `time_source.<値>`: 本文に既にある `time_source:` の数。ラベルが無いノートは `notes_without_time_source_label`。フィールドは新設しない。
- `subtitle_quote_check`: いつも `SKIP`。字幕全文はGitHubに無いので照合しない。
