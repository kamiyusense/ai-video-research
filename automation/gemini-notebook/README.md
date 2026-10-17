# Gemini Notebook AI技術研究室: 継続研究Loop v0.5 (GASダイレクト検証・Git Database API単一アトミック保存方式)

**目的**: 動画を読む回数を増やすことではなく、Geminiが既存Notebookの知識を使って、自分で新情報を発見し、検証して、差分だけを蓄積し、非公開GitHub正本および次回調査テーマへ循環させる**一連の自動研究ワークフロー**を作る。

## このブランチで実装・接続したもの（v0.5）

| 部品 | 場所 | 段階 |
|---|---|---|
| Python / GAS 共通仕様契約（スキーマ・禁止キー・禁止文字列パターン・GAS 9KB保護制限） | [contract_spec_v1.json](contract_spec_v1.json) | CANONICAL_CONTRACT_V1_5（Python/JS 100%一致検証済み） |
| **PC電源OFF対応・最良案**: GASダイレクト検証・Git Database API単一アトミック保存エンジン | [cloud_relay_gas.js](cloud_relay_gas.js) | AUTOMATED_CLOUD_ENGINE_V05（Node.js互換・Mock/異常系11スイート `PASS`、Google/GitHub本番環境でのLIVEデプロイ・PAT実行は `NOT_TESTED`） |
| ローカルCLI・基準検証ブリッジ（共通契約対応・増分ブランチキャッシュ・文字列パターン検査搭載） | [receipt_to_research.py](receipt_to_research.py) | AUTOMATED_BRIDGE_V05（全11スイート `PASS`） |
| GeminiネイティブTaskの単一運用指示（v0.5 GAS直接保存方式対応・未実証境界明記） | [GEMINI_TASK.md](GEMINI_TASK.md) | READY_TO_PASTE（Gemini側スケジュール無人実行・Drive自動出力・Notebook自動追加は `NOT_TESTED`） |
| GitHub正本×全ブランチ横断の差分・台帳エクスポート（Notebook内総合索引とは別管理） | [state/github_knowledge_index_export.md](state/github_knowledge_index_export.md) | GENERATED_ON_GITHUB（Notebookへの逆同期は `NOT_SYNCED_FROM_GITHUB`） |
| 索引の混同・上書き防止ポインタ文書 | [state/AI技術研究室_知識索引.md](state/AI技術研究室_知識索引.md) | GUARD_DOCUMENT |
| 継続研究ステート（破損時の無断初期化防止・リモートブランチ完全走査キャッシュSSOT） | [state/loop_state.json](state/loop_state.json) | GENERATED_ON_GITHUB |
| 自動テストスイート（Python/JS完全互換・9KB上限保護・ページネーション・truncated停止・分割継続走査） | [tests/test_gemini_notebook_loop.py](../../tests/test_gemini_notebook_loop.py) | CONFIRMED_TEST（全11スイート `PASS`） |
| (参考保管) GitHub Actions クラウド受信テンプレート | [github-workflow-gemini-receipt-ingest.yml](github-workflow-gemini-receipt-ingest.yml) | OPTIONAL_REFERENCE（GAS直接保存方式ではGitHub Actions不要のため未使用） |

---

## 1. v0.5 で修正・強化した5つの重要課題（別AI独立コードレビューへの完全対応）

### 問題1対策：GAS `ScriptProperties` の1値9KB制限の厳格保護（GitHub正本SSOT化）
- **課題**: GASの `ScriptProperties` は1つのキーあたり **9KB（9,216 bytes）** の上限があり、処理済みReceipt履歴やブランチキャッシュをGAS側に蓄積し続けると将来容量超過で停止する危険があった。
- **解決策**:
  1. 永続的な処理済みReceipt履歴（`processed_receipts`）と完了済みリモートブランチキャッシュ（`remote_branch_cache`）は、容量制限のない **GitHub正本の `automation/gemini-notebook/state/loop_state.json` 側（SSOT）に保存・参照** する設計に変更した。
  2. GAS側の `RELAY_STATE_V1` には最小限の揮発制御情報（`lastGitHubCommitSha`, `lastDriveSyncedCommitSha`, `pendingDriveSync`, 直近のNo-Opダイジェスト最大20件、停止記録最大10件、分割スキャン再開カーソル `partialScanProgress`）のみを保持し、`saveBoundedRelayState_()` により **常に7,500 bytes以下** に自動トリム・制限する。

### 問題2対策：重複検出の完全性保証（ページネーション・`truncated` 検知・分割継続スキャン）
- **課題**: ① `/branches?per_page=100` が1ページ目しか取得していなかった、② Git Trees API の `truncated: true` を検査していなかった、③ Markdown本文読取上限（25件/回）に達して未調査ファイルが残ってもブランチを完了扱いにして重複確認PASSに進む危険があった。
- **解決策**:
  1. **全ページ取得**: `/branches?per_page=100&page=N` を最終ページ（100件未満）までループ取得する。
  2. **`truncated` の厳格拒否**: `GET /git/trees/{tree_sha}?recursive=1` の応答で `truncated === true` を検知した場合は、不完全な重複照合を拒否して即座に例外停止する。
  3. **未完走ブランチのキャッシュ昇格禁止と分割継続スキャン**: 1実行あたりのBlob読取上限（`max_blob_fetches_per_run = 25`）に達して未調査のMarkdownファイルが残った場合、`dedupScanComplete = false` とし、そのブランチを完了扱い（`scan_complete: true`）にしない。当該実行ではGitHubへのコミットを安全に保留（`PAUSED_INCOMPLETE_DEDUP_SCAN_CONTINUES_NEXT_RUN`）し、`partialScanProgress` に記録した調査済みパスから次回実行時に残りのファイルを継続走査する。全ファイルの走査が完了した時点で初めて `scan_complete: true` としてコミット処理へ進む。

### 問題3対策：GitHub REST API 公式仕様との完全一致（Commit SHA → Tree SHA 解決）
- **課題**: 対象ブランチでは `/git/commits/{commit_sha}` から `tree.sha` を取得していたが、他ブランチでは `/git/trees/` に直接 `commit_sha` を渡しており、また他ブランチのTree取得失敗時に `continue` でスキップしていた。
- **解決策**:
  1. 対象ブランチだけでなく**すべての他ブランチ**において、必ず `GET /repos/{owner}/{repo}/git/commits/{commit_sha}` を呼んで公式の `tree.sha` を解決してから `GET /repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1` を呼び出すよう統一した。
  2. 他ブランチのCommit/Tree/registry取得でHTTPエラーやJSON破損が発生した場合は無言で `continue` せず、即座に安全停止する。
  3. Mockテスト（`test_10`, `test_11`）の模擬GitHubサーバー側でも、`/git/trees/` に `commit_sha` が渡された場合は `HTTP 404` で拒否する厳格な検証に変更した。

### 問題4対策：`GEMINI_TASK.md` の現行アーキテクチャ（GAS直接保存方式）への更新
- [GEMINI_TASK.md](GEMINI_TASK.md) に残っていた旧v0.3のGitHub Actions経由の説明を削除し、GASダイレクト検証・Git Database API単一アトミック保存方式に統一した。
- 同時に、「Gemini Scheduled Actionsからの無人Google Drive出力」および「Scheduled Actions実行中のNotebookへの自律ソース追加」は実機未実証（`NOT_TESTED` / `UNKNOWN`）であり、未確認のまま完了と自己申告してはならないことを明記した。

### 問題5対策：文字列フィールド値に対する秘密情報・字幕転載パターン検査と限界の明示
- **実装した多層検査**:
  - 禁止キー名（`transcript`, `subtitles`, `api_key`, `secret` 等）の拒否に加え、**すべての文字列フィールドの値（`summary_ja`, `claims[].text`, `unknowns[]` 等）** に対して以下の正規表現パターン検査と改行制限（最大3改行）を Python / GAS 双方で強制した：
    - GitHub PAT / OAuthトークン（`ghp_...`, `github_pat_...`）
    - Google APIキー / OAuthトークン（`AIza...`, `ya29....`）
    - OpenAI / Anthropic / Slack 等のシークレットキー（`sk-...`, `xoxb-...`）
    - PEM秘密鍵ブロック（`-----BEGIN ... PRIVATE KEY-----`）および `Bearer` トークン
    - SRT / WebVTT 字幕タイムコード（`WEBVTT`, `00:01:20,000 --> ...`）
    - 3行以上連続するタイムスタンプ付き文字起こし行
- **機械的検証の限界（残留リスク）の明示**:
  - 上記の決定論的検査により既知形式のトークン漏洩や字幕塊の混入はGitHub送信前に遮断できるが、**「タイムスタンプを持たない300字以内の短い丸写し」や「特定のプレフィックスを持たない未知形式の機密文字列」を機械検査だけで100%完全にゼロにすることは原理的に不可能**である。
  - そのため、「禁止データ混入リスクがゼロ」とは見なさず、自動保存先は必ず **非defaultブランチ（Draft PR #10）に隔離** し、人間が最終確認してから `main` へマージする運用境界を維持する。

---

## 2. 運用上の完成条件と客観的ステータス（「Mock成功」と「本番実証」の厳格な区別）

| 評価項目 | 状態 | 根拠・証拠（Mockと本番の区別） |
|---|---|---|
| 1. コードが存在する | **PASS** | `contract_spec_v1.json` (v1.5), `cloud_relay_gas.js` (v0.5), `receipt_to_research.py` (v0.5), `GEMINI_TASK.md` |
| 2. Mockテスト・互換性・異常系テストが成功する | **PASS (ローカル/Mock実証)** | `py -3 tests/test_gemini_notebook_loop.py`（全11スイート PASS：Python/JS完全一致、9KB制限トリム、2ページ分岐取得、30ファイル分割継続走査、truncated停止、Commit→Tree SHA厳格解決、文字列内PAT/SRT拒否） |
| 3. GitHubへの実際の書込みが成功する | **PASS (ローカルGit→GitHub本番ブランチ)** | 非defaultブランチ `feature/gemini-notebook-research-loop-20261016` へのpushおよびcommit SHA・全ファイルblob SHAのremote readback一致を確認済み |
| 4. GAS本番環境からGitHub本番環境へのAPI保存 | **NOT_TESTED (本番未実施)** | Node.js上の模擬GitHub APIサーバーに対するテストは `PASS` だが、Googleクラウド上の本番GASからPATを用いた本番GitHub APIへの書込みは未実施（禁止境界を遵守） |
| 5. Notebookへの実際の更新が成功する | **NOT_TESTED (本番未実施)** | 過去にユーザー手動実行による16ソース登録報告はあるが、本パイプラインからのNotebook実機更新は未実施（`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`） |
| 6. GeminiからGitHubまで手動コピーなしで処理できる | **NOT_TESTED (本番未配線)** | コード・異常系対策は完成しているが、PAT発行・GAS本番配置・Gemini実機出力の確認前であるため本番未実証 |
| 7. PCの電源が切れていても定期実行が継続する | **UNKNOWN / NOT_TESTED** | GAS → GitHub API間はPC電源OFFで動作する仕様だが、起点のGemini Scheduled Actionsが無人でGoogle Driveへ結果ファイルを出力できるかは実機未実証 |
