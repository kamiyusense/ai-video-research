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
| 3 | RAG研究ノートを最新版へ置き換え（許可3） | 作業役（ユーザーPC） | 追加PASS・旧版削除を承認 | 新ソース `af697c8c`（GitHub `169dda0` 版 SHA-256 一致を確認後、`transcript_notebook_source_id` を1行追加して投入）。正規化比較で一致。件数53→55（増加は2件のみ）。旧 `610789c0` の削除を検品役が承認（バックアップ全文あり） |
| 4 | T2 notebooklm-py 2ソース自動登録モジュール | 作業役（PR #14 `2aaf20d`） | NEEDS_FIX（1周目） | テストは独立実測で136件OK（ネット遮断・同名ブランチ）。安全面はOK。ただし実Notebookのタイトル（`tests/fixtures/notebook_sources_20261020.json`）で重複判定を試すと、`【研究ノート】…[id]`・`動画研究_…id…` を研究ノートと認識せず、IDを含むmarkdownをYouTube扱いする → LIVEで研究ノートを二重登録する。修正指示済み |

## 次のタスク（作業役向け）

**T2: notebooklm-py 経由の「2ソース自動登録」モジュール（オフライン実装＋テスト）**

背景: 2026-10-20 の実機作業（ループ記録2・3）はユーザーPCの notebooklm-py 0.8.5 で手作業的に行った。これを再実行可能なコードにする。既存の `notebook_auto_ingest.py`（CDP方式）は壊さず、別モジュールとして追加する。

- 対象: 新規 `automation/gemini-notebook/notebooklm_py_ingest.py`、新規 `tests/test_notebooklm_py_ingest.py`
- 作るもの:
  1. **クライアント差し替え口**：`list_sources()` / `get_fulltext(id)` / `add_text(title, text)` / `auth_check_passive()` だけを持つ小さなインターフェース。実装は (a) テスト用の偽クライアント、(b) `notebooklm` CLI をsubprocessで呼ぶ実機用アダプタ（コマンドの正確さは実機未確認＝`UNVERIFIED` とコメントで明記）。削除メソッドは持たせない。
  2. **ログイン点検**：最初に `auth_check_passive()`。失敗なら書き込み0件で `AUTH_EXPIRED_HALT` を返して止まる。login/refresh は呼ばない。
  3. **事前読み戻し・重複チェック**：既存の `evaluate_2_source_okf_independence` を再利用して、字幕原文OKF・研究ノートOKFの有無を判定。揃っていれば `NO_OP`、足りない方だけ追加する。
  4. **字幕原文OKFの組み立て**：既存の `build_transcript_okf_content` を再利用。字幕cueが無い場合は、NotebookのYouTubeソース本文を使ったことを `acquisition_method` に記録し、`UNVERIFIED`・cue数0とする。
  5. **事後読み戻し**：追加後に一覧と本文を読み戻す。完全一致に加えて「Markdown記号・空白を除いた正規化一致」を判定関数として実装する（NotebookLMの表示用整形への対応。今回の実機で合格基準にしたもの）。両ソースが別IDであることも確認する。
  6. **安全**：既定は dry-run（計画だけ出す）。実書き込みには `--live` と `--notebook-id` の明示が必須。結果が不明な書き込みは再送せず、一覧の読み戻しで確認する。
- 受入条件（検品役が確認する点）: 次の各ケースを偽クライアントでテストし、全部オフラインでPASS。
  - 両方そろっている → 書き込み0の `NO_OP`
  - 字幕原文だけ無い → 字幕原文だけ追加
  - ログイン切れ → 書き込み0で停止
  - 正規化一致：記号が消えた本文は合格、1文字欠けた本文は不合格
  - 書き込み結果が不明 → 再送せず読み戻し
  - 削除の呼び出しが存在しない
  - 既存テスト（同名ブランチで122件）を壊さない
- 禁止: 実Notebookへの接続・書き込み、Gemini呼び出し、テストの削除・スキップ。

## ユーザー判断の記録

- 2026-10-20 18:04（JST）相棒が待ちリスト1〜4をすべて明示許可。
  - 2（権利判断）: 字幕原文をNotebookへ複製してよい。GitHubへの字幕全文保存は引き続き禁止。
  - 1・3・4: ユーザーのPC上の作業役（Remote Control）がNotebook操作を担当し、検品指示役が読み戻し値で判定する。

## ユーザー待ちリスト

（2026-10-20 20:08 JST：1〜4は完了。結果はループ記録2・3と `registry.json` の `notebook_sources`。現在の待ちは無し）


| # | 何を | なぜ止めたか | 承認されたら進むこと |
|---|---|---|---|
| 1 | Phase 7 実機：`pRfC1DILDEM` か `u3ka_AAb8qE` の「字幕原文OKF」をNotebookへ新規登録し読み戻す | Notebook LIVE書き込み（守りルール5） | 1動画2ソースの正式完成判定（`SUCCESS_2_SOURCE_OKF`）に進める |
| 2 | 字幕原文をNotebookへ複製してよいかの権利・規約判断 | ロードマップが `BLOCKED_RIGHTS_OR_TERMS` 判定を要求 | 上記1の前提 |
| 3 | Notebookの旧RAGノートを最新版で置き換えるか（現在は追記で補っただけ） | 置き換えはソース削除を伴いIDが変わる（守りルール5） | Notebook側の相互リンクが正式版になる |
| 4 | 台帳 `registry.json` の「NOTEBOOK_READBACK_UNKNOWN」を、手元検品で読み戻せた29動画ぶん更新するか | 手元検品の生データ（ソースID対応表）がGitHubに無く、検品役が独立確認できない | 対応表を共有してもらえれば、作業役が台帳更新→検品役が照合 |
