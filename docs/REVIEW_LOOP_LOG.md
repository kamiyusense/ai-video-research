# 検品ループ記録とユーザー待ちリスト

運用ルールはルート [AGENTS.md](../AGENTS.md) の「2026-10-20 検品ループ運用」。各周の判定はここに追記する（HEAD・テスト数は毎回実測）。

## 実測ベースライン（2026-10-20）

- `feature/gemini-notebook-research-loop-20261016` HEAD: `169dda0`（引き継ぎ書の `decdcb7` より進んでいる）
- `python3 -m unittest discover -s tests`（同名ローカルブランチ上）: 121件中120件PASS、1件ERROR
  - `test_auto_research_pipeline.TestAutoResearchPipeline.test_dry_run_no_side_effects`：dry-runなのに `verify_timestamps.fetch_player` がYouTubeへ通信し、ネットワーク不可の環境で `URLError`。「121 tests PASS」はネットワークが通る環境に依存している。
- 作業ブランチ名（`claude/...`）上では、ブランチ名チェックのテストがさらに2件「安全エラー」で落ちる（想定内）。
- Notebook側の実態（ユーザー手元の読み取り検品、`/mnt/project-files/Notebook検品レポート_20261020.md`）：53ソース。どの動画にも「字幕原文OKF」ソースは無い（Phase 7 未達）。

## ループ記録

| 周 | タスク | 担当 | 判定 | 根拠 |
|---|---|---|---|---|
| 0 | AGENTS.md に目標・守りルール・ループ手順を追加 | 検品指示役 | PASS（自己点検） | 既存「retry=0」との矛盾を解消する一文を追加済み |
| 1 | dry-runテストのネットワーク依存を除去 | 作業役（PR #14 `2f001d7`） | PASS（1周目） | 検品役が独立実測：YouTube通信不可の環境・同名ブランチで 122件OK。新テスト `test_dry_run_makes_no_network_calls` を旧コードに当てると失敗（検出力あり）。差分はdry-run分岐のみでLIVE経路は不変。dry-runの出力が動画IDだけのメタデータになる点は仕様変更として相棒に報告 |
| 2 | pRfC1DILDEM 字幕原文OKFをNotebookへ登録（許可1） | 作業役（ユーザーPC） | PASS（本文）／一部UNKNOWN | 新ソース `a32a70ec`（研究ノートと別ID）。取得元はNotebook内YouTubeソース `25c0f62e` のfulltext（時刻cue無し・cue_count 0・`UNVERIFIED`）。NotebookLMの読み戻しはMarkdownを表示用に整形するためSHA-256完全一致は不可、記号・空白除去後の比較で一致。荷札の動画ID・URL・論理IDは読み戻しで確認。本文中のHTMLコメントID（`AI_VIDEO_TRANSCRIPT_RAW:`）は読み戻しに出ないためUNKNOWN |
| 3 | RAG研究ノートを最新版へ置き換え（許可3） | 作業役（ユーザーPC） | 追加PASS・旧版削除を承認 | 新ソース `af697c8c`（GitHub `169dda0` 版 SHA-256 一致を確認後、`transcript_notebook_source_id` を1行追加して投入）。正規化比較で一致。件数53→55（増加は2件のみ）。旧 `610789c0` の削除を検品役が承認（バックアップ全文あり）→ 作業役が1回だけ削除し、一覧の読み戻し2経路で54件・`610789c0` 無し・他IDの変化なしを確認 |
| 4 | T2 notebooklm-py 2ソース自動登録モジュール | 作業役（PR #14 `2aaf20d`） | NEEDS_FIX（1周目） | テストは独立実測で136件OK（ネット遮断・同名ブランチ）。安全面はOK。ただし実Notebookのタイトル（`tests/fixtures/notebook_sources_20261020.json`）で重複判定を試すと、`【研究ノート】…[id]`・`動画研究_…id…` を研究ノートと認識せず、IDを含むmarkdownをYouTube扱いする → LIVEで研究ノートを二重登録する。修正指示済み |
| 5 | T2 修正（2周目） | 作業役（PR #14 `1e128aa`） | PASS | 独立実測：ネット遮断・同名ブランチで146件OK。fixtureの実タイトルで台帳31件を走査し、研究ノートは `registry.json` の `notebook_sources` と全件一致、字幕原文は pRfC1DILDEM の `a32a70ec` のみ検出、曖昧0件。動画タイトルを渡すとYouTubeは type=youtube のソースだけを拾う（pRfC→`25c0f62e`、sodTF→`2a738296`）。追加は add_text の1か所のみで削除口なし。CLIアダプタは実機未確認（UNVERIFIED） |
| 6 | T3 Notebook健康診断（読み取り専用） | 作業役（PR #14 `011d719`） | PASS（1周目） | 独立実測：ネット遮断・同名ブランチで152件OK。fixture＋台帳で OK・欠落0・台帳外0・字幕原文未登録30。字幕原文 `a32a70ec` を消した一覧では ATTENTION・欠落1を正しく報告。ログイン切れでは AUTH_EXPIRED で一覧も書き込みも呼ばない（書き込み0回を確認） |
| 7 | T2 実機dry-run（相棒PC、書き込み0） | 作業役（ユーザーPC、`1e128aa`） | PASS（計画）／add_textは不合格 | ログイン確認PASS、一覧54件→54件で変化なし。pRfC1DILDEM → `NO_OP`、u3ka_AAb8qE → 字幕原文だけ追加の計画（元本文 `d1fef625` 10201文字、`NOTEBOOK_YOUTUBE_SOURCE_FULLTEXT`）。CLIアダプタの list/fulltext/auth は実CLIと一致。ただし notebooklm-py 0.8.5 に `source add-text` は無く、live だと必ず失敗 → T5で修正 |
| 8 | T4 手順書とロードマップ現在地 | 作業役（PR #14 `3ff322b`） | NEEDS_FIX（1周目・軽微） | 152件OK。内容はループ記録2〜6と整合。ただし執筆後に判明した事実が未反映：(1) 実機dry-run済み（ループ記録7）なのに「実Notebookでは未実行」と記載、(2) 実CLIで確認済みは auth/list に加えて fulltext も、(3) add_text は実CLIに無い（T5で修正予定）ことを手順書に明記、(4) 旧 `610789c0` は削除済み（ループ記録3を追記済み） |
| 9 | T5 add_text を実CLIに合わせる | 作業役（PR #14 `4831a12`） | PASS（1周目） | 独立実測：ネット遮断・同名ブランチで158件OK。コマンドは `source add - --type text --title … --json --notebook …`（本文は標準入力・シェルを通さない引数列）、IDは `source.id`→`id` の順、失敗・タイムアウトは結果不明として再送せず一覧で確認。add 待ち時間は既定600秒。実際の `--live` 書き込みは未実行（UNVERIFIED） |
| 10 | T4 修正（2周目） | 作業役（PR #14 `4d6950b`） | PASS | 指摘4点すべて反映を差分で確認（実機dry-run済み・`--live`/health未実行、実CLI確認3コマンド、旧版の add-text 不具合とT5修正、旧 `610789c0` 置き換え済み）。差分はドキュメント3ファイルのみ、158件OK |
| 11 | T6 ユーザー確定仕様（時刻リンク・投稿日時・URL単体登録廃止） | 作業役（PR #14 `bd515ca`） | NEEDS_FIX（1周目） | コードは良好：独立実測169件OK、cue行は `[HH:MM:SS](…&t=秒s)` で秒は切り捨て・発話は前後空白除去のみ、`published_at` を荷札に記録、時刻なしは登録せず停止、`--include-youtube-url` は拒否。不足：(1) 正とするドキュメント `claude/requirements-alignment-20261020` が未マージ（ロードマップに取り下げ済みの旧v1.2節が残る）、(2) 実機で取得実績のある youtube-transcript-api の取得元が未実装（既存timedtext経路は実機未確認）、(3) Drive経路の字幕OKFに `published_at` が渡らない |
| 12 | T6 修正（2周目） | 作業役（PR #14 `4419d40`） | PASS | 独立実測171件OK。ロードマップの最上位節は requirements 側の「ユーザー確定要件R1〜R5」1つだけ（重複解消）。字幕取得は youtube-transcript-api → timedtext の順で、取得元を `acquisition_method` に記録。Drive経路の字幕OKFにも `published_at`。youtube-transcript-api 1.2.2 の実データとの属性照合は実機未確認 |
| 13 | T7 研究ノート時刻リンク化／Drive YouTube参照ファイル廃止 | 作業役（PR #14 `8a90508`） | PASS（1周目） | 独立実測177件OK、テスト後の作業ツリー差分なし。荷札・既存リンク・URL・インラインコードは不変、二重適用で不変を確認。pRfC1DILDEM研究ノートに適用すると47か所が時刻リンク化（GitHubファイルは不変）。Python/GASの出力一致テストPASS |
| 14 | T8 URL貼り付け経路へ notebooklm-py 接続＋研究ノート荷札に `published_at` | 作業役（PR #14 `f83dec0`） | PASS（1周目・条件付き） | 独立実測186件OK。手順8はGitHub保存後に `run_notebooklm_py_step` を呼び、字幕OKFのcueと `published_at` を渡す。成功判定は SUCCESS_2_SOURCE_OKF / NO_OP のみ、URL単体ソースの読み返しは常にFalse（登録しない）。既定はdry-run、書き込みは `--live` と notebook_id 必須。UNKNOWN：手順3〜8を通しで通すテストなし、dry-run時は手順8前に戻るため計画が出ない、実機 `--live` 未実行 |

## 次のタスク（作業役向け）

**T8: 「URLを貼るだけ」の通し運転にNotebook登録（notebooklm-py）をつなぐ（R5）**
- 対象: `auto_research_pipeline.py`（`run_pipeline` と CLI）、`receipt_to_research.py`、テスト
- やること:
  1. `--notebook-backend {cdp,notebooklm-py}` を追加（既定は現状どおり cdp）。`notebooklm-py` のときは、研究ノート生成・GitHub保存のあとに `notebooklm_py_ingest.run_ingest` を呼び、字幕取得（youtube-transcript-api→timedtext）・2ソース不足分の登録・読み戻しまで1回の実行で行う。既定は計画のみ。書き込みは `--live` と `--notebook-id` の両方が必要（既存の安全条件をそのまま引き継ぐ）。
  2. `receipt_to_research.py` が書く研究ノートの荷札に `published_at`（取得できなければ `"UNKNOWN"`）と `transcript_logical_id` が必ず入るようにする（R4・R1）。
  3. 実行結果（status・plan・writes・新ソースID）をパイプラインの戻り値に含める。ログイン切れ・字幕取得不可・曖昧は書き込み0で止まり、理由を返す。
  4. テスト（偽クライアント・偽取得関数・ネット不要）：新規URL→計画（字幕・研究ノートの2件）、既に揃った動画→NO_OP、ログイン切れ→停止、字幕不可→停止、`--live` に `--notebook-id` 無し→停止、研究ノート荷札に `published_at` と `transcript_logical_id`。既存テスト非破壊。
- 禁止: 実Notebook接続・書き込み、Gemini呼び出し、GitHubへの実push。

## ユーザー判断の記録

- 2026-10-20 18:04（JST）相棒が待ちリスト1〜4をすべて明示許可。
  - 2（権利判断）: 字幕原文をNotebookへ複製してよい。GitHubへの字幕全文保存は引き続き禁止。
  - 1・3・4: ユーザーのPC上の作業役（Remote Control）がNotebook操作を担当し、検品指示役が読み戻し値で判定する。
- 2026-10-20 22:42（JST）相棒の判断：
  - URL単体ソース15件は削除してよい。ただし先に各動画の字幕全文OKF（時刻なし・`published_at`入り）を登録し、読み戻しで確認してから削除する。
  - 字幕全文は**時刻なしを正**とする（R3の方針転換。発話ごとの時刻リンクは入れない）。場面の時刻リンクは研究ノート側（T7）で示す。
  - `published_at` は必ず入れる（R4は維持）。

## ユーザー待ちリスト

（2026-10-20 20:08 JST：1〜4は完了。結果はループ記録2・3と `registry.json` の `notebook_sources`）

| # | 何を | なぜ止めたか | 承認されたら進むこと |
|---|---|---|---|
| 5 | u3ka_AAb8qE の字幕全文OKF（時刻なし・`published_at` 2026-07-25）を実Notebookへ追加 | 22:42 の方針転換で時刻なしが正に。実行は再ログイン後 | OKF動画も2資料方式になる |
| 6 | URL単体ソース15件：先に字幕全文OKFを登録→読み戻し確認→URLソース削除（**22:42 相棒許可済み**） | 再ログイン待ち | Notebookが仕様どおり2資料方式に揃う |
| 7 | pRfC1DILDEM の字幕OKF `a32a70ec` は時刻なしのままで正。ただし `published_at` が無いため、入り版を追加→読み戻し→`a32a70ec` 削除してよいか | 削除は承認制（相棒に確認中） | RAG動画の字幕にも投稿日時が入る |
| 8 | Notebookへの書き込み全般 | ログイン切れ（22:20確認）。再ログインは自動でやらない | 5〜7を実行 |

（以下は完了済みの旧リスト）



| # | 何を | なぜ止めたか | 承認されたら進むこと |
|---|---|---|---|
| 1 | Phase 7 実機：`pRfC1DILDEM` か `u3ka_AAb8qE` の「字幕原文OKF」をNotebookへ新規登録し読み戻す | Notebook LIVE書き込み（守りルール5） | 1動画2ソースの正式完成判定（`SUCCESS_2_SOURCE_OKF`）に進める |
| 2 | 字幕原文をNotebookへ複製してよいかの権利・規約判断 | ロードマップが `BLOCKED_RIGHTS_OR_TERMS` 判定を要求 | 上記1の前提 |
| 3 | Notebookの旧RAGノートを最新版で置き換えるか（現在は追記で補っただけ） | 置き換えはソース削除を伴いIDが変わる（守りルール5） | Notebook側の相互リンクが正式版になる |
| 4 | 台帳 `registry.json` の「NOTEBOOK_READBACK_UNKNOWN」を、手元検品で読み戻せた29動画ぶん更新するか | 手元検品の生データ（ソースID対応表）がGitHubに無く、検品役が独立確認できない | 対応表を共有してもらえれば、作業役が台帳更新→検品役が照合 |
