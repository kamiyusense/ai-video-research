# GitHub正本 知識索引・差分エクスポート (`github_knowledge_index_export.md`)

> **【重要：索引の区別と上書き禁止】**
> - このファイルは **GitHub 正本（`kamiyusense/ai-video-research`）側の既知動画台帳・未解決課題・次回テーマの差分エクスポート** です。
> - Gemini Notebook 内に既存の総合索引ソース **`AI技術研究室_知識索引.md`**（先行16ソース等の蓄積を含む総合索引）とは**別物**です。
> - Notebook 内の `AI技術研究室_知識索引.md` をこのファイルで丸ごと上書き置換しないでください。Notebook 側では既存内容を維持したまま差分追記（または別ソースとして参照）してください。
> - **GitHub への保存成功は、Gemini Notebook への同期完了を意味しません** (`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`)。

- 対象リポジトリ: `kamiyusense/ai-video-research` (private)
- 補助知識庫 (Gemini Notebook): https://notebooklm.google.com/notebook/ai-video-research-part2-past14-20261017
- GitHub側エクスポート更新日: 2026-10-17
- リモートブランチ照合鮮度: `FRESH_FETCHED`
- Notebook側への逆同期状態: `NOT_SYNCED_FROM_GITHUB`

## 1. GitHub全ブランチ横断・既知の動画ID台帳（重複登録禁止リスト）

`registry.json` だけでなく、`research/*.md` および `notes/*.md` のファイル名・本文から検出された動画IDを含みます。

| video_id | 状態 | 検出元 (現在ブランチ / 並行PRブランチ) | 参照パス |
|---|---|---|---|
| `2-8cXaRHlqI` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-2-8cXaRHlqI-gemini-notebook.md` |
| `26MGuVIJh4A` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-26MGuVIJh4A-gemini-notebook.md` |
| `3bLrrkA1nlQ` | PRELIMINARY_RESEARCH_RECORDED; ORIGINAL_VIDEO_UNKNOWN; LIVE_NOT_RUN | origin/research/cognitive-drift-series-20261010, origin/research/video08-notebooklm-youtube-extension-20261010 (registry.json) | `research/2026-10-10-3bLrrkA1nlQ-html-plan-preliminary.md` |
| `BStkW1HTfmk` | VIDEO_CONTENT_PENDING; OFFICIAL_ONLY_RESEARCH; OBSIDIAN_INSTALL_NOT_RUN | current_branch (registry.json) | `research/2026-10-10-BStkW1HTfmk-obsidian-preliminary.md` |
| `BvbkOQWgAw8` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-BvbkOQWgAw8-gemini-notebook.md` |
| `D0B-l7A69nI` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-D0B-l7A69nI-gemini-notebook.md` |
| `Eh75KT85Y40` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-Eh75KT85Y40-gemini-notebook.md` |
| `GVB8VfuNeJQ` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-GVB8VfuNeJQ-gemini-notebook.md` |
| `JMoByqOlftc` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-JMoByqOlftc-gemini-notebook.md` |
| `JXmk7hmbS3c` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-JXmk7hmbS3c-gemini-notebook.md` |
| `MVVpR2Bb0Rk` | REMOTE_MARKDOWN_REFERENCE | origin/research/cognitive-drift-series-20261010, origin/research/video08-notebooklm-youtube-extension-20261010 (body:notes/cognitive-drift-video-series-20261010.md) | `notes/cognitive-drift-video-series-20261010.md` |
| `Mg0pYFVAuWQ` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-Mg0pYFVAuWQ-gemini-notebook.md` |
| `MnzEE0fLxBs` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-MnzEE0fLxBs-gemini-notebook.md` |
| `NCQZiT0e59g` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-NCQZiT0e59g-gemini-notebook.md` |
| `RZLAP2CLUM8` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-RZLAP2CLUM8-gemini-notebook.md` |
| `Vr3JkAT9mo8` | RESEARCH_RECORDED; STATIC_SPECIALIST_IMPLEMENTED; LIVE_NOT_RUN | current_branch (registry.json) | `research/2026-10-10-Vr3JkAT9mo8-work-specialists.md` |
| `W35UQZL2w7E` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-W35UQZL2w7E-gemini-notebook.md` |
| `X9Zk68AII4A` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-X9Zk68AII4A-gemini-notebook.md` |
| `XckM9eFa_vg` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-XckM9eFa_vg-gemini-notebook.md` |
| `YrTVpJ1ebUk` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-YrTVpJ1ebUk-gemini-notebook.md` |
| `ZY7YuYHLlIQ` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-ZY7YuYHLlIQ-gemini-notebook.md` |
| `ZgMrRA1Czlc` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-ZgMrRA1Czlc-gemini-notebook.md` |
| `ZjUJ-35acaU` | REVIEWED_PARTIAL; OFFICIAL_CROSSCHECK; VIDEO_VISUAL_UNKNOWN; EXTENSION_NOT_TESTED | current_branch (registry.json) | `research/2026-10-10-ZjUJ-35acaU-notebooklm-youtube-extension.md` |
| `cneFa24EFEk` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-cneFa24EFEk-gemini-notebook.md` |
| `gD6UZ4wG8OM` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-gD6UZ4wG8OM-gemini-notebook.md` |
| `j3Cyvbfn9_k` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-j3Cyvbfn9_k-gemini-notebook.md` |
| `lC5jxpYmatE` | RESEARCH_RECORDED; LIVE_NOT_RUN | current_branch (registry.json) | `research/2026-10-10-lC5jxpYmatE-ai-techniques.md` |
| `sodTFSuV4zY` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-sodTFSuV4zY-gemini-notebook.md` |
| `t22FELAl-BM` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-t22FELAl-BM-gemini-notebook.md` |
| `y2xCGyURl7Q` | GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE | current_branch (registry.json) | `research/2026-10-17-y2xCGyURl7Q-gemini-notebook.md` |

## 2. 優先研究テーマ・次回調査キュー (`next_topics`)

1. R001/R002: 自律研究Loopの完了条件・停止条件と、重複イベントや結果不明書込みの安全な復旧パターン
2. R004/R005: ハーネス・MCP・プラグイン・公式コネクタの権限境界とモデル非依存の状態管理
3. P006連携: 新しいAI機能・ツール発表時に「過去の未解決課題」と自動照合して再挑戦を提案する仕組み

## 3. 未確認・要検証事項 (`unknowns`)

- cneFa24EFEk (No.02): Addness社内Webhookエンドポイントの厳密な仕様。
- t22FELAl-BM (No.03): OpenAIのエンタープライズ向け拡張キャッシュ保持期間の正確な上限値。
- X9Zk68AII4A (No.04): hillclimb内部アルゴリズムにおける収束判定の完全な自動閾値パラメータ。
- ZgMrRA1Czlc (No.05): 無許可送金が発生した内部モデルの完全な推論パラメータとシステムプロンプト全文。
- gD6UZ4wG8OM (No.06): Felix氏の社内実験における未公開プロンプト例の完全な原文。
- W35UQZL2w7E (No.07): OpenAIの将来的なトークナイザー圧縮比率改定スケジュール。
- JXmk7hmbS3c (No.08): KEITO氏が内部運用している非公開Discord Botのソースコード全文。
- Eh75KT85Y40 (No.09): 公式LINEで配布されるテンプレート内部プロンプト全文。
- 26MGuVIJh4A (No.10): AI仙人氏が社内実務で使用している8ターミナル並列管理ツールの構成詳細。
- XckM9eFa_vg (No.11): 概要欄配布スターターキットZIPの1文字単位の原文。
- NCQZiT0e59g (No.12): 自作iPhone録音アプリおよび自己改善ループの内部ソースコード全文。
- y2xCGyURl7Q (No.13): Argonの思考プロセストークンに対する厳密な内部課金レート。
- RZLAP2CLUM8 (No.14): 投稿者が実務で使用しているObsidian専用テンプレートプラグイン名。
- 2-8cXaRHlqI (No.15): 言及された非公式NotebookLM CLIの正確なGitHubリポジトリURL。
- YrTVpJ1ebUk (No.16): dotsの日本リージョン向け専用クラウドPCの提供開始日。
- j3Cyvbfn9_k (No.17): 検証で動かなかったGemini 3.1 ProのWebGL互換性バグの詳細原因。
- JMoByqOlftc (No.18): サボり男。氏が使用している自作プロンプト管理スプレッドシートの全項目。
- MnzEE0fLxBs (No.19): ここな氏が実務で使用している社内規定ソースのファイル名。
- D0B-l7A69nI (No.20): 動画内で言及された専用要約Webサイトの現在の運営状況。
- Mg0pYFVAuWQ (No.21): 音声会話時の内部コンピュート消費レートの正確な係数。
- GVB8VfuNeJQ (No.22): みずたろう氏が提示した契約書サンプルの実在企業名。
- BvbkOQWgAw8 (No.23): MIT学生が使用した元論文の完全な書誌情報。
- ZY7YuYHLlIQ (No.24): KEITO氏が使用したSparkスキル用YAMLメタプロンプトの全文公開リンク。
- ZjUJ-35acaU (No.25): 拡張機能作者の今後のアップデート予定と保守方針。
- BStkW1HTfmk (No.26): Leo氏が実験で使用したGoogleドライブMCPサーバーの実装コード全文。

## 4. 未解決課題ストック（P006 再評価対象）

新技術・新機能を発見した際は、以下の未解決課題を解決できる一次資料の根拠があるか照合すること：

- **P006-U01**: Google AI Studioの長尺YouTube動画入力でのブラウザUIフリーズ回避・映像フレーム直接検証の省力化 (状態: `OPEN`, 参照: `proposals/006-unresolved-task-backlog-revisit.md`)
- **P006-U02**: Gemini Notebookと非公開GitHub間の手動コピーを最小化する安全な公式連携・差分同期 (状態: `IN_PROGRESS`, 参照: `automation/gemini-notebook/README.md`)
- **P006-U03**: 反復的な画面操作（Computer Use）から公式API・決定的スクリプトへの安全な移行判断 (状態: `OPEN`, 参照: `research/2026-10-10-lC5jxpYmatE-ai-techniques.md`)
