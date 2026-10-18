# 📺 AI技術研究室

> **【最新の引継ぎ入口・必読（2026-10-19）】** 新チャットで「GitHub見て引き継いで」と言われた場合は、GitHub current stateを確認し、必ず **[docs/HANDOVER_CURRENT.md](docs/HANDOVER_CURRENT.md) → [docs/OKF_KNOWLEDGE_ROADMAP.md](docs/OKF_KNOWLEDGE_ROADMAP.md)** を全文読む。続いて [RESEARCH_ROADMAP.md](RESEARCH_ROADMAP.md)、[AGENTS.md](AGENTS.md) も確認。最新方針は「原字幕のNotebook内独立保存（許可範囲・完全性の確認）＋OKF研究ノート＋関連研究リンク＋根拠付きQA」。古い逐次動画リレーやGitHub→Notebook逆同期の記述を優先しない。静的・LIVE・UNKNOWNを区別する。


AI関連全般を学び、知識と検証結果を蓄積し、最終的に安全なAI自動化へつなげる研究室。

YouTube、公式資料、論文、公開実装、更新情報を対象にする。Claude×Julesは応用例の一つ。Loop、Skill、プラグイン、各社の新しいAI、ハーネス、評価と復旧、統合自動化まで扱う。

研究の順序と未調査事項は RESEARCH_ROADMAP.md に記録する。

## 🟢 担当制｜まずここから（STATIC実装済・外部AI手動受渡し）

- [担当制の運用手順](docs/SPECIALIST_WORKFLOW.md)：動画URL受付 → 独立映像/字幕調査 → 検品 → 知識記録
- [5担当の一覧・仕事の引き渡し](agents/README.md)（coordinator / visual / research / reviewer / archivist）
- [共通記憶の目次](MEMORY.md)（自動同期ではなく、必要時に明示して読む）
- [映像担当へのコピープロンプト](prompts/specialist-visual.md)
- [字幕・独立調査担当へのコピープロンプト](prompts/specialist-research.md)
- [新チャット/Workへの担当引継ぎプロンプト](prompts/specialist-resume.md)
- [静的mock仕様](tests/SPECIALIST_HANDOFF_MOCK.md)
- [動画06の研究記録](research/2026-10-10-Vr3JkAT9mo8-work-specialists.md) ／ [段階導入案P007](proposals/007-video-research-specialist-rollout.md)

**使い方**: URLと調査目的をcoordinatorに渡す → 必要なら2つのコピープロンプトを人間が外部AIへ貼る → AIの短い報告をreviewerへ → 保存する場合だけarchivistへ。GitHubの資料を保存しただけではChatGPTプロジェクト、AI Studio、Sparkへ自動読込されない。外部モデル実行/WorkのLIVE/自動タスクは未接続。

## 対象
- ChatGPTプロジェクト名: 📺 AI技術研究室
- GitHub: kamiyusense/ai-video-research（非公開）
- kamiyusense/multi-ai-council-phase0 は変更しない。
- 本資料は確認用の非default branchに保存する初期資料。GitHubの実作成・確認状況とChatGPT側の未完了事項は SETUP_STATUS.md を確認する。

## 保存するもの
動画URL、動画ID、出典時刻、独自要約、公式資料URL、確認日・対象バージョン、主張別の確認結果、再現条件、改善提案。

動画本体、字幕全文、長い引用、秘密情報、APIキー、Cookie、個人情報、社内資料を保存しない。

## 使い方
1. OPERATIONS.md に従い、動画IDで registry.json の重複を確認する。
2. templates/research-record.md を複製し、動画を確認できた範囲だけ記録する。
3. 公式資料と照合する。文書の記述と実機での再現は別々に記録する。
4. notes/ に確認済みの技術知識、proposals/ に実行前の改善提案を残す。
5. 初期化後のGitHub書き込みは非default branchとレビュー用PRで行い、readbackする。Mergeしない。

## 資料
- CHATGPT_PROJECT_INSTRUCTIONS.md: ChatGPTのプロジェクト指示
- AGENTS.md / CLAUDE.md: 作業対象と承認境界
- templates/research-record.md: 動画研究のテンプレート
- templates/technical-note.md: 技術ノートのテンプレート
- templates/automation-proposal.md: 自動化・改善提案のテンプレート
- notes/verified-tooling.md: 公式資料を確認した初期技術ノート
- proposals/001-evidence-first.md: 各AI・ツール向け改善提案
- RESEARCH_ROADMAP.md: AI全般から自動化へ進む研究計画
- proposals/002-automation-learning-loop.md: 研究成果を自動化設計につなぐ改善提案
- OPERATIONS.md: 初期運用・重複・復旧手順
- registry.json: 動画IDの台帳
- evidence/: 保存内容のreadback証拠
- PROJECT_SOURCE.md: ChatGPTへ1ファイルで追加する初期資料

課金につながる操作、LIVE起動、Merge、権限変更を自動実行しない。文書に禁止事項を書いても、サービス側の権限制御が設定されたことにはならない。

## 動画研究05｜再利用候補（2026-10-10）
- [AI仙人の「課題ドリブン・Skill・Computer Use」独自研究記録](research/2026-10-10-lC5jxpYmatE-ai-techniques.md)（出典動画ID: lC5jxpYmatE。字幕報告＋AI Studio選択4区間の映像報告。ChatGPTの独立全編視聴なし）
- [P006 未解決課題を保管して、新機能で解決できるか提案する](proposals/006-unresolved-task-backlog-revisit.md)（**未採用**。未来の研究で再評価する候補であり、巡回・通知・既存Loop改修は未設定）

## YouTubeから学ぶ方法の調査
- [Chatへの調査引き継ぎ](prompts/chat-youtube-research.md)
- [2026-10-10 Work側の独立調査](research/2026-10-10-youtube-learning-methods.md)
- [動画取得と学習記録の実証計画](proposals/003-youtube-learning-loop.md)

公式資料の確認と実際の動画処理は区別する。本調査では動画URL未提示のため実証はNOT_RUN。

## 契約全体からの再調査（現在の推奨）
- [ChatGPT Plus / Google AI Proの全体棚卸しと最適構成](research/2026-10-10-subscription-wide-youtube-learning.md)
- [拡張した技能・Loop案](proposals/004-subscription-wide-learning-loop.md)
- [最新のChat調査用プロンプト](prompts/chat-youtube-research.md)
- [47一次資料・機能の矛盾・装備の実在確認](evidence/subscription-wide-research-docs-20261010.json)

資料からの最適候補はAI Studio Playgroundの動画入力、公式一次資料の検証、Work/Codexの技能化・記録の組み合わせ。実測の最適解は未確定。原動画／字幕全文は保存せず、Notebookへは独自ノートだけを入れる。URL投入から自動保存までの連携はNOT_RUN。
