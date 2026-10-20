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

## 次のタスク（作業役向け）

（T1〜T5完了。次は相棒の承認待ち5（u3ka_AAb8qE の字幕原文を `--live` で追加）。承認が出たら、相棒PCで health → dry-run → `--live` → 事後読み戻し → health を手順書どおりに実行し、検品役が読み戻し値で判定する）

## ユーザー判断の記録

- 2026-10-20 18:04（JST）相棒が待ちリスト1〜4をすべて明示許可。
  - 2（権利判断）: 字幕原文をNotebookへ複製してよい。GitHubへの字幕全文保存は引き続き禁止。
  - 1・3・4: ユーザーのPC上の作業役（Remote Control）がNotebook操作を担当し、検品指示役が読み戻し値で判定する。

## ユーザー待ちリスト

（2026-10-20 20:08 JST：1〜4は完了。結果はループ記録2・3と `registry.json` の `notebook_sources`）

| # | 何を | なぜ止めたか | 承認されたら進むこと |
|---|---|---|---|
| 5 | u3ka_AAb8qE の字幕原文OKFを、新しい自動登録道具で実Notebookへ追加する（T5修正後に `--live`） | 新しいNotebook書き込み（守りルール5）。前回の許可はpRfC1DILDEM分のみ | OKF動画も字幕原文＋研究ノートの2ソースになる |

（以下は完了済みの旧リスト）



| # | 何を | なぜ止めたか | 承認されたら進むこと |
|---|---|---|---|
| 1 | Phase 7 実機：`pRfC1DILDEM` か `u3ka_AAb8qE` の「字幕原文OKF」をNotebookへ新規登録し読み戻す | Notebook LIVE書き込み（守りルール5） | 1動画2ソースの正式完成判定（`SUCCESS_2_SOURCE_OKF`）に進める |
| 2 | 字幕原文をNotebookへ複製してよいかの権利・規約判断 | ロードマップが `BLOCKED_RIGHTS_OR_TERMS` 判定を要求 | 上記1の前提 |
| 3 | Notebookの旧RAGノートを最新版で置き換えるか（現在は追記で補っただけ） | 置き換えはソース削除を伴いIDが変わる（守りルール5） | Notebook側の相互リンクが正式版になる |
| 4 | 台帳 `registry.json` の「NOTEBOOK_READBACK_UNKNOWN」を、手元検品で読み戻せた29動画ぶん更新するか | 手元検品の生データ（ソースID対応表）がGitHubに無く、検品役が独立確認できない | 対応表を共有してもらえれば、作業役が台帳更新→検品役が照合 |
