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
| 15 | T9 通し試験（手順3〜8モック）＋dry-runで手順8の計画表示 | 作業役（PR #14 `0082e2d`） | PASS（1周目） | 独立実測195件OK、作業ツリー差分なし。dry-run時は `live=False` を強制して手順8の計画（種類・タイトル・logical_id）だけ返し、IDが無ければ一覧も読まない。通し試験で追加は字幕・研究ノートの2件のみ・URL単体0件、既登録はNO_OP。注意：(c)時刻リンク形式と(e)時刻なし停止の試験は22:42の方針転換によりT10で書き換え予定。UNKNOWN：dry-runの予定タイトルは仮名、GitHub保存は偽物、実機 `--live` 未実行 |
| 16 | T10 字幕時刻なし化・published_at点検・URLソース15件の移行計画・ロードマップv1.3 | 作業役（PR #14 `e4b42e7`） | NEEDS_FIX（1周目） | コードは良好：独立実測209件OK・差分なし。時刻なし本文が既定、取得元は cue→Notebook内YouTube本文→字幕API、何も無い時だけ TRANSCRIPT_UNAVAILABLE で停止、health が published_at 欠落を ATTENTION、migrate-plan は読み取りのみで削除コードなし（15件解決・UNKNOWN 0）。不足：(1) ロードマップに旧記述が残る（表題v1.2、v1.2改訂行の「時刻リンク」、完成判定(4)の「Cue全量…引用時刻と整合」、Phase5表と受入条件の「30組完全双方向整合性」、G3の取り消し線）＝相棒22:49「新旧を併存させない」に反する、(2) 段落区切りが3秒/300字で、AGENTS.md と相棒PCで作成済み15本の「約1分ごと」と不一致 |
| 17 | T10 修正（2周目） | 作業役（PR #14 `efe019d`） | PASS | 独立実測212件OK・差分なし。ロードマップv1.3で旧記述（v1.2改訂行・Cue全量・取り消し線・「30組」の誤読）を解消、段落は約60秒ごと（保険1000字）、字幕取得順は cue→字幕API→timedtext→Notebook本文（最後の手段）、README と AGENTS.md の `--include-youtube-url` 記述なし。UNKNOWN：migrate-plan・health本文読み・タイトル取得は実機未実行、相棒PCで作成済み15本との段落形式の一致は未照合 |
| 18 | T11 関連動画リンク（R6）検証器・全件候補・関連索引（dry-run） | 作業役（PR #14 `5dcfd99`） | PASS（1周目・条件付き） | 独立実測231件OK・差分なし。related_links.py は読み取り専用（書き込み・削除コードなし、`files_modified: false`）。現registryで validate：related_records 65件中33件が不合格（根拠なし33、自己リンク2）、合格の確定ペアは pRfC↔u3ka の1組のみ。candidates 147件（未登録118）、すべてCANDIDATEで根拠に共通語と両ノートの該当箇所。UNKNOWN：候補の並びの品質は人の目で未確認（確定済みペアが6位）、実Notebookでの既存index検索は未検証。要判断：既存ノート33件の不合格 related_records の扱い |
| 19 | T12 ロードマップv2.0統合・repair-plan・段落の時刻目印（任意） | 作業役（PR #14 `c36978e`） | PASS（1周目・条件付き） | 独立実測243件OK・差分なし。ロードマップは相棒PC側 v2.0（e50590c）を採用、見出し1つ・旧版併存なし、AGENTS.md・HANDOVER の旧記述も解消。repair-plan は読み取りのみ（`files_modified:false`、削除予定33件は validate の不合格と一致、確定ペア温存）。時刻目印は既定OFFで従来出力を固定。UNKNOWN：repo の字幕ビルダーは v2.0 §3.1 が求める本文先頭2行（ID・動画URL）をまだ出さない（相棒PCの15本は対応済み）＝T13、目印ONのNotebook読み戻しは実機未確認 |
| 20 | T13 字幕先頭2行（ID・動画URL）・時刻目印の切替配線・repair-plan --summary | 作業役（PR #14 `e074821`） | PASS（1周目・条件付き） | 独立実測252件OK・差分なし、registry.json／research 無変更。repair-plan --summary は読み取りのみで人が読める一覧が出る。時刻目印は既定OFF、`DEFAULT_PARAGRAPH_ANCHORS` 1か所で切替。要改善：置換候補の質がまちまち（共通語が「mac・mini・computer・use」など汎用語だけの候補あり）→T14。UNKNOWN：先頭2行の実機読み戻し・相棒PCの15本との行並び一致は未照合 |
| 21 | T14 関連候補の精度向上 | 作業役（PR #14 `eade1e0`） | PASS（1周目・条件付き） | 独立実測260件OK・差分なし。候補147→49件（未登録118→35）、汎用語・大手名だけの候補は出さない。上位8組を目で確認：主題は合っている（例：dots、GPT-6.1 Sol、vault/CLAUDE.md）。pRfC↔u3ka は1位。UNKNOWN：落ちた組に本当は関連のものがある可能性、汎用語リストは31本向けの手作業、人の確認は未実施 |
| 22 | T15 段落先頭の時刻目印を既定ON | 作業役（PR #14 `8a85bde`） | PASS（1周目・条件付き） | 独立実測267件OK・差分なし。`DEFAULT_PARAGRAPH_ANCHORS=True`、実出力で見出し直後に `ID:`／`動画:` 2行・荷札 `transcript_format: PARAGRAPHS_WITH_ANCHORS`。health は目印なし字幕を ATTENTION、migrate-plan は目印なし既存字幕を置き換え対象に、読み戻し正規化は ▶ 消失を吸収。文書は新旧併存なし。UNKNOWN：実機NotebookLMでの▶・URL表示、相棒PC再作成物との見出し文言の一致は未照合 |
| 23 | T16 目印の書式を実機形式 `[HH:MM:SS] <URL>&t=秒s` に統一・相棒PC側ロードマップ取り込み | 作業役（PR #14 `20b1e32`） | PASS（1周目・条件付き） | 独立実測273件OK・差分なし。衝突マーカー0、ロードマップは v2.0 見出し1つ、ビルダーは新形式のみ出力（▶は読み取り側の許容だけ残す）。UNKNOWN：実Notebookの15本が実際にこの形式かは相棒PC報告のみ、見出し文言・荷札値の突き合わせ未実施→相棒PCで点検ツール（health／migrate-plan・読み取りのみ）を実行して独立確認する |
| 24 | T17 関連リンクの自動修復（人の確認なし・候補止まり） | 作業役（PR #14 `664e224`） | PASS（1周目・条件付き） | 独立実測294件OK・差分なし。validate は 108件・不合格0、再実行は変更0件（冪等）、研究ノート25本の差分は関連レコード行・節見出し・空行のみ、確定済みペアは無変更、相棒PCが付けた8組は温存。相棒の保存許可（18:37Z）後にcommit/push。UNKNOWN：追加CANDIDATE60件の品質は人の目で未確認（機械選び）、Notebook側の研究ノート差し替えは未着手 |
| 25 | T18 テストを枝名に依存しない形に | 作業役（PR #14 `e129a05`） | PASS（1周目） | 独立実測：別名の枝・detached HEAD で全件OK、差分なし、パイプライン本体（automation）は T17 から変更0（安全チェックは弱めていない）。許可枝以外（main等）で書き込みが拒否されるテストが追加。作業役がローカルの `main` を誤削除して復元（リモート無事、報告済み） |

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
- 2026-10-21 03:09（JST）相棒の判断：関連リンクの仕分けは相棒の目視確認なしで自動適用（候補止まり）。続けて「今確認待ちの分はあとはやっていい」と許可＝関連リンクの置き換え（GitHub別ブランチ）と、その反映に伴うNotebook側の研究ノート差し替え（追加→読み戻し→旧版削除）。Merge・課金・権限変更は含まない。
- 2026-10-21 02:37（JST）相棒の判断：字幕に約1分ごとの段落先頭の時刻目印（`▶HH:MM:SS` ＋ `&t=秒s` リンク1つ）を付ける。現在Notebookにある時刻なし字幕15本は作り直して差し替える（追加→読み戻し→旧を削除）。ログイン画面の表示も許可。
- 2026-10-20 22:49（JST）相棒が「そんな感じでお願い」で待ちリスト7（RAG旧2件の入れ替え）と15件移行の進め方を了承。ロードマップ等は新旧の記述を併存させず、混ざる旧記述は削除してよい。
- 2026-10-20 22:42（JST）相棒の判断：
  - URL単体ソース15件は削除してよい。ただし先に各動画の字幕全文OKF（時刻なし・`published_at`入り）を登録し、読み戻しで確認してから削除する。
  - 字幕全文は発話ごとの時刻リンクを入れない（R3の方針転換。※02:37に「段落先頭の時刻目印あり」へ更新済み・上の記録が最新）。場面の時刻リンクは研究ノート側（T7）で示す。
  - `published_at` は必ず入れる（R4は維持）。

## ユーザー待ちリスト

（2026-10-20 20:08 JST：1〜4は完了。結果はループ記録2・3と `registry.json` の `notebook_sources`）

| # | 何を | なぜ止めたか | 承認されたら進むこと |
|---|---|---|---|
| 5 | u3ka_AAb8qE の字幕全文OKF（段落先頭の時刻目印つき・`published_at` 2026-07-25）を実Notebookへ追加 | 22:42 の方針転換で時刻なしが正に。実行は再ログイン後 | OKF動画も2資料方式になる |
| 6 | URL単体ソース15件：先に字幕全文OKFを登録→読み戻し確認→URLソース削除（**22:42 相棒許可済み**） | 再ログイン待ち | Notebookが仕様どおり2資料方式に揃う |
| 7 | pRfC1DILDEM の旧2件（字幕 `a32a70ec`・研究ノート `af697c8c`）を、投稿日時入り・時刻なしの新版に入れ替え（追加→読み戻し→旧2件削除）（**22:49 相棒了承**） | 再ログイン待ち | RAG動画の字幕にも投稿日時が入る |
| 8 | Notebookへの書き込み全般 | ログイン切れ（22:20確認）。再ログインは自動でやらない | 5〜7を実行 |

（以下は完了済みの旧リスト）



| # | 何を | なぜ止めたか | 承認されたら進むこと |
|---|---|---|---|
| 1 | Phase 7 実機：`pRfC1DILDEM` か `u3ka_AAb8qE` の「字幕原文OKF」をNotebookへ新規登録し読み戻す | Notebook LIVE書き込み（守りルール5） | 1動画2ソースの正式完成判定（`SUCCESS_2_SOURCE_OKF`）に進める |
| 2 | 字幕原文をNotebookへ複製してよいかの権利・規約判断 | ロードマップが `BLOCKED_RIGHTS_OR_TERMS` 判定を要求 | 上記1の前提 |
| 3 | Notebookの旧RAGノートを最新版で置き換えるか（現在は追記で補っただけ） | 置き換えはソース削除を伴いIDが変わる（守りルール5） | Notebook側の相互リンクが正式版になる |
| 4 | 台帳 `registry.json` の「NOTEBOOK_READBACK_UNKNOWN」を、手元検品で読み戻せた29動画ぶん更新するか | 手元検品の生データ（ソースID対応表）がGitHubに無く、検品役が独立確認できない | 対応表を共有してもらえれば、作業役が台帳更新→検品役が照合 |

## GH-22 字幕保存スイッチ（2026-10-27・作業継続）

- 開始HEAD実測: `38c2beb19496a2a1c07efc8c7069aecfa6d3d89f`、ブランチ `symphony/gh-22-design`、開始時作業ツリー差分なし。
- 受け箱・永続選別・状態・好みメモ部品追加。試作の画面はまだ新部品に未接続。
- `python -m unittest discover -s tests -p 'test_subtitle_switch*.py'`: 17件、OK（0.007秒）。ローカル部品の試験のみ。独立GitHub検品・実機PASSではない。
- GitHub current stateは許可されたDraft PR検索のみ実施し0件。visibility/default branchのremote照合は許可されたAPI範囲外のためUNKNOWN。
- 次: 全工程のアダプター接続、1ボタン画面、lab_folder照合、既知3点修正、全体Mock試験、オーナー向け手順。
- ユーザー待ち: Notebook/Drive/YouTubeの実機検証は本Issueで禁止。別途対象と範囲の許可後に実機確認可能。本作業はオフライン実装を続ける。

## GH-22 継続ターン2（2026-10-27・環境阻害あり）

- 判定：STATIC実装／MOCK試験は下記範囲で合格。独立GitHub検品・実機はUNKNOWN。Issueの完了条件は未達。
- 追加：`pipeline.py`（工程保存・OSロック・再開・結果不明読戻し・原因変更後2回まで）、`captions.py`（json3・開始秒・重なった自動字幕だけ重複除去）、`services.py`（既存重複検査・OKF検品・索引・GitHubの対象限定保存とHEAD/本文読戻し・Notebook不足分登録と本文/DOM読戻し）、`switch_app.py`（1ボタン画面）、設定見本、研究用指示文。
- `subtitle_switch.pyw` の直接起動を新画面へ接続。旧試作の関数／PowerShellは参照と既存テスト用に温存。READMEをオーナー向け起動・待ち理由・復旧手順に更新。
- 既知修正：legacy pipelineに `--target-branch`（main/masterは明示しても拒否）、QA_WORKFLOWのURL単体登録方針を純粋2ソースへ訂正、RAG動画の既知の失効ソースIDをUNKNOWNへ。新しい完全IDの推測は禁止のため実機readback待ち。
- このローカル版に `lab_folder()` は存在しなかったため既存notebook_auto_ingestに共通関数を追加し新アプリが再利用。新しい親フォルダ優先・旧直下・設定上書きを試験。
- 実測：`python -m unittest discover -s tests -p 'test_subtitle_switch*.py'` 43件、0.041秒、OK。外部境界は偽物。実アダプターを通す2本のMock完走、字幕のGitHub排除、同一DOM不合格、本文不一致、上限前停止、既存2ソースNo-Op、応答不明時読戻しを含む。
- 全体実測：389件、assertion failure 0、error 20。20件とも `PermissionError: [Errno 13] Permission denied: 'node'`。Nodeを導入・ダウンロードしていない。最終の状態更新後は関連43件とcompileを再実行して合格。全件合格とは認定しない。
- 台帳変更で過去の画面fixtureとの比較が不整合になった健康診断テストは、2026-10-20の画面fixtureと対になる歴史台帳fixtureへ分離。現在台帳の失効IDがUNKNOWNかつ健康診断ATTENTIONになる試験も追加。偽の現行IDで合格させていない。
- `git diff --check` とPython compile合格。WindowsのTk表示、外部CLIの実仕様適合、Notebook/Drive/YouTube/GitHub保存の実機動作はUNKNOWN。実サービス起動・モデル呼出しは0。
- **環境阻害**：前ターンのgit add/commitは `.git/index.lock: Read-only file system`。今ターン `os.statvfs('.git').f_flag & os.ST_RDONLY` を実測しTrue。原因未変更のため同じ失敗操作を繰り返さず、コミット未作成。開始HEAD `38c2beb19496a2a1c07efc8c7069aecfa6d3d89f` のまま、全変更は作業ツリーに保持。
- 次の作業：環境側で.git書込みとNode実行が可能になった後、全試験と差分を確認して署名付きローカルコミット。Symphonyの公開後にDraft PRを読み戻して独立検品し、合格した場合だけIssueコメント1件→対象ラベル削除。現時点ではコメント・ラベル削除をしていない。

### GH-22 ユーザー／環境待ちリスト

| 何を | なぜ | 解消後に進むこと |
|---|---|---|
| Symphony作業領域の.git書込み | ファイルシステムがread-onlyで必須commitを作れない | ローカルcommitとSymphonyによるDraft PR公開 |
| Node実行可能な検証環境 | 既存20件がPermissionErrorで未検証 | 全体試験の全件合格確認 |
| Notebook/Drive等の実機検証 | 本Issue内では実行禁止 | 別途対象・範囲の許可後にのみ実機確認（本Issueのオフライン完成判定とは分離） |

## GH-22 継続ターン3（2026-10-27・安全境界再点検）

- 開始時再実測：`.git`のST_RDONLY=True、`shutil.which('node')`=None。開始HEADは前ターンと同じ。コミット阻害の原因は未変更なので失敗コマンドを再送しない。環境迂回・別index等による制約回避もしていない。
- 修正：結果不明writeの読戻しがno_writeの通信／認証エラーになっても元のinflightを消さない。Notebookの資料別送信印を照合し、不明な既送信があれば再送も未送信追加もしない。1資料目だけ確認でき、2資料目が未送信ならその不足分だけ継続。
- 修正：後続動画でremote HEADが進んだ場合のGitHub読戻しは、元コミットがremoteの祖先であることと、その版の3ファイル・現行ノート本文一致で立証。再Pushしない。
- 修正：字幕指紋／生成本文を研究前・検品前に再確認。根拠リンクの秒数を字幕開始秒と照合。Claudeの終了コード0のJSONエラーも枠切れ待ちとして扱う。API/provider環境変数は存在だけでモデル起動を拒否し、値を読まない。
- 修正：検品した保管庫ノートだけでなく、実際にstageするrepositoryノートとの一致を必須化。既存receipt_to_research.scan_forbidden_keysをノート・registry・catalogに適用。台帳工程の日付またぎでも保存予定パスを固定。
- 画面：工程・主な待ち理由を日本語化。完了・登録済みの再表示切替。偽境界のreceiptはis_mock=true。
- 実測：`python -m unittest discover -s tests -p 'test_subtitle_switch*.py'` 55件、0.059秒、OK。前ターンより12件追加。検品対象との差し替え、台帳禁止キー、字幕改変、架空の秒数、0終了コード枠切れ、Notebook途中停止、読戻し失敗後の再送防止、祖先コミット読戻し、日付またぎ、API起動拒否、一覧表示を検証。
- Python compile／`git diff --check` 合格。既存全体389件中Node起因20errorの記録は前ターン実測で、今回の55件を全体試験の全件合格へ読み替えない。
- 判定：MOCK／STATIC合格範囲は上記。remote差分の独立検品・Windows画面・実サービスはUNKNOWN。署名付きcommit、Symphony公開、Draft PR確認、全試験合格が未達のためIssueコメント・ラベル削除は未実施。
- ユーザー／環境待ち：前ターンの「.git書込み」「Node実行可能な環境」は継続。新しい実機承認は要求しない（本Issue内の実機禁止を維持）。

## GH-22 継続ターン4（2026-10-27・再起動後の工程停止）

- 開始HEAD実測 `6feddafa3558f595349b0bd81872eef6b691f2c6`、`symphony/gh-22-design`、作業ツリー差分なし。前ターンまでの変更はSymphonyチェックポイントに含まれる。
- 許可されたDraft PR検索APIでmain宛てDraft PR #24を確認。検索レスポンスのrepo属性でvisibility=public、default_branch=mainを確認（古い資料の非公開表記は現状と異なる）。
- 目的・受入条件：Notebook認証切れ／YouTubeロボット確認は再起動後の新着動画にも該当工程の待ちを適用し、明示的な原因変更後のみ再開。Notebook停止中の新着動画のGitHub工程は継続。実サービス禁止を維持。
- 変更：`pipeline.py` に工程停止の永続化、`test_subtitle_switch_pipeline.py` に再起動・新着・同一原因選択の3試験。READMEと設計書へ復旧方法を追記。
- 実測：関連58件、0.074秒、OK。全体404件、failure 0、error 20、skip 0。20件はすべて `PermissionError: [Errno 13] Permission denied: 'node'`。Node試験をskip／偽PASSに変更していない。全件合格は未達。
- 環境再測定：`.git` のST_RDONLY=True、Node実行ファイル検出なし。commit不能の原因が変わっていないため既知の失敗コマンドを再送せず、署名付きcommitは未作成。変更は作業ツリーへ保持し、Symphonyのチェックポイント対象とする。
- 判定：関連MOCK試験は合格、全体試験は環境阻害。Windows画面・モデル／外部CLI実行・実保存はUNKNOWN。Issueコメント・ラベル削除は未実施。
- 次：.git書込みとNode実行が可能な作業環境で、全体試験と署名付きcommitを完了。Symphony公開後のDraft PRを照合して全条件を満たした場合だけ、Issueコメント1件→対象ラベル削除。

### 同一runの継続2〜4：環境阻害の再確認

- 3回の継続で `.git` のST_RDONLY=True、Node検出なしを再確認。HEADと未コミット5ファイルは変わっていない。nodejs／bun／denoも検出されない。
- 状態：BLOCKED（環境）。新しいコード変更を理由なく増やさず、既知の失敗commit／Node試験の再実行や制約回避は行わない。試験結果は直近実測の関連58件OK／全体404件中20errorのままで、新しいPASSとして扱わない。
- 再開条件：Official Symphony側で.git書込みとNode実行可能な環境を用意すること。復旧後、保持された差分を確認し、全体試験・署名付きcommit・公開後のPR照合を実施する。現環境からインストール・push・ライフサイクル変更はしない。Issueコメント／ラベル削除は引き続き未実施。

### 同一runの継続20：最終引継ぎ

- 継続20でも `.git` のST_RDONLY=True、Node検出なし。HEADは `6feddafa3558f595349b0bd81872eef6b691f2c6`、変更5ファイルを保持。環境条件は変わらずBLOCKED。
- 最新の試験実測は関連58件OK／全体404件中Node起因20error。再実行なし。署名付きローカルcommitは未作成。変更の公開・チェックポイントはOfficial Symphonyに委ねる。
- Draft PR #24の説明は更新済み。完了用Issueコメントと対象ラベル削除は未実施、Merge／main push／実サービス実行なし。環境復旧後は上記の再開条件から続ける。

## GH-22 継続ターン5（2026-10-27・好みメモ配送失敗の隔離）

- 開始HEAD実測 `035a2a649e63822ef746fddf20d00f6d81ef9c9c`、ブランチ `symphony/gh-22-design`、開始差分なし。許可された検索で main 宛て Draft PR #24 を再確認。
- 修正：好みフォルダ内のJSONが配列・null・数値・文字列の場合は配送待ちへ戻す。送信済みPCファイルの削除失敗も配送待ちへ戻す。どちらも例外を動画保存へ伝播させない。次回はsession_idの読み戻しで配送済みを照合し、重複作成しない。既存ファイルは変更しない。
- 受入検証：不正な形のJSON4種類、削除権限エラー、復旧後の配送・重複防止を追加。`python -m unittest discover -s tests -p 'test_subtitle_switch*.py'` は60件、0.078秒、OK。`git diff --check` 合格。すべてオフライン、モデル・外部通信なし。
- 環境実測：`.git` のST_RDONLY=True、Node検出なし。前回と原因が同じため失敗commitと全体Node試験の再実行はしない。必須の署名付きローカルcommitは環境阻害で未作成。変更はSymphonyチェックポイント対象。
- 判定：今回のMOCK回帰試験は合格。全体試験は前回実測404件中20errorから未解決で、全件合格としない。Windows実画面・実サービスはUNKNOWN。Issue完了コメント・ラベル削除は条件未達につき未実施。
- 環境待ち：既存リストの.git書込み／Node実行環境の復旧後、全体試験・署名付きcommit・公開PR照合へ進む。実サービスの禁止は維持。

## GH-22 継続ターン6（2026-10-27・環境復旧確認）

- 開始HEAD `d710b8a7bcd631fc229dc2dbbe0da85d6d8e9895`、ブランチ `symphony/gh-22-design`、開始差分なし。許可されたDraft PR検索から #24、main宛て、remote HEAD一致、publicを再確認。
- 関連オフライン試験を実測：60件、0.078秒、OK。外部通信・モデル実行なし。`git diff --check` 合格。Windows実画面・実サービスはUNKNOWN。
- 環境実測：`.git` のST_RDONLY=True、node／nodejsとも検出なし。全体試験の既知20errorと署名付きcommitの阻害原因は解消していない。同じ失敗操作を再送せず、Node試験をskip扱いにも変更しない。
- ユーザー待ち／環境待ち：Official Symphony側の.git書込み・Node実行環境の復旧が必要。復旧後に全体試験、AI-Agent署名付きcommit、公開PR照合へ進む。インストール・push・ワークスペース制約回避は行わない。
- 完了条件未達のためIssueコメント・ラベル削除は未実施。この記録はSymphonyチェックポイントへ引き継ぐ。

AI-Agent: codex

### 同一run継続2：環境阻害継続

- `.git` のST_RDONLY=True、node／nodejs検出なしを再測定。前ターンの作業記録のみ未コミットで保持。環境は復旧していないため、既知の失敗commit・全体試験は再送しない。
- BLOCKED（環境）：Official Symphony側で.git書込みとNode実行環境が復旧したら、全体試験・署名付きcommit・PR照合を再開する。Issueコメント・ラベル削除は未実施。

### 同一run継続3〜7：環境復旧なし

- 各継続で.gitのST_RDONLY=TrueとNode不在を実測。継続7でも同じ。環境待ちのBLOCKEDを維持。既知の失敗操作の再送、試験のskip化、制約回避はしない。
- 未コミットの作業記録を保持。Official Symphony側の環境復旧後に、全体試験とAI-Agent署名付きcommitから再開する。完了用Issueコメント・ラベル削除は未実施。

### 同一run継続20：環境阻害の最終引継ぎ

- 継続20で再測定：.gitのST_RDONLY=True、node／nodejs不在。継続14でも同条件を実測し、環境復旧なし。BLOCKED（環境）。
- 最新の関連試験実測は60件OK。全体試験の既知Node起因20errorは未解消。署名付きローカルcommitは読取り専用マウントにより未作成。未コミットの作業記録を保持し、Official Symphonyのチェックポイントに委ねる。
- 復旧後：保持差分確認 → 全体試験 → AI-Agent署名付きcommit → 公開後Draft PR照合 → 全条件達成時のみIssueコメント1件と対象ラベル削除。実サービス実行・Merge・main pushは禁止を維持。

AI-Agent: codex

## GH-22 継続ターン7（2026-10-27・公開状態と環境の再確認）

- 開始HEAD実測 `527c4cb346e72eb87d40513226efd4d14854101c`、ブランチ `symphony/gh-22-design`、開始差分なし。許可されたPR検索でmain宛てDraft PR #24とremote HEAD一致を確認。repositoryはpublic。
- 関連オフライン試験を再実測：60件、0.089秒、OK。`git diff --check` 合格。モデル・外部サービス実行なし。
- `.git` のST_RDONLY=True、node／nodejs検出なし。既知のcommit失敗と全体試験20errorの原因は変わっていないため再送しない。署名付きローカルcommitは環境阻害で未作成。全体試験の最新実測は前回の404件中20errorであり、今回の60件合格とは区別する。
- BLOCKED（環境）。Official Symphony側の.git書込みとNode実行環境の復旧後に、全体試験・署名付きcommit・公開PR照合を再開する。実機はUNKNOWN。完了用Issueコメント・対象ラベル削除は未実施。今回の記録はSymphonyチェックポイントに引き継ぐ。

AI-Agent: codex

### 同一run継続20：環境阻害の引継ぎ

- 継続2・3・6・10・14・20で.gitのST_RDONLY=True、node／nodejs不在を再測定。環境は復旧していない。BLOCKED（環境）。
- 最新の関連試験実測は60件、0.089秒、OK。全体試験の既知20errorと署名付きcommitは未解決。既知の失敗操作を再送せず、検品ログの差分を保持。
- Official Symphony側で.git書込みとNode実行環境を復旧後、全体試験・AI-Agent署名付きcommit・公開Draft PR #24の照合から再開。Issue完了コメントと対象ラベル削除は未実施。実サービス実行なし、実機結果UNKNOWN。

AI-Agent: codex

## GH-22 継続ターン8（2026-10-27・環境阻害の再測定）

- 開始HEAD `da5278b242a5b8a90c1279c10f7133bafb6865c1`、`symphony/gh-22-design`、開始差分なし。許可されたPR検索でDraft PR #24、main宛て、remote HEAD一致、publicを確認。
- 関連オフライン試験は今回実測60件、0.081秒、OK。モデル・外部通信なし。差分空白検査合格。設計文書と日本語起動手順を再読。
- `.git` のST_RDONLY=True、node／nodejs検出なし。既知のcommit失敗と全体試験の環境阻害は未解消。同じ失敗操作は再送せず、署名付きcommitは未作成。全体試験の前回実測404件中20errorを今回の60件合格で置き換えない。
- BLOCKED（環境）。Official Symphony側の.git書込みとNode実行環境の復旧後、全体試験・署名付きcommit・公開PR照合から再開する。実機はUNKNOWN、本Issue内では実行禁止を維持。完了用Issueコメント・対象ラベル削除は未実施。今回の記録はSymphonyチェックポイントへ引き継ぐ。

AI-Agent: codex

### 同一run継続20：環境阻害の引継ぎ

- 継続2〜20で.gitのST_RDONLY=True、node／nodejs不在を再測定。環境復旧なし、BLOCKED（環境）。既知の失敗commitと全体試験を再送せず、制約回避や試験のskip化は行っていない。
- 今runの関連試験実測は60件、0.081秒、OK。全体試験の既知20errorと署名付きcommitは未完了。検品ログの未コミット差分を保持し、Official Symphonyのチェックポイントへ引き継ぐ。
- 復旧後：全体試験 → AI-Agent署名付きcommit → 公開Draft PR #24照合 → 全条件達成時のみIssueコメント1件と対象ラベル削除。実サービス実行なし、実機結果UNKNOWN。

AI-Agent: codex

## GH-22 継続ターン9（2026-10-27・環境阻害確認）

- 開始HEAD `6a74f150f0e536999872cc98582fa81ff05b9a31`、ブランチ `symphony/gh-22-design`、開始差分なし。許可されたPR検索でmain宛てDraft PR #24、remote HEAD一致、publicを確認。
- 関連オフライン試験を今回実測：60件、0.081秒、OK。モデル・外部通信なし。`git diff --check` 合格。
- 環境実測：.gitのST_RDONLY=True、node／nodejs検出なし。既知のcommit失敗・全体試験20errorの阻害原因は未解消。同じ失敗操作は再送せず、試験のskip化・環境制約回避もしない。署名付きローカルcommitは未作成。
- BLOCKED（環境）。Official Symphony側の.git書込みとNode実行環境の復旧後、全体試験・AI-Agent署名付きcommit・公開PR照合から再開する。実サービスは実行禁止、実機結果UNKNOWN。完了用Issueコメントと対象ラベル削除は未実施。この記録をSymphonyチェックポイントへ引き継ぐ。

AI-Agent: codex

### 同一run継続20：環境阻害の引継ぎ

- 継続2〜20で.gitのST_RDONLY=True、node／nodejs不在を再測定。環境復旧なし、BLOCKED（環境）。既知の失敗commit・全体試験は再送せず、制約回避・試験skip化も行っていない。
- 今runの関連試験実測は60件、0.081秒、OK。全体試験の既知Node起因20errorと署名付きcommitは未完了。作業記録の差分を保持し、Official Symphonyのチェックポイントへ引き継ぐ。
- 復旧後：保持差分確認 → 全体試験 → AI-Agent署名付きcommit → 公開Draft PR #24照合 → 全条件達成時のみIssueコメント1件と対象ラベル削除。実サービス実行なし、実機結果UNKNOWN。

AI-Agent: codex

## GH-22 継続ターン10（2026-10-27・環境阻害確認）

- 開始HEAD `87febd447cf0dc1a8d569e51755c58d7b65afce6`、ブランチ `symphony/gh-22-design`、開始差分なし。許可されたPR検索でmain宛てDraft PR #24、remote HEAD一致、publicを確認。
- 今回実測：字幕スイッチ関連60件、0.078秒、OK。モデル・外部通信なし。差分空白検査合格。アプリコード変更なし。
- `.git` のST_RDONLY=True、node／nodejs検出なし。既知の署名付きcommitと全体試験20errorの阻害原因は未解消。同じ失敗操作は再送しない。全体試験の前回実測404件中20errorは未解決で、今回の関連60件の合格と区別する。
- BLOCKED（環境）。Official Symphony側の.git書込みとNode実行環境復旧後、全体試験・AI-Agent署名付きcommit・公開PR照合を再開。実サービス未実行、実機結果UNKNOWN。完了用Issueコメント・対象ラベル削除は未実施。記録差分をSymphonyチェックポイントへ引き継ぐ。

AI-Agent: codex

### 同一run継続20：環境阻害の引継ぎ

- 継続2〜20で.gitのST_RDONLY=True、node／nodejs不在を再測定。環境復旧なし、BLOCKED（環境）。既知の失敗commit・全体試験の再送、試験skip化、制約回避は行っていない。
- 今runの関連試験実測は60件、0.078秒、OK。全体試験の既知Node起因20errorと署名付きcommitは未完了。検品ログの差分を保持し、Official Symphonyのチェックポイントへ引き継ぐ。
- 復旧後：保持差分確認 → 全体試験 → AI-Agent署名付きcommit → 公開Draft PR #24照合 → 全条件達成時のみIssueコメント1件と対象ラベル削除。実サービス未実行、実機結果UNKNOWN。

AI-Agent: codex

## GH-22 継続ターン11（2026-10-27・環境阻害確認）

- 開始HEAD `79896fb2ee29cb8c2412b5010137d9141cc4aad9`、`symphony/gh-22-design`、開始差分なし。許可されたPR検索でmain宛てDraft PR #24、remote HEAD一致、publicを確認。
- 今回実測：字幕スイッチ関連60件、0.076秒、OK。モデル・外部サービス実行なし。差分空白検査合格。アプリコード変更なし。
- `.git` のST_RDONLY=True、node／nodejs検出なし。既知の署名付きcommitと全体試験20errorの阻害原因は未解消。同じ失敗操作は再送しない。全体試験の前回実測404件中20errorは今回再実行しておらず、関連60件の合格と区別する。
- BLOCKED（環境）。ユーザー待ち／環境待ち：Official Symphony側で.git書込みとNode実行環境を復旧後、全体試験・AI-Agent署名付きcommit・公開PR照合を再開する。実サービス未実行、実機結果UNKNOWN。完了用Issueコメント・対象ラベル削除は未実施。記録差分をSymphonyチェックポイントへ引き継ぐ。

AI-Agent: codex

### 同一run継続20：環境阻害の引継ぎ

- 継続2〜20で.gitのST_RDONLY=True、node／nodejs不在を再測定。環境復旧なし、BLOCKED（環境）。既知の失敗commit・全体試験は再送せず、試験skip化・制約回避は行っていない。
- 今runの関連試験実測は60件、0.076秒、OK。全体試験の既知Node起因20errorと署名付きcommitは未完了。検品ログの差分を保持し、Official Symphonyチェックポイントへ引き継ぐ。
- 復旧後：保持差分確認 → 全体試験 → AI-Agent署名付きcommit → 公開Draft PR #24照合 → 全条件達成時のみIssueコメント1件と対象ラベル削除。実サービス未実行、実機結果UNKNOWN。

AI-Agent: codex

## GH-22 継続ターン12（2026-10-27・環境阻害確認）

- 開始HEAD `e9ba22a198a6aee32bb80943f8fd56076d524ccb`、`symphony/gh-22-design`、開始差分なし。許可されたPR検索でmain宛てDraft PR #24、remote HEAD一致、publicを確認。
- 今回実測：字幕スイッチ関連60件、0.078秒、OK。モデル・外部サービス実行なし。差分空白検査合格。アプリコード変更なし。
- `.git` のST_RDONLY=True、node／nodejs検出なし。署名付きcommitと全体試験の既知20errorの阻害原因は未解消。同じ失敗操作は再送しない。全体試験は今回再実行していない。
- BLOCKED（環境）。ユーザー待ち／環境待ち：Official Symphony側で.git書込みとNode実行環境を復旧後、全体試験・AI-Agent署名付きcommit・公開PR照合を再開。実機UNKNOWN。完了用Issueコメント・対象ラベル削除は未実施。記録差分をSymphonyチェックポイントへ引き継ぐ。

AI-Agent: codex

### 同一run継続20：環境阻害の引継ぎ

- 継続2〜20で.gitのST_RDONLY=True、node／nodejs不在を実測。環境復旧なし、BLOCKED（環境）。失敗済みcommitや既知の全体試験の再送、試験skip化、制約回避は行っていない。
- 今runの関連試験実測は60件、0.078秒、OK。全体試験の既知Node起因20errorと署名付きcommitは未完了。記録差分を保持し、Official Symphonyチェックポイントへ引き継ぐ。
- 復旧後：保持差分確認 → 全体試験 → AI-Agent署名付きcommit → 公開Draft PR #24照合 → 全条件達成時のみIssueコメント1件と対象ラベル削除。実サービス未実行、実機結果UNKNOWN。

AI-Agent: codex
