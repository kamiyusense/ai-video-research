# Gemini Notebook AI技術研究室: 継続研究Loop v0.3

**目的**: 動画を読む回数を増やすことではなく、Geminiが既存Notebookの知識を使って、自分で新情報を発見し、検証して、差分だけを蓄積し、非公開GitHub正本および次回調査テーマへ循環させる**一連の自動研究ワークフロー**を作る。

## このブランチで実装・接続したもの（v0.3）

| 部品 | 場所 | 段階 |
|---|---|---|
| GeminiネイティブTaskの単一運用指示（全11工程統合） | [GEMINI_TASK.md](GEMINI_TASK.md) | READY_TO_PASTE（Gemini側スケジュール無人実行は `NOT_TESTED`） |
| 知識差分からGitHub正式研究記録・GitHub側索引エクスポートを作るブリッジ | [receipt_to_research.py](receipt_to_research.py) | AUTOMATED_BRIDGE_V03（8スイート全 `PASS`） |
| **PC電源OFF対応**: Google Drive/Docs → GitHub Actions クラウド自動中継スクリプト | [cloud_relay_gas.js](cloud_relay_gas.js) | CODE_IMPLEMENTED（GAS実機デプロイ・PAT設定は `NOT_TESTED`） |
| **PC電源OFF対応**: GitHub Actions クラウド受信・検証・非defaultブランチ保存テンプレート | [github-workflow-gemini-receipt-ingest.yml](github-workflow-gemini-receipt-ingest.yml) | CODE_IMPLEMENTED（`.github/workflows/` 有効化前テンプレート） |
| GitHub正本×全ブランチ横断の差分・台帳エクスポート（Notebook内総合索引とは別管理） | [state/github_knowledge_index_export.md](state/github_knowledge_index_export.md) | GENERATED_ON_GITHUB（Notebookへの逆同期は `NOT_SYNCED_FROM_GITHUB`） |
| 索引の混同・上書き防止ポインタ文書 | [state/AI技術研究室_知識索引.md](state/AI技術研究室_知識索引.md) | GUARD_DOCUMENT |
| 継続研究ステート（破損時の無断初期化防止付き） | [state/loop_state.json](state/loop_state.json) | GENERATED_ON_GITHUB |
| 自動テストスイート（鮮度保証・本文重複照合・破損停止・Readback・クラウド変数） | [tests/test_gemini_notebook_loop.py](../../tests/test_gemini_notebook_loop.py) | CONFIRMED_TEST（8スイート全 `PASS`） |

## 1. v0.3 で修正・強化した5つの重要保証

1. **リモートブランチ重複照合での鮮度保証（古いローカル参照を信用しない）**:
   - `collect_remote_branch_videos()` は走査前に必ず `git fetch --prune origin` を実行し（`remote_dedup_freshness: "FRESH_FETCHED"`）、もし `fetch` が失敗した場合は古いローカル参照を信用せず安全停止する（オフライン明示許可時を除く）。
2. **`registry.json` だけでなく、`research/*.md` と `notes/*.md` のファイル名・本文も重複判定に利用**:
   - 現在ブランチおよび全 `origin/*` リモートブランチにおいて、`registry.json` に加え、`research/*.md`・`notes/*.md` のファイル名および本文中の `video_id:` / `record_id: youtube:<ID>` / `### NN｜<ID>` / `- `<ID>`:` パターンを走査する。これにより `registry.json` 未登録の `MVVpR2Bb0Rk`（`notes/cognitive-drift-video-series-20261010.md` 本文内）等も自動検出される。
3. **`loop_state.json` が破損・読取不能の場合、既存履歴を無断で初期化しない**:
   - `load_loop_state()` は、既存の `loop_state.json` が JSON 構文エラー・読取エラー・スキーマ違反を起こした場合に `ValueError` で即座に安全停止し、既存の処理済み履歴を絶対に空で上書きしない。
4. **新規生成した GitHub 側索引エクスポートと、Gemini Notebook 内の既存総合索引を厳格に区別**:
   - GitHub 側が生成する台帳・差分ファイルは `state/github_knowledge_index_export.md` とし、Gemini Notebook 内に既存の総合索引（`AI技術研究室_知識索引.md`、先行16ソース等の知識を含む）を丸ごと上書き置換することを禁止した。
5. **GitHub への保存成功と、Notebook への同期成功を混同しない**:
   - すべての出力 JSON・状態ファイル・研究ノートにおいて `github_write_status` と `notebook_sync_status: "NOT_SYNCED_FROM_GITHUB"` を分離した。GitHub への commit/push が成功しても、Notebook 側の索引更新完了とは扱わない。

## 2. 自宅PCの常時起動を必要としないクラウド経路の比較（公式機能・追加課金ゼロ）

```text
Gemini Task (Scheduled Actions)
  │ ① 研究結果 + `research_receipt_v1` コードブロックを出力
  ▼
Google Docs / Google Drive フォルダ (Google クラウド上)
  │ ② Google Apps Script (`cloud_relay_gas.js`) が時間主導トリガーで自動検知 (PC電源不要・無料枠)
  │    └─ SHA-256 冪等性チェック後、GitHub REST API (`repository_dispatch`) を1回呼出し (retry=0)
  ▼
GitHub Actions (`github-workflow-gemini-receipt-ingest.yml`) (GitHub クラウド上・PC電源不要・無料枠)
  │ ③ 非defaultブランチを checkout (`fetch-depth: 0`)
  │ ④ `receipt_to_research.py --payload-env RECEIPT_PAYLOAD --apply --sync-index --commit --push`
  │ ⑤ リモート readback 検証 + `github_knowledge_index_export.md` 更新
  ▼
(任意) `cloud_relay_gas.js` の `pullGitHubIndexExportToDriveDoc()`
  └─ GitHub上の `github_knowledge_index_export.md` を Google Drive の別ドキュメントへ反映
     （※Notebook内既存の `AI技術研究室_知識索引.md` は上書きしない）
```

| 方式 | 自宅PC常時起動 | 追加料金 | 人間の毎回の操作回数 | 公式仕様上の制約・必要な初回設定 |
|---|---|---|---|---|
| **方式A: クラウド完結型**<br>(Gemini → Drive/Docs → GAS `cloud_relay_gas.js` → GitHub Actions) | **不要（PC電源OFFで動作）** | **0円** | **0〜1回**<br>・Workspace拡張で自動Docs保存が通る場合: **0回**<br>・Gemini画面で「Googleドキュメントにエクスポート」を1クリックする場合: **1回** | ・初回のみ GAS プロジェクト作成＋Fine-grained PAT 設定＋ワークフローの `.github/workflows/` 配置が必要。<br>・Gemini Scheduled Actions が無人で Docs 作成まで完走するかは実機未検証（`UNKNOWN`）。 |
| **方式B: GitHub Web/スマホ直接投入型**<br>(Gemini → GitHub Actions `workflow_dispatch`) | **不要（PC電源OFFで動作）** | **0円** | **スマホ/Webで2操作**<br>（Geminiでコピー → GitHub Actions画面に貼付・Run） | GAS 設定すら不要。PCを開かずにスマホのブラウザだけで検証・全ブランチ重複照合・GitHub保存が完結する。 |
| **方式C: ローカルPCワンコマンド型**<br>(`receipt_to_research.py --from-clipboard` / `--inbox`) | **実行時のみPC起動が必要** | **0円** | **1回**<br>（コピーして1コマンド実行、またはDriveフォルダ同期） | 現在のブランチで今すぐ追加設定なしで動作する（実機テスト済み）。 |

## 3. 運用上の完成条件と現在の客観的ステータス

| 評価項目 | 状態 | 根拠・証拠 |
|---|---|---|
| 1. コードが存在する | **PASS** | `receipt_to_research.py` (v0.3), `cloud_relay_gas.js`, `github-workflow-gemini-receipt-ingest.yml`, `GEMINI_TASK.md` |
| 2. Mockテストが成功する | **PASS** | `py tests/test_gemini_notebook_loop.py`（全8スイート PASS：鮮度保証fetch、Markdown本文重複検出、`loop_state.json` 破損時停止、索引分離、Git push/readback、クラウド環境変数入力） |
| 3. GitHubへの実際の書込みが成功する | **PASS** | 非defaultブランチ `feature/gemini-notebook-research-loop-20261016` への push および GitHub API / `git ls-remote` による commit SHA・全ファイル blob SHA 読み戻し一致を確認 |
| 4. Notebookへの実際の更新が成功する | **NOT_TESTED** | 過去にユーザー手動実行による16ソース登録報告はあるが、今回の v0.3 パイプラインからの Notebook 実機更新は未実施（`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`） |
| 5. GeminiからGitHubまで手動コピーなしで処理できる | **NOT_TESTED (コード実装済み・初回配線待ち)** | Drive/Docs → GAS (`cloud_relay_gas.js`) → GitHub Actions (`repository_dispatch`) のコードは完成しているが、PAT 発行・Actions 有効化を無断で行わない安全境界のため LIVE 疎通は未実施 |
| 6. PCの電源が切れていても定期実行が継続する | **UNKNOWN / NOT_TESTED** | GAS＋GitHub Actions 側は PC 電源 OFF でクラウド動作する公式仕様だが、起点となる Gemini Scheduled Actions の無人 Notebook 更新・Docs 出力が継続完走するかは実機未実証 |
