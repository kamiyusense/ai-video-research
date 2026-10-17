# Gemini Notebook AI技術研究室: 継続研究・質問回答・時刻付き動画検索システム v0.6

**目的**: 動画を読む回数を増やすことではなく、① Geminiが既存Notebook（元資料の図書館）の知識を使って新情報を発見・検証し、詳しい技術ノートと章立てタイムラインを非公開GitHub正本へ蓄積すること、② **ユーザーの自然文の質問に対し、一次資料で検証された回答と「該当動画の正確な再生位置リンク（`&t=XXs`）」を即座に案内できる知識システム**を実現すること。

## このブランチで実装・接続したもの（v0.6）

| 部品 | 場所 | 段階 |
|---|---|---|
| Python / GAS 共通仕様契約 v1.6（章立て目次 `chapters`・詳細技術知識 `detailed_findings_ja`・関連研究 `related_records`・時刻根拠 `timestamp_source` 対応） | [contract_spec_v1.json](contract_spec_v1.json) | CANONICAL_CONTRACT_V1_6（Python/JS 100%一致・v0.5後方互換） |
| **新設 (v0.6)**: 自然文質問回答・時刻付き動画箇所検索エンジン（①〜⑥パイプライン・推測時刻リンク禁止） | [query_research.py](query_research.py) | AUTOMATED_QA_SEARCH_ENGINE_V06（全12スイート `PASS`） |
| **新設 (v0.6)**: 質問回答ワークフロー＆質問窓口（Notebook / ChatGPT / CLI / Gemini）設計比較 | [QA_WORKFLOW.md](QA_WORKFLOW.md) | ARCHITECTURE_AND_WORKFLOW_DOC |
| **新設 (v0.6)**: 全研究記録・確認済みチャプター・検証結果の構造化検索カタログ | [state/video_knowledge_catalog.json](state/video_knowledge_catalog.json) | GENERATED_ON_GITHUB |
| **PC電源OFF対応・最良案**: GASダイレクト検証・Git Database API単一アトミック保存エンジン（v0.6詳細記録対応） | [cloud_relay_gas.js](cloud_relay_gas.js) | AUTOMATED_CLOUD_ENGINE_V06（Node.js互換・Mock/異常系12スイート `PASS`、本番環境でのLIVEデプロイ・PAT実行は `NOT_TESTED`） |
| ローカルCLI・基準検証ブリッジ（v0.6詳細記録・章立て目次・時刻根拠検証対応） | [receipt_to_research.py](receipt_to_research.py) | AUTOMATED_BRIDGE_V06（全12スイート `PASS`） |
| GeminiネイティブTaskの単一運用指示（v0.6 Notebook図書館化・章立てタイムライン抽出・時刻根拠ルール対応） | [GEMINI_TASK.md](GEMINI_TASK.md) | READY_TO_PASTE（Gemini側スケジュール無人実行・Drive自動出力・Notebook自動追加は `NOT_TESTED`） |
| GitHub正本×全ブランチ横断の差分・台帳エクスポート（Notebook内総合索引とは別管理） | [state/github_knowledge_index_export.md](state/github_knowledge_index_export.md) | GENERATED_ON_GITHUB（Notebookへの逆同期は `NOT_SYNCED_FROM_GITHUB`） |
| 索引の混同・上書き防止ポインタ文書 | [state/AI技術研究室_知識索引.md](state/AI技術研究室_知識索引.md) | GUARD_DOCUMENT |
| 継続研究ステート（破損時の無断初期化防止・リモートブランチ完全走査キャッシュSSOT） | [state/loop_state.json](state/loop_state.json) | GENERATED_ON_GITHUB |
| 自動テストスイート（Python/JS完全互換・9KB上限保護・詳細研究ノート・時刻根拠検証・Q&A検索） | [tests/test_gemini_notebook_loop.py](../../tests/test_gemini_notebook_loop.py) | CONFIRMED_TEST（全12スイート `PASS`） |
| (参考保管) GitHub Actions クラウド受信テンプレート | [github-workflow-gemini-receipt-ingest.yml](github-workflow-gemini-receipt-ingest.yml) | OPTIONAL_REFERENCE（GAS直接保存方式ではGitHub Actions不要のため未使用） |

---

## 1. v0.6 で拡張した主要機能（動画図書館・詳細研究記録・質問回答・時刻付き検索）

### 拡張1：Notebook（元資料の図書館）とGitHub（構造化正本）の二層設計
- **Gemini Notebook の役割**:
  - 公開・字幕ありのYouTube動画は可能な限り**動画URLをNotebookソースとして登録**し、Notebook自身が取得できる字幕由来の詳細文脈を参照できるようにする（※字幕全文をGitHubへコピー・保存することは引き続き禁止）。
  - 同時に、YouTube URL登録だけではNotebook内部で秒単位のタイムスタンプが失われる弱点を補うため、**動画タイトル・URL・独自要約・章立て目次（開始/終了時刻）・`&t=XXs` 再生リンク・検証結果・既存研究との関連**をまとめた構造化研究カードを併用し、既存ソースおよび総合索引 `AI技術研究室_知識索引.md` を保護する。
- **GitHub 正本の役割（300文字制限の解消と後方互換拡張）**:
  - 従来の `summary_ja`（300文字以内の概要要約）を維持したまま、`research_receipt_v1` 契約に以下の任意フィールドを後方互換で追加し、Python（`receipt_to_research.py`）とGAS（`cloud_relay_gas.js`）の双方で100%同一のMarkdownとして出力する：
    1. `chapters`: 動画全体の章立て・確認済みタイムライン（`title`, `start_seconds`, `end_seconds`, `summary_ja`, `timestamp_source`, `key_topics`）
    2. `detailed_findings_ja`: 最大2,500文字・最大25改行の構造化技術ノート（仕組み・適用条件・失敗例・再利用手順。禁止キー・禁止文字列パターン検査により字幕丸写しや秘密情報はブロック）
    3. `related_records`: 既存研究やP006未解決課題との接続（`EXTENDS`, `UPDATES`, `COMPLEMENTS`, `CONTRADICTS`, `RESOLVES_BACKLOG`）

### 拡張2：時刻の信頼性ルール（確認根拠 `timestamp_source` の必須化と推測リンク禁止）
- 各章（`chapters`）および主張（`claims`）のタイムスタンプには確認根拠（`YOUTUBE_CHAPTER_METADATA`, `TIMESTAMPED_CAPTIONS`, `VISUAL_FRAME_CHECK`, `OFFICIAL_TIME_RANGE`, `UNKNOWN`）を記録する。
- `timestamp_source == "UNKNOWN"` の場合に秒数を指定することはバリデーションで拒否され、またレンダリング・検索時にも**確認済み時刻がある場合のみ** `[MM:SS〜MM:SS](https://www.youtube.com/watch?v=<ID>&t=<sec>s)` リンクを生成し、未確認時刻は `UNKNOWN` と明示する。

### 拡張3：自然文による質問回答・時刻付き動画箇所検索エンジン (`query_research.py`)
- ユーザーの自然文質問から **①意図理解 → ②目的適合度×一次資料検証強度×時刻根拠によるGitHub検索 → ③Notebook詳細ソース案内 → ④不足知識・追加調査提案 → ⑤根拠付き回答合成 → ⑥YouTube再生リンク提示** を一気通貫で実行する。
- 詳しい運用手順と質問窓口（ChatGPT / ローカルCLI / Gemini Notebook / Gemini App）の比較は [QA_WORKFLOW.md](QA_WORKFLOW.md) を参照。

---

## 2. 運用上の完成条件と客観的ステータス（「Mock成功」と「本番実証」の厳格な区別）

| 評価項目 | 状態 | 根拠・証拠（Mockと本番の区別） |
|---|---|---|
| 1. コード・検索エンジン・カタログが存在する | **PASS** | `contract_spec_v1.json` (v1.6), `cloud_relay_gas.js` (v0.6), `receipt_to_research.py` (v0.6), `query_research.py` (v0.6), `QA_WORKFLOW.md`, `state/video_knowledge_catalog.json` |
| 2. Mockテスト・互換性・異常系・Q&A検索テストが成功する | **PASS (ローカル/Mock実証)** | `py -3 tests/test_gemini_notebook_loop.py`（全12スイート PASS：v0.5全項目に加え、v0.6の章立て目次・詳細技術ノート・関連研究のPython/JS完全一致、未確認時刻の推測リンク拒否、自然文質問からの該当チャプター `&t=XXs` 検索・知識ギャップ検出を実証） |
| 3. GitHubへの実際の書込みが成功する | **PASS (ローカルGit→GitHub本番ブランチ)** | 非defaultブランチ `feature/gemini-notebook-research-loop-20261016` へのpushおよびcommit SHA・全ファイルblob SHAのremote readback一致を確認済み |
| 4. GAS本番環境からGitHub本番環境へのAPI保存 | **NOT_TESTED (本番未実施)** | Node.js上の模擬GitHub APIサーバーに対するテストは `PASS` だが、Googleクラウド上の本番GASからPATを用いた本番GitHub APIへの書込みは未実施（禁止境界を遵守） |
| 5. Notebookへの実際の更新が成功する | **NOT_TESTED (本番未実施)** | 過去にユーザー手動実行による16ソース登録報告はあるが、本パイプラインからのNotebook実機更新は未実施（`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`） |
| 6. GeminiからGitHubまで手動コピーなしで処理できる | **NOT_TESTED (本番未配線)** | コード・異常系対策は完成しているが、PAT発行・GAS本番配置・Gemini実機出力の確認前であるため本番未実証 |
| 7. PCの電源が切れていても定期実行が継続する | **UNKNOWN / NOT_TESTED** | GAS → GitHub API間はPC電源OFFで動作する仕様だが、起点のGemini Scheduled Actionsが無人でGoogle Driveへ結果ファイルを出力できるかは実機未実証 |
