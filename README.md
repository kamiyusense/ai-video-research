# 📺 AI技術研究室

AI関連全般を学び、知識と検証結果を蓄積し、最終的に安全なAI自動化へつなげる研究室。

YouTube、公式資料、論文、公開実装、更新情報を対象にする。Claude×Julesは応用例の一つ。Loop、Skill、プラグイン、各社の新しいAI、ハーネス、評価と復旧、統合自動化まで扱う。

研究の順序と未調査事項は RESEARCH_ROADMAP.md に記録する。

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

## YouTubeから学ぶ方法の調査
- [Chatへの調査引き継ぎ](prompts/chat-youtube-research.md)
- [2026-10-10 Work側の独立調査](research/2026-10-10-youtube-learning-methods.md)
- [動画取得と学習記録の実証計画](proposals/003-youtube-learning-loop.md)

公式資料の確認と実際の動画処理は区別する。本調査では動画URL未提示のため実証はNOT_RUN。
