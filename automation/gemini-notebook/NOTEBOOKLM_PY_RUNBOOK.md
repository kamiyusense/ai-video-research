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

**CLIコマンドの確認状況**（[検品ループ記録](../../docs/REVIEW_LOOP_LOG.md) 7）: ツールの内部で呼ぶ `notebooklm` CLIのうち、実CLIで確認済みなのは `auth check --test --passive`・`source list --json`・`source fulltext --json` の3つ（相棒PCの実機dry-run）。PR #14 `1e128aa` までの版は存在しない `source add-text` を呼んでいたため、その版で `--live` を使うと必ず失敗する（T5 `4831a12` で修正）。テキスト追加は `notebooklm source add - --type text --title <題> --json --notebook <ID>`（本文は標準入力）で、形は実機調査（ループ記録7）で判明したものだが、書き込みの実行は**未確認（UNVERIFIED）**。合わなければ `notebooklm_py_ingest.py` の `NotebookLmCliClient.COMMANDS` を直す（コード変更は作業役＋検品役のループで）。

> **たとえ**: 司書さんへの指示書のうち「点検・一覧・中身を読む」は実物で試した。「本を置く」は書き方を調べただけで、まだ実際に置いたことはない。

## 1. 起動方法

リポジトリのフォルダで、次の形で起動する（`uv` が notebooklm-py 0.8.5 と youtube-transcript-api 1.2.2 入りの一時的な環境を用意してくれる）。

```
uv run --python 3.12 --with notebooklm-py==0.8.5 --with youtube-transcript-api==1.2.2 python automation/gemini-notebook/notebooklm_py_ingest.py <引数>
```

> **たとえ**: 道具箱（Python 3.12・notebooklm-py 0.8.5・youtube-transcript-api 1.2.2）をその場で借りてきて、作業が終わったら返す。

NotebookのIDは `e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7`（`registry.json` の `notebook_sources.notebook_id` と同じ）。

## 2. 手順（この順番を守る）

### 手順1: 健康診断（health・読み取りのみ）

```
uv run --python 3.12 --with notebooklm-py==0.8.5 --with youtube-transcript-api==1.2.2 python automation/gemini-notebook/notebooklm_py_ingest.py health --notebook-id e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7
```

- 結果はJSON。`status` が `OK`（終了コード0）か `ATTENTION`（1）か `AUTH_EXPIRED`（3）。
- `AUTH_EXPIRED` なら、ここで止めてログインし直す（0章の決まり）。
- 見る項目: `registry_ids_missing_in_notebook`（台帳にあるのに棚に無い）、`notebook_sources_not_in_registry`（棚にあるのに台帳に無い研究ノート・字幕原文）、`videos_without_transcript_okf`（字幕原文がまだの動画）、`sources_without_published_at`（荷札に投稿日時が無い・`UNKNOWN` の字幕全文・研究ノート。2026-10-20時点では `a32a70ec` が該当する見込み）。投稿日時を確かめるため、字幕全文・研究ノートの本文を読む（読み取りのみ）。

> **たとえ**: 棚と台帳を見比べて「無くなった本」「台帳に書き忘れた本」「まだ原本が届いていない動画」を数えるだけ。何も動かさない。

### 手順2: 計画を見る（dry-run・既定）

```
uv run --python 3.12 --with notebooklm-py==0.8.5 --with youtube-transcript-api==1.2.2 python automation/gemini-notebook/notebooklm_py_ingest.py --video-id <動画ID> --video-title "<YouTubeのタイトル>" --research-md research/<研究ノート>.md --notebook-id e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7
```

- `--live` を付けないので書き込まない。棚の一覧を読んで、足りない方だけを `plan` に出す。
- `status` の意味:
  - `NO_OP`: 両方揃っている。
  - `DRY_RUN_PLAN`: `plan` に書いた分を足す予定。
  - `AMBIGUOUS_EXISTING_SOURCES`: 見分けがつかないので止まった。
  - `TRANSCRIPT_UNAVAILABLE`: 字幕全文がどこからも取れなかった（Notebook内YouTubeソースの本文・YouTube字幕とも無し）ので、何も書かずに止まった。
  - `AUTH_EXPIRED_HALT`: ログイン切れ。
- 字幕cueのJSONがあれば `--cues-json` で渡す。無ければ、①Notebook内にその動画のYouTubeソースがあればその本文、②無ければ実行しているPCからYouTubeの字幕（youtube-transcript-api → 既存のYouTube字幕取得の順）を使う。投稿日時は実行PCからYouTubeの視聴ページで取る。**2026-10-20 22:42 JST の方針転換**で字幕全文は時刻なしが正になり、本文は発話を段落にまとめた読みやすい形（発話そのものは変えない）。場面の時刻リンクは研究ノート側に付く。字幕全文・研究ノートの両方の荷札に `published_at`（取れなければ `UNKNOWN`）、字幕全文の荷札に取得元 `acquisition_method` と `cue_count` が入る。
- `--video-title` はNotebookのYouTubeソースを見つけるのに使う。YouTube上のタイトルと同じものを渡す。
- `--notebook-id` を付けないと、棚を読まずに「両方足す」とだけ出す（`DRY_RUN_PLAN_OFFLINE`）。

> **たとえ**: 「この2冊のうち、こっちだけ足します」という計画書を作って見せるだけ。

#### 参考: URLを貼るだけの通し運転（auto_research_pipeline）のdry-run

通し運転からも同じ計画を見られる（T9、PR #14）。`--dry-run` ではGitHub・Notebook・Driveへの書き込みは0で、`--live` を付けても書き込まない。

```
uv run --python 3.12 --with notebooklm-py==0.8.5 --with youtube-transcript-api==1.2.2 python automation/gemini-notebook/auto_research_pipeline.py "https://www.youtube.com/watch?v=<動画ID>" --dry-run --notebook-backend notebooklm-py --notebook-id e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7
```

- `--notebook-id` を付けると棚の一覧を読み、字幕と投稿日時を取りに行く（読み取りのみ）。付けなければ棚も字幕も見ずに `DRY_RUN_PLAN_OFFLINE` を返す。
- `--notebook-id` 付きのdry-runでは、YouTubeの題名と投稿日時も読み取りで取り、計画の題名を本番と同じにする（字幕トラック情報は使わない）。題名が取れなかったとき・`--notebook-id` 無しのときは、仮の `YouTube Video <動画ID>` になり、取れなかった理由を `notes` に書く。

出力例（オフラインテストの偽の棚・偽の題名取得（題名「テスト用の動画タイトル」）で取得。最後のJSONから抜粋）:

```
[8/8] [DRY RUN] notebooklm-py でNotebookへの追加予定を確認します（書き込みなし）...
  - 追加予定: transcript / 【字幕原文】テスト用の動画タイトル [dQw4w9WgXcQ] / youtube:dQw4w9WgXcQ:transcript
  - 追加予定: research_note / 【研究ノート】テスト用の動画タイトル [dQw4w9WgXcQ] / youtube:dQw4w9WgXcQ:research
[DRY RUN] Notebook計画: DRY_RUN_PLAN。GitHub・Notebook・Driveへの書き込みゼロで終了します。
{
  "status": "DRY_RUN_PLAN",
  "notebook_ingest": {
    "status": "DRY_RUN_PLAN",
    "live": false,
    "plan": ["transcript", "research_note"],
    "plan_details": [
      {"kind": "transcript", "title": "【字幕原文】テスト用の動画タイトル [dQw4w9WgXcQ]", "logical_id": "youtube:dQw4w9WgXcQ:transcript"},
      {"kind": "research_note", "title": "【研究ノート】テスト用の動画タイトル [dQw4w9WgXcQ]", "logical_id": "youtube:dQw4w9WgXcQ:research"}
    ],
    "writes": [],
    "new_source_ids": [],
    "published_at": "2026-10-01"
  }
}
```

> **たとえ**: 通し運転の「下見モード」。最後に「棚に置く予定の2冊（題名と荷札番号）」の一覧だけ見せて、何も置かずに帰ってくる。

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

### 手順6: URL単体ソースの移行計画（migrate-plan・読み取りのみ）

2026-10-20 22:42 JST に相棒が「URL単体ソース15件は削除してよい。ただし先に字幕全文OKFを登録→読み戻し確認してから」と判断した。その順番の計画を出す（T10、PR #14）。**このツールは削除を実行しない**（削除の機能そのものが無い）。

```
uv run --python 3.12 --with notebooklm-py==0.8.5 --with youtube-transcript-api==1.2.2 python automation/gemini-notebook/notebooklm_py_ingest.py migrate-plan --notebook-id e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7
```

- 棚の type=youtube の資料ごとに、①その動画の字幕全文OKF・研究ノートOKFの有無、②字幕の取得元の順（Notebook内YouTubeソースの本文 → youtube-transcript-api）、③追加予定（題名・logical_id）、④「読み戻し一致の後にだけ」削除してよいURLソースID、を返す。
- 動画IDは、棚の「【研究ノート】題 [ID]」「【字幕原文】題 [ID]」→ GitHubの研究ノート本文の順に、YouTubeソースの題名で探す。見つからなければ `VIDEO_ID_UNKNOWN` として削除予定から外す。
- `status`: `ADD_THEN_DELETE`（先に字幕全文OKFを足す）／`READY_TO_DELETE_URL_SOURCE`（`published_at` 入りの字幕全文OKFが既にある。削除前に読み戻しをもう一度）／`AMBIGUOUS_EXISTING_SOURCES`／`VIDEO_ID_UNKNOWN`。
- 既存の字幕全文OKFに `published_at` が無い動画（`pRfC1DILDEM` の `a32a70ec`）は、入り版の追加を `to_add_pending_approval`、旧版を `replace_pending_approval` に出す（置き換え＝削除を含むので相棒の承認待ち。待ちリスト7）。
- 実際の追加は手順2〜4（動画ごと、承認のあと `--live`）、削除は読み戻し一致を確かめてから相棒PCの作業役が行う。

出力例（オフラインテストの実一覧写しで取得。15件のうち1件だけ抜粋。写しには本文が無いため Notebook内本文の `available` は false）:

```
{
  "status": "DRY_RUN_MIGRATION_PLAN",
  "url_source_count": 15,
  "video_id_unknown_count": 0,
  "delete_after_readback_count": 15,
  "deletion_executed": false,
  "items": [
    {
      "youtube_source_id": "d1fef625-ac11-40f7-b0d4-cfe2ae46c9a2",
      "youtube_title": "AIが資料整理する新ルールOKFをサクッと理解する",
      "video_id": "u3ka_AAb8qE",
      "transcript_source_order": [
        {
          "method": "NOTEBOOK_YOUTUBE_SOURCE_FULLTEXT",
          "source_id": "d1fef625-ac11-40f7-b0d4-cfe2ae46c9a2",
          "available": false,
          "chars": 0
        },
        {
          "method": "YOUTUBE_TRANSCRIPT_API",
          "available": "UNKNOWN（実行PCで取得して確認）"
        }
      ],
      "existing": {
        "transcript_okf": null,
        "transcript_published_at": null,
        "research_note_okf": "65b634f5-f9ad-4c6e-930d-744970701c0b"
      },
      "to_add": [
        {
          "kind": "transcript",
          "title": "【字幕原文】AIが資料整理する新ルールOKFをサクッと理解する [u3ka_AAb8qE]",
          "logical_id": "youtube:u3ka_AAb8qE:transcript"
        }
      ],
      "notes": [
        "URLソースの削除は、追加した字幕全文OKFの読み戻し一致を確かめた後だけ（その前は削除しない）。"
      ],
      "status": "ADD_THEN_DELETE",
      "delete_after_readback": [
        "d1fef625-ac11-40f7-b0d4-cfe2ae46c9a2"
      ]
    }
  ]
}
```

> **たとえ**: 「動画のURLだけ書いた貼り紙」15枚を、本物の原本（字幕全文）に差し替える段取り表。原本を棚に置いて中身を確かめた貼り紙だけ、はがしてよい印を付ける。はがす作業そのものは、この表ではやらない。

## 3. 確認済み・未確認の区別（2026-10-20 時点）

- **確認済み（テスト）**: 偽クライアントと実Notebook一覧の写し（`tests/fixtures/notebook_sources_20261020.json`、id/type/titleのみ）を使ったオフラインテスト。PR #14 `4831a12` 時点で158件、T9時点で195件、T10時点で211件OK（ネット遮断・同名ブランチのローカルコピー）。通し運転（手順3〜8）は字幕取得・研究ノート保存・Git・Notebookをすべて偽物にしたテストで確認。
- **未確認（UNVERIFIED / UNKNOWN）**: 登録のdry-run（書き込み0）は相棒PCで実機実行済み（`1e128aa`、ループ記録7）。`--live`（書き込み）と `health` は実機ではまだ一度も実行していない。`add_text` 後にソースへ付く type も不明。 `migrate-plan` も実機未実行（Notebook内YouTubeソースの本文が実際に取れるか・その文字数はUNKNOWN）。
