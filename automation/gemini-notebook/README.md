# Gemini Notebook AI技術研究室: 継続研究・質問回答・時刻付き動画検索システム v0.6

**目的**: 動画を読む回数を増やすことではなく、① Geminiが既存Notebook（元資料の図書館）の知識を使って新情報を発見・検証し、詳しい技術ノートと章立てタイムラインを非公開GitHub正本へ蓄積すること、② **ユーザーの自然文の質問に対し、一次資料で検証された回答と「該当動画の正確な再生位置リンク（`&t=XXs`）」を即座に案内できる知識システム**を実現すること。

## このブランチで実装・接続したもの（v0.6）

| 部品 | 場所 | 段階 |
|---|---|---|
| Python / GAS 共通仕様契約 v1.6（章立て目次 `chapters`・詳細技術知識 `detailed_findings_ja`・関連研究 `related_records`・時刻根拠 `timestamp_source` 対応） | [contract_spec_v1.json](contract_spec_v1.json) | CANONICAL_CONTRACT_V1_6（Python/JS 100%一致・v0.5後方互換） |
| **新設 (v0.6)**: YouTube一次メタデータ・概要欄チャプター・時刻付き字幕の章別検証ツール＆検証証拠データベース | [verify_timestamps.py](verify_timestamps.py) / [state/timestamp_evidence.json](state/timestamp_evidence.json) | PRIMARY_TIMESTAMP_AUDITOR_V06（全28動画・241章を章単位照合済み） |
| **新設 (v0.6)**: 自然文質問回答・時刻付き動画箇所検索エンジン（①〜⑥パイプライン・推測時刻リンク禁止） | [query_research.py](query_research.py) | AUTOMATED_QA_SEARCH_ENGINE_V06（全15スイート `PASS`） |
| **新設 (v0.6)**: 質問回答ワークフロー＆質問窓口（Notebook / ChatGPT / CLI / Gemini）設計比較 | [QA_WORKFLOW.md](QA_WORKFLOW.md) | ARCHITECTURE_AND_WORKFLOW_DOC |
| **新設 (v0.6)**: 全研究記録・確認済みチャプター・検証結果の構造化検索カタログ | [state/video_knowledge_catalog.json](state/video_knowledge_catalog.json) | GENERATED_ON_GITHUB（28動画・全31記録・確認済み139章） |
| **PC電源OFF対応・最良案**: GASダイレクト検証・Git Database API単一アトミック保存エンジン（v0.6詳細記録・汎用正規化対応） | [cloud_relay_gas.js](cloud_relay_gas.js) | AUTOMATED_CLOUD_ENGINE_V06（Node.js互換・Mock/異常系15スイート `PASS`、本番環境でのLIVEデプロイ・PAT実行は `NOT_TESTED`） |
| ローカルCLI・基準検証ブリッジ（v0.6詳細記録・章立て目次・章別時刻根拠検証・100本〜1000本汎用スケール対応） | [receipt_to_research.py](receipt_to_research.py) | AUTOMATED_BRIDGE_V06（全15スイート `PASS`） |
| GeminiネイティブTaskの単一運用指示（v0.6 Notebook図書館化・章立てタイムライン抽出・時刻根拠ルール対応） | [GEMINI_TASK.md](GEMINI_TASK.md) | READY_TO_PASTE（Gemini側スケジュール無人実行・Drive自動出力・Notebook自動追加は `NOT_TESTED`） |
| GitHub正本×全ブランチ横断の差分・台帳エクスポート（Notebook内総合索引とは別管理） | [state/github_knowledge_index_export.md](state/github_knowledge_index_export.md) | GENERATED_ON_GITHUB（Notebookへの逆同期は `NOT_SYNCED_FROM_GITHUB`） |
| 索引の混同・上書き防止ポインタ文書 | [state/AI技術研究室_知識索引.md](state/AI技術研究室_知識索引.md) | GUARD_DOCUMENT |
| 継続研究ステート（破損時の無断初期化防止・リモートブランチ完全走査キャッシュSSOT） | [state/loop_state.json](state/loop_state.json) | GENERATED_ON_GITHUB |
| 自動テストスイート（Python/JS完全互換・9KB上限保護・章別時刻根拠検証・Q&A検索精度・100本スケール検証） | [tests/test_gemini_notebook_loop.py](../../tests/test_gemini_notebook_loop.py) | CONFIRMED_TEST（全15スイート `PASS`） |
| (参考保管) GitHub Actions クラウド受信テンプレート | [github-workflow-gemini-receipt-ingest.yml](github-workflow-gemini-receipt-ingest.yml) | OPTIONAL_REFERENCE（GAS直接保存方式ではGitHub Actions不要のため未使用） |

---

## 1. v0.6 で拡張した主要機能（動画図書館・詳細研究記録・質問回答・時刻付き検索）

### 拡張1：Notebook（元資料の図書館）とGitHub（構造化正本）の二層設計
- **Gemini Notebook の役割（純粋2ソースOKF原則）**:
  - 新規動画の登録では、1ノート300ソース枠（最大150動画相当）を厳格に保護するため、YouTube URLソースをデフォルト除外とし、純粋な**「字幕原文OKF（`AI_VIDEO_TRANSCRIPT_RAW:<video_id>`）」と「研究ノートOKF（`AI_VIDEO_RESEARCH_NOTE:<video_id>`）」の2つの独立資料登録を絶対の原則**とする（YouTube URLは追加参考オプトイン `--include-youtube-url` として併用可、※字幕全文をGitHubへ保存することは引き続き禁止）。
  - 同時に、構造化研究カード（`動画研究カード_<video_id>`）により**動画タイトル・独自要約・章立て目次（開始/終了時刻）・`&t=XXs` 再生リンク・検証結果・既存研究との関連**を併用し、既存ソースおよび総合索引 `AI技術研究室_知識索引.md` を保護する。
- **GitHub 正本の役割（文字数上限と完全保持の分離設計）**:
  - `research_receipt_v1` 契約のスキーマ上限：
    - `summary_ja`: 最大300文字・最大3改行（300文字を超える場合は先頭299文字＋`…`に切り詰め、切り詰め前の全文は `detailed_findings_ja` の「全体要約（原文保持）」行へ退避）
    - `detailed_findings_ja`: 最大2,500文字・最大25改行の構造化技術ノート（YouTube一次メタデータ比較、章別検証内訳、全体要約原文、キーワード、公式照合報告、制約・注意点、今後の応用、未確認事項、概要欄チャプター一覧を格納）
    - `chapters`（最大25章）: `title`（最大150文字、超過時は `detailed_findings_ja` へ原文退避）、`summary_ja`（最大300文字）、`key_topics`（最大8個、各60文字）
    - `claims`（最大12件）: `text`（最大500文字）
    - `related_records`（最大10件）: `note`（最大250文字）

### 拡張2：時刻・一次資料・Notebook出所の厳格検証ルール（推測補完の全面禁止）
1. **章単位の一次時刻検証（`timestamp_evidence.json`）**:
   - 一次検証データがない動画や、動画全体の尺（`dur_match`）が一致しているだけの章に `TIMESTAMPED_CAPTIONS` を付与することは禁止。
   - 各章の秒数（`seconds`）が YouTube概要欄チャプターと±2秒で一致（`DESC_MATCH` → `YOUTUBE_CHAPTER_METADATA`）、または時刻付き字幕の前後発話とトピック語彙が一致（`CAPTION_PASS` → `TIMESTAMPED_CAPTIONS`）した章のみ再生リンク（`&t=XXs`）を生成し、それ以外（`CAPTION_FAIL`, `DURATION_MISMATCH`, `CONTRADICTS_DESC`）はすべて `UNKNOWN`（`start_seconds: null`）とする。
2. **公式照合ステータスの厳格化**:
   - 一次資料の有効な `official_url`（YouTube以外のHTTPS URL）がない場合、Geminiの自己申告（`official_verification.details`）だけで `CONFIRMED_DOC` を付与することを禁止し、`REPORTED_BY_AUTHOR`（または `UNKNOWN`）として記録する。スキーマ検証でも `official_url` のない `CONFIRMED_DOC` はエラーとして拒否する。
3. **Notebookソース名・URL・Readbackの厳格化**:
   - 引継ぎファイルに `notebook_source_id`（またはCLI引数 `--notebook-source-id`）がない場合は推測でソース名を作らずエラー停止する。
   - 架空のNotebook URLを生成せず、常に正本Notebook URL（`https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7`）を使用する。
   - `notebook_readback` が省略された場合は `"UNKNOWN"` とし（自動で `"PASS"` にしない）、自己申告 `"PASS"` も `registry.json` 上では `NOTEBOOK_READBACK_SELF_REPORTED_ONLY` としてGitHub側の独立確認と明確に区別する。

### 拡張3：自然文による質問回答・時刻付き動画箇所検索エンジン (`query_research.py`)
- ユーザーの自然文質問から **①意図理解 → ②目的適合度×一次資料検証強度×時刻根拠によるGitHub検索 → ③Notebook詳細ソース案内 → ④不足知識・追加調査提案 → ⑤根拠付き回答合成 → ⑥YouTube再生リンク提示** を一気通貫で実行する。
- 確認済み時刻がある章のみ `&t=XXs` リンクを出力し、時刻が `UNKNOWN` の章は通常動画URL（`https://www.youtube.com/watch?v=...`）とGemini Notebookソース参照案内を出力する。

---

## 2. 運用上の完成条件と客観的ステータス（「Mock成功」と「本番実証」の厳格な区別）

| 評価項目 | 状態 | 根拠・証拠（Mockと本番の区別） |
|---|---|---|
| 1. コード・検索エンジン・カタログ・時刻検証DBが存在する | **PASS** | `contract_spec_v1.json` (v1.6), `verify_timestamps.py`, `state/timestamp_evidence.json`, `cloud_relay_gas.js` (v0.6), `receipt_to_research.py` (v0.6), `query_research.py` (v0.6), `state/video_knowledge_catalog.json` |
| 2. Mockテスト・互換性・異常系・Q&A検索・100本スケールテストが成功する | **PASS (ローカル/Mock実証)** | `py -m unittest discover -s tests -p "test_*.py" -v`（全15スイート PASS：Python/JS完全一致、未確認時刻の推測リンク拒否、公式URLなし `CONFIRMED_DOC` 拒否、ソース名欠落エラー停止、28動画Q&A検索精度、100本スケール変換を実証） |
| 3. GitHubへの実際の書込みが成功する | **PASS (ローカルGit→GitHub本番ブランチ)** | 非defaultブランチ `feature/gemini-notebook-research-loop-20261016` へのpushおよびcommit SHA・全ファイルblob SHAのremote readback一致を確認済み（※ローカルDriveフォルダ `G:\マイドライブ\AI技術研究室_GitHub引継ぎ` の読取はマウントパス・SHA-256照合によるもので、Google Drive APIの `folderId` 通信ではない） |
| 4. GAS本番環境からGitHub本番環境へのAPI保存 | **NOT_TESTED (本番未実施)** | Node.js上の模擬GitHub APIサーバーに対するテストは `PASS` だが、Googleクラウド上の本番GASからPATを用いた本番GitHub APIへの書込みは未実施（禁止境界を遵守） |
| 5. Notebookへの実際の更新が成功する | **NOT_TESTED (本番未実施)** | ユーザー報告によりNotebook側44ソース・総合索引の存在は把握しているが、本パイプラインからのNotebook自動更新は未実施（`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`） |
| 6. GeminiからGitHubまで手動コピーなしで処理できる | **NOT_TESTED (本番未配線)** | コード・異常系対策は完成しているが、PAT発行・GAS本番配置・Gemini実機出力の確認前であるため本番未実証 |
| 7. PCの電源が切れていても定期実行が継続する | **UNKNOWN / NOT_TESTED** | GAS → GitHub API間はPC電源OFFで動作する仕様だが、起点のGemini Scheduled Actionsが無人でGoogle Driveへ結果ファイルを出力できるかは実機未実証 |

