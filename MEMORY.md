# 📺 AI技術研究室｜共有記憶インデックス v1
更新基準: 2026-10-10 / 保存先: private GitHub `kamiyusense/ai-video-research`

**重要**: このファイルはChatGPT製品のネイティブMemory機能ではなく、人間またはAIが明示的に参照する**Markdownの索引**。保存しただけで全チャット／他AIに自動共有・自動同期はされない。

## 共通の目的
YouTube・公式資料・研究成果から価値あるAI技術を学び、ユーザーの理解・判断・作業改善に利用する。長期的には人間の手間を減らす安全な研究Loopへ段階的に進む。開発・副業・日常の関心に応じて研究対象を選び、全てをAI開発へ無理に結び付けない。

## 現在の担当制（静的に準備済み、実機受渡しは未試験）
- 受付・司令塔：`agents/coordinator/`
- 映像：`agents/visual/`（Google AI Studioを想定、実行はユーザー）
- 独立調査：`agents/research/`（Gemini Sparkを想定、実行はユーザー）
- 検品：`agents/reviewer/`（ChatGPT）
- 記録：`agents/archivist/`（ChatGPT/Work候補、実機試験は未実施）

詳しい責務は [担当一覧](agents/README.md) と [運用手順](docs/SPECIALIST_WORKFLOW.md)。担当別の状態は `agents/<role>/MEMORY.md` を確認する。

## 研究の正本と最新確認
- 研究方針：`AGENTS.md`, `RESEARCH_ROADMAP.md`
- 既存記録の重複照合：`registry.json`
- 研究ノート：`research/`、技術ノート：`notes/`、改善候補：`proposals/`
- 受渡し形式：`templates/handoff-envelope.md`
- 動画06の資料：`research/2026-10-10-Vr3JkAT9mo8-work-specialists.md`
- 参考にする先行研究：動画05は`research/2026-10-10-lC5jxpYmatE-ai-techniques.md`
- **GitHubのmainではなく未MergeのDraft PR群に保存中。** 最新head・PR番号・統合状況は毎回fresh readbackする。過去のSHAを正本にしない。
- 改善候補P005（新規計画時の目的→障害→次タスク）は別PRのため、未統合である可能性がある。

## 本番投入前の未解決
- 新しい担当がGitHub記録を確実に読めるか、外部AIで入力指示が守られるか：UNKNOWN
- Google AI Studioの長尺入力のフリーズ原因：UNKNOWN。字幕解析と必要区間の映像分析に分けて扱う。
- Workによる外部AIサイトの実操作・結果回収：NOT_TESTED。
- 他担当を司令塔から自動起動：NOT_WIRED。
- データ自動同期、定期巡回、スケジュール：NOT_CONFIGURED。

## 安全境界
研究室以外のGitHub repoは変更しない。課金、外部AIへの自動送信/起動、APIキー、権限変更、LIVE運用、Merge、default branch直書きは別承認。外部の字幕全文・動画本体・個人情報・秘密情報は保存しない。
