# Gemini Notebook AI技術研究室: 継続研究Loop v0.4 (GASダイレクト検証・Git Database API単一アトミック保存方式)

**目的**: 動画を読む回数を増やすことではなく、Geminiが既存Notebookの知識を使って、自分で新情報を発見し、検証して、差分だけを蓄積し、非公開GitHub正本および次回調査テーマへ循環させる**一連の自動研究ワークフロー**を作る。

## このブランチで実装・接続したもの（v0.4）

| 部品 | 場所 | 段階 |
|---|---|---|
| Python / GAS 共通仕様契約（スキーマ・禁止キー・制限値・初期バックログ） | [contract_spec_v1.json](contract_spec_v1.json) | CANONICAL_CONTRACT_V1_4（Python/JS 100%一致検証済み） |
| **PC電源OFF対応・最良案**: GASダイレクト検証・Git Database API単一アトミック保存エンジン | [cloud_relay_gas.js](cloud_relay_gas.js) | AUTOMATED_CLOUD_ENGINE_V04（Node.js互換・Mock実演 `PASS`、実機デプロイ・PAT設定は `NOT_TESTED`） |
| ローカルCLI・基準検証ブリッジ（共通契約対応・増分ブランチキャッシュ搭載） | [receipt_to_research.py](receipt_to_research.py) | AUTOMATED_BRIDGE_V04（全10スイート `PASS`） |
| GeminiネイティブTaskの単一運用指示（全11工程統合） | [GEMINI_TASK.md](GEMINI_TASK.md) | READY_TO_PASTE（Gemini側スケジュール無人実行は `NOT_TESTED`） |
| GitHub正本×全ブランチ横断の差分・台帳エクスポート（Notebook内総合索引とは別管理） | [state/github_knowledge_index_export.md](state/github_knowledge_index_export.md) | GENERATED_ON_GITHUB（Notebookへの逆同期は `NOT_SYNCED_FROM_GITHUB`） |
| 索引の混同・上書き防止ポインタ文書 | [state/AI技術研究室_知識索引.md](state/AI技術研究室_知識索引.md) | GUARD_DOCUMENT |
| 継続研究ステート（破損時の無断初期化防止付き） | [state/loop_state.json](state/loop_state.json) | GENERATED_ON_GITHUB |
| 自動テストスイート（Python/JS完全互換・GASアトミック保存・競合停止・Drive自己修復） | [tests/test_gemini_notebook_loop.py](../../tests/test_gemini_notebook_loop.py) | CONFIRMED_TEST（全10スイート `PASS`） |
| (参考保管) GitHub Actions クラウド受信テンプレート | [github-workflow-gemini-receipt-ingest.yml](github-workflow-gemini-receipt-ingest.yml) | OPTIONAL_REFERENCE（v0.4ではGitHub Actions不要のため未使用） |

---

## 1. v0.4 アーキテクチャ（GitHub Actions不要・`main`変更ゼロ・生データ汚染ゼロ）

```text
Gemini Task (Scheduled Actions / 手動実行)
  │ ① 研究結果 + `research_receipt_v1` コードブロックを出力
  ▼
Google Docs / Google Drive Inbox フォルダ (Google クラウド上)
  │ ② Google Apps Script (`cloud_relay_gas.js` v0.4) が時間主導トリガーで自動検知 (PC電源不要・無料枠)
  │    ├─ LockService (`getScriptLock()`) により多重起動・同時実行を排他制御
  │    ├─ 共通契約 (`contract_spec_v1.json`) に基づくスキーマ検証・禁止キー拒否（字幕全文・機密情報の混入をメモリ上で遮断）
  │    ├─ GitHub REST API (Branches + Git Trees API) と Commit SHA キャッシュによる省通信・全ブランチ横断重複検査
  │    ├─ Git Database API (`POST /git/blobs` → `POST /git/trees` → `POST /git/commits` → `PATCH /git/refs/heads/<branch>` with `force: false`)
  │    │  により、検証合格データのみを非defaultブランチへ【1回の単一アトミックコミット】で直接保存
  │    ├─ 即時 Remote Readback（Commit SHA および全ファイルの Git Blob SHA 一致確認）
  │    └─ 2フェーズ状態管理＋自己修復 (Self-Healing Reconciliation) により Google Drive 上の知識索引Docを更新
  ▼
非公開 GitHub (`kamiyusense/ai-video-research` の許可済み非defaultブランチ)
  └─ `research/YYYY-MM-DD-<video_id>-gemini-notebook.md`
  └─ `registry.json`
  └─ `automation/gemini-notebook/state/loop_state.json`
  └─ `automation/gemini-notebook/state/github_knowledge_index_export.md`
```

---

## 2. 別AI（ChatGPT / GPT-6）の追加レビュー4懸念に対するv0.4の技術的解決策

### 懸念A対策：Python (`receipt_to_research.py`) と JavaScript (`cloud_relay_gas.js`) の二重実装・乖離防止
1. **機械可読な単一共通契約 (`contract_spec_v1.json`) の導入**:
   - スキーマバージョン、許可ステータス、文字数上限、禁止キー（`transcript`, `subtitles`, `raw_transcript`, `api_key`, `secret` 等）、対象リポジトリ、禁止ブランチ（`main`, `master`）を [contract_spec_v1.json](contract_spec_v1.json) に一元化した。
2. **Node.js × Python 自動互換性テスト (`test_09_python_js_cross_language_contract_and_output_parity`)**:
   - `cloud_relay_gas.js` を Google Apps Script と Node.js の両方で動作するハイブリッドモジュールとして設計し、`tests/test_gemini_notebook_loop.py` 内で Node.js を呼び出して Python 実装と JS 実装の出力を直接照合している。
   - 正規化 SHA-256 ダイジェスト、生成される `research/*.md`、差分更新セクション（`## 差分更新`）、および `github_knowledge_index_export.md` が **1バイトの狂いもなく100%完全一致** することを自動テストで強制保証している。

### 懸念B対策：GASの実行時間（6分制限）・API呼び出し回数のスケーラビリティ
1. **Git Trees API (`?recursive=1`) によるファイル名からのゼロ通信ID抽出**:
   - 各ブランチのファイル一覧と Blob SHA は `GET /git/trees/{sha}?recursive=1` の **1回のHTTPリクエスト**（最大10万ファイル対応）で一括取得できる。
   - `research/YYYY-MM-DD-<video_id>-*.md` の動画IDはファイルパス文字列だけで抽出できるため、各研究ファイルのMarkdown本文を毎回ダウンロードする必要がない。
2. **ブランチ Commit SHA キャッシュ (`branchCache`) と1実行あたりBlob読取上限 (`max_blob_fetches_per_run = 25`)**:
   - 各リモートブランチの最新 Commit SHA を `RELAY_STATE_V1.branchCache`（Python側では `loop_state.json` 連携）に記録し、前回から変更がないブランチは **API呼び出し0回** でキャッシュ済み動画IDリストを再利用する。
   - 本文検査が必要な `notes/*.md` 等も未走査ブランチのみ対象とし、1実行あたりのBlob取得数を最大25件に制限することで、将来研究ファイルが1,000件を超えても1回のGAS実行は数秒（API呼び出し10回前後）で完了する。

### 懸念C対策：Fine-grained PAT の権限範囲とブランチ保護の厳格な区別
1. **「プログラム上の拒否（Application Guard）」と「認証キー/サーバー上の拒否（Platform Guard）」の明確な分離**:
   - GitHub の Fine-grained PAT（`Contents: Read and Write`）はリポジトリ単位の権限であるため、トークン単体の機能だけでは任意の作業ブランチのみに書込みを制限できない。
   - **第1層（アプリケーション層ガード）**: `verifyTargetBranchBoundary_()` が `FORBIDDEN_BRANCHES = ["main", "master"]` を強制し、設定ミスがあっても `main` への書込みリクエスト自体を生成しない。
   - **第2層（GitHubサーバー層ガード）**: GitHub 側で `main` ブランチに Branch Protection / Ruleset を設定することで、万が一トークン単体で直接APIが呼ばれてもサーバー側が拒否する（※GitHubの仕様上、非公開リポジトリでのサーバー側ブランチ保護の強制には GitHub Pro/Team プランが必要であり、Freeプランでは第1層ガード＋最小権限運用が中心となる。GASは実行時に `mainBranchServerProtected` の真偽値をAPIで確認してレポートに明記する）。

### 懸念D対策：GitHubとGoogle Driveの更新不一致（Split-Brain）の自己修復・同時実行排他・ブランチ競合停止
1. **GAS同時実行の排他制御 (`LockService.getScriptLock()`)**:
   - `relayDriveReceiptsToGitHub()` の冒頭でスクリプト排他ロック（`tryLock(5000)`）を取得し、`finally` ブロックで必ず解放する。定期トリガーと手動実行が重なっても同時実行は発生しない。
2. **GitHubブランチ競合の原子的拒否 (`force: false` / HTTP 422 安全停止)**:
   - `PATCH /git/refs/heads/<branch>` に必ず `force: false` を指定する。GASの読取からコミットまでの間に別コミットがPushされていた場合、GitHubサーバーが `HTTP 422 (Update is not a fast forward)` で原子的に拒否し、GASは上書きも再試行もせず安全停止する。
3. **GitHub保存成功後にGoogle Drive更新が失敗した場合の2フェーズ自己修復 (Self-Healing Reconciliation)**:
   - **GitHubを唯一の正本（SSOT）、Google Driveの索引ドキュメントを派生ビュー（Derived View）**として扱う。
   - **ケース1（GitHubコミット成功後、Drive Doc更新でエラーが発生した場合）**:
     - GitHubコミット完了時点で `RELAY_STATE_V1` に `lastGitHubCommitSha` と `pendingDriveSync: true` を保存する。
     - 次回のGAS実行時、同じReceiptファイルに対しては `SKIP_DUPLICATE_ALREADY_COMMITTED_ON_GITHUB` として**GitHubへの二重コミットを完全に防止**した上で、関数末尾の自己修復フェーズ（`driveReconciliation`）が GitHub 正本の `github_knowledge_index_export.md` を読み取って Google Drive のドキュメントを自動修復する（`RECONCILED_FROM_GITHUB_SSOT`）。
   - **ケース2（GitHubコミット成功直後、`RELAY_STATE_V1` の保存前にGASが強制終了した場合）**:
     - 次回実行時、GASはGitHub上の `loop_state.json`（単一アトミックコミット内に含まれているため必ず更新済み）を読み取り、`processed_receipts` に当該 `sha256` が既に存在することを検知してローカル状態を自己修復（`HEALED_FROM_GITHUB_SSOT_ALREADY_COMMITTED`）し、Drive側の更新だけを実行する。

---

## 3. 運用上の完成条件と現在の客観的ステータス（v0.4）

| 評価項目 | 状態 | 根拠・証拠 |
|---|---|---|
| 1. コードが存在する | **PASS** | `contract_spec_v1.json`, `cloud_relay_gas.js` (v0.4), `receipt_to_research.py` (v0.4), `GEMINI_TASK.md` |
| 2. Mockテスト・互換性テストが成功する | **PASS** | `py -3 tests/test_gemini_notebook_loop.py`（全10スイート PASS：Python/JS完全一致、GASアトミック保存、LockService排他、422競合停止、Drive自己修復） |
| 3. GitHubへの実際の書込みが成功する | **PASS** | 非defaultブランチ `feature/gemini-notebook-research-loop-20261016` への push および commit SHA・全ファイル blob SHA 読み戻し一致を確認 |
| 4. Notebookへの実際の更新が成功する | **NOT_TESTED** | 過去にユーザー手動実行による16ソース登録報告はあるが、v0.4パイプラインからのNotebook実機更新は未実施（`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`） |
| 5. GeminiからGitHubまで手動コピーなしで処理できる | **NOT_TESTED (コード完成・初回PAT/GAS設定待ち)** | GAS単体でDrive検知からGitHub非defaultブランチへの直接アトミック保存まで完結するコードは完成しMock実証済みだが、無断でのPAT発行・GASデプロイを行わない安全境界のため実機疎通は未実施 |
| 6. PCの電源が切れていても定期実行が継続する | **UNKNOWN / NOT_TESTED** | GAS → GitHub API 保存経路はPC電源OFFで100%クラウド動作する公式仕様だが、起点となる **Gemini Scheduled Actions が無人で研究完走し Google Drive の指定受信先へ出力できるか** は公式仕様上保証されておらず実機未実証 |
