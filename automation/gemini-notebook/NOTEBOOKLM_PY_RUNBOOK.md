# notebooklm-py 2ソース登録 手順書（相棒のPC用）

対象ツール: [notebooklm_py_ingest.py](notebooklm_py_ingest.py)（2026-10-20 追加、PR #14）
目的: 1本の動画について「字幕原文OKF」と「研究ノートOKF」を別々のソースとしてNotebookへ入れ、読み戻して確かめる。

> **たとえ**: Notebookは図書館の本棚、このツールは司書さん。まず棚を点検し（health）、次に「この本を足します」という計画書を作り（dry-run）、相棒がOKを出してから実際に本を置く（--live）。

## 0. 先に知っておくこと（安全）

| 決まり | たとえ |
|---|---|
| 書き込みは `--live` と `--notebook-id` の両方を付けた時だけ。付けなければ計画を見せるだけ | 「本当に置いていい？」の合図が2つ揃わないと棚に触らない |
| ログインが切れていたら、何も書かずに止まる。ツールはログインし直しをしない。相棒がブラウザでログインし直してから、もう一度最初（health）から | 図書館カードが切れていたら司書さんは作業をやめて、相棒に更新をお願いする |
| 書き込みの結果が分からなかった時（途中で通信が切れた等）は、もう一度送らない。棚の一覧を読み返して、入ったかどうかを確かめる | 「届いたか分からない荷物」をもう1個送らず、まず受け取り記録を見る |
| このツールには削除の機能が無い。消したい時は別途、相棒の判断と手作業で | 司書さんは本を足すだけで、捨てることはできない |
| 既にある資料と見分けがつかない時は、何も書かずに `AMBIGUOUS_EXISTING_SOURCES` で止まる | 似た本が2冊あって分からなければ、勝手に3冊目を置かない |
| 字幕全文はGitHubに保存しない（Notebookへの複製は 2026-10-20 に相棒が許可済み） | 原本のコピーは図書館にだけ置き、GitHubの台帳には荷札だけ書く |

**CLIコマンドの確認状況**（[検品ループ記録](../../docs/REVIEW_LOOP_LOG.md) 7）: ツールの内部で呼ぶ `notebooklm` CLIのうち、ログイン点検・一覧・本文取得は相棒PCの実機dry-runで動作確認済み。テキスト追加は `notebooklm source add - --type text --title <題> --json --notebook <ID>`（本文は標準入力）で、形は実機調査（ループ記録7）で判明したものだが、書き込みの実行は**未確認（UNVERIFIED）**。合わなければ `notebooklm_py_ingest.py` の `NotebookLmCliClient.COMMANDS` を直す（コード変更は作業役＋検品役のループで）。

> **たとえ**: 司書さんへの指示書のうち「点検・一覧・中身を読む」は実物で試した。「本を置く」は書き方を調べただけで、まだ実際に置いたことはない。

## 1. 起動方法

リポジトリのフォルダで、次の形で起動する（`uv` が notebooklm-py 0.8.5 入りの一時的な環境を用意してくれる）。

```
uv run --python 3.12 --with notebooklm-py==0.8.5 python automation/gemini-notebook/notebooklm_py_ingest.py <引数>
```

> **たとえ**: 道具箱（Python 3.12 と notebooklm-py 0.8.5）をその場で借りてきて、作業が終わったら返す。

NotebookのIDは `e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7`（`registry.json` の `notebook_sources.notebook_id` と同じ）。

## 2. 手順（この順番を守る）

### 手順1: 健康診断（health・読み取りのみ）

```
uv run --python 3.12 --with notebooklm-py==0.8.5 python automation/gemini-notebook/notebooklm_py_ingest.py health --notebook-id e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7
```

- 結果はJSON。`status` が `OK`（終了コード0）か `ATTENTION`（1）か `AUTH_EXPIRED`（3）。
- `AUTH_EXPIRED` なら、ここで止めてログインし直す（0章の決まり）。
- 見る項目: `registry_ids_missing_in_notebook`（台帳にあるのに棚に無い）、`notebook_sources_not_in_registry`（棚にあるのに台帳に無い研究ノート・字幕原文）、`videos_without_transcript_okf`（字幕原文がまだの動画）。

> **たとえ**: 棚と台帳を見比べて「無くなった本」「台帳に書き忘れた本」「まだ原本が届いていない動画」を数えるだけ。何も動かさない。

### 手順2: 計画を見る（dry-run・既定）

```
uv run --python 3.12 --with notebooklm-py==0.8.5 python automation/gemini-notebook/notebooklm_py_ingest.py --video-id <動画ID> --video-title "<YouTubeのタイトル>" --research-md research/<研究ノート>.md --notebook-id e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7
```

- `--live` を付けないので書き込まない。棚の一覧を読んで、足りない方だけを `plan` に出す。
- `status` の意味:
  - `NO_OP`: 両方揃っている。
  - `DRY_RUN_PLAN`: `plan` に書いた分を足す予定。
  - `AMBIGUOUS_EXISTING_SOURCES`: 見分けがつかないので止まった。
  - `TRANSCRIPT_SOURCE_MISSING`: 字幕も、NotebookのYouTubeソースも無いので、字幕原文を作れない。
  - `AUTH_EXPIRED_HALT`: ログイン切れ。
- 字幕cueのJSONがあれば `--cues-json` で渡す。無ければNotebook内YouTubeソースの本文を使う。その場合は `acquisition_method: NOTEBOOK_YOUTUBE_SOURCE_FULLTEXT`、`UNVERIFIED`、cue数0 として記録される（時刻なし）。
- `--video-title` はNotebookのYouTubeソースを見つけるのに使う。YouTube上のタイトルと同じものを渡す。
- `--notebook-id` を付けないと、棚を読まずに「両方足す」とだけ出す（`DRY_RUN_PLAN_OFFLINE`）。

> **たとえ**: 「この2冊のうち、こっちだけ足します」という計画書を作って見せるだけ。

### 手順3: 相棒の承認

- 計画（`plan`、足す資料の種類とタイトル）を相棒が確認し、「この動画のこの資料を足してよい」と明示的にOKを出す。
- OKが無ければ手順4へ進まない（Notebookへの書き込みは承認制）。

### 手順4: 実際に書き込む（--live）

手順2のコマンドに `--live` を足して実行する。

- 足りない方だけ追加し、追加後に一覧と本文を読み戻して確かめる。
  - 本文は、完全一致か「Markdown記号・空白を除いた正規化一致」なら合格。NotebookLMは表示用に `#` `**` `>` リンク記法・番号リスト・HTMLコメントを消し、改行を足すため。
  - 字幕原文と研究ノートが別IDであることも確認する。
- `status` の意味:
  - `SUCCESS_2_SOURCE_OKF`: このツールの範囲（登録と読み戻し）で合格。
  - `READBACK_MISMATCH`: 読み戻しが合わない。
  - `WRITE_RESULT_UNKNOWN`: 書いたか分からない。再送せず、手順1の health で確かめる。
- ツールの `SUCCESS_2_SOURCE_OKF` は、ロードマップの正式完成判定（自然言語QA確認などを含む）とは別物。

> **たとえ**: 本を置いたあと、棚に戻って「本当にあるか・中身が同じか・別の本として並んでいるか」を目で確かめる。

### 手順5: 結果を残す

- 出力JSONを作業役・検品役に渡し、`registry.json` の `notebook_sources` 更新と [docs/REVIEW_LOOP_LOG.md](../../docs/REVIEW_LOOP_LOG.md) への記録をループで行う。
- 最後にもう一度 health を流し、`registry_ids_missing_in_notebook` が0であることを確かめる。

## 3. 確認済み・未確認の区別（2026-10-20 時点）

- **確認済み（テスト）**: 偽クライアントと実Notebook一覧の写し（`tests/fixtures/notebook_sources_20261020.json`、id/type/titleのみ）を使ったオフラインテスト。PR #14 `011d719` 時点で、ネット遮断・同名ブランチのローカルコピーで152件OK。
- **未確認（UNVERIFIED / UNKNOWN）**: 実Notebookへの書き込み（`--live`）はまだ一度も実行していない（dry-runは実機で実行済み、ループ記録7）。`add_text` 後にソースへ付く type も不明。
