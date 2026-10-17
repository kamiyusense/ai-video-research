# 【実演】Claude CodeでAI副業を完全自動化する方法。年商30億社長が全部見せます

- record_id: `youtube:cneFa24EFEk`
- video_id: `cneFa24EFEk`
- canonical_url: https://www.youtube.com/watch?v=cneFa24EFEk
- original_url: https://www.youtube.com/watch?v=cneFa24EFEk
- publication_date: 2026-10-15
- checked_at: 2026-10-17
- source_scope: YOUTUBE_TRANSCRIPT_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:AI技術研究室_直近調査12本_完全総合辞書_20261017
- Gemini Notebook source: AI技術研究室_直近調査12本_完全総合辞書_20261017
- Gemini readback (self-reported): PASS
- GitHub independent verification: NOT_RUN
- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB
- changes: NEW

## 独自要約
Claude Codeを用いたAI副業・業務自動化の実演。非エンジニアでもCLI（ターミナル）から自然言語のみでWebアプリ構築、スクレイピング、SNS運用ツール作成、および自社プラットフォーム（Addness）とのWebhook連携を行う手順を解説。人間の役割は『何を作るかの要件定義とディレクション』に特化し、実装・デバッグ・リファクタリングをすべてClaude Codeに委譲するワークフローを提示。

## 動画目次・確認済みタイムライン（チャプター）
- UNKNOWN | **概要・AI副業の常識変化とCLIの優位性** | Gemini報告区間(00:00〜02:15 / 一次時刻未確認のため再生リンク非生成): 概要・AI副業の常識変化とCLIの優位性 | time_source: UNKNOWN | topics: Claude Code, CLI自動化, Addness連携
- UNKNOWN | **環境構築：Node.js導入とClaude Code認証** | Gemini報告区間(02:15〜06:40 / 一次時刻未確認のため再生リンク非生成): 環境構築：Node.js導入とClaude Code認証 | time_source: UNKNOWN | topics: Claude Code
- UNKNOWN | **実演①：競合リサーチ自動化ツールの爆速作成** | Gemini報告区間(06:40〜12:10 / 一次時刻未確認のため再生リンク非生成): 実演①：競合リサーチ自動化ツールの爆速作成 | time_source: UNKNOWN | topics: Claude Code, CLI自動化, Addness連携
- UNKNOWN | **実演②：LP分析と改善提案レポートの自動生成** | Gemini報告区間(12:10〜17:55 / 一次時刻未確認のため再生リンク非生成): 実演②：LP分析と改善提案レポートの自動生成 | time_source: UNKNOWN | topics: Claude Code, CLI自動化, Addness連携
- UNKNOWN | **実演③：Addness Webhookと連携した顧客フォロー自動化** | Gemini報告区間(17:55〜22:30 / 一次時刻未確認のため再生リンク非生成): 実演③：Addness Webhookと連携した顧客フォロー自動化 | time_source: UNKNOWN | topics: Webhook
- UNKNOWN | **トークン消費管理と5時間制限の回避策** | Gemini報告区間(22:30〜25:10 / 一次時刻未確認のため再生リンク非生成): トークン消費管理と5時間制限の回避策 | time_source: UNKNOWN | topics: Claude Code, CLI自動化, Addness連携
- UNKNOWN | **まとめ・AIディレクターへの転換戦略** | Gemini報告区間(25:10〜27:18 / 一次時刻未確認のため再生リンク非生成): まとめ・AIディレクターへの転換戦略 | time_source: UNKNOWN | topics: Claude Code, CLI自動化, Addness連携

## 詳細技術知識・再利用ノート
- 整理番号・区分: No.02 (Part 1: 直近調査12本 (No.01〜12)) / 投稿者: みかみ【東大退学させられた男】 / 調査日: 2026-10-16
- 動画長・公開日照合: Gemini記載長=27:18, 記載公開日=2026-10-15 | YouTube一次実測長=27:53 (1673s), 一次公開日=2026-05-08
- 証拠強度区分: PART1（Notebook内のYouTubeソース由来）
- 全体要約（原文完全保持）: Claude Codeを用いたAI副業・業務自動化の実演。非エンジニアでもCLI（ターミナル）から自然言語のみでWebアプリ構築、スクレイピング、SNS運用ツール作成、および自社プラットフォーム（Addness）とのWebhook連携を行う手順を解説。人間の役割は『何を作るかの要件定義とディレクション』に特化し、実装・デバッグ・リファクタリングをすべてClaude Codeに委譲するワークフローを提示。
- 主要技術キーワード: Claude Code, CLI自動化, Addness連携, Webhook, 自律デバッグ, Playwright, 要件定義ディレクション
- 公式仕様・一次資料照合詳細: Claude Code公式CLIリファレンスおよびNode.js環境要件と一致。
- 制約・注意点: 外部SaaS連携時のAPIキー管理とレートリミットに留意が必要。
- 今後の応用・自動化案: Addnessや外部CRMと接続した顧客フォローおよび競合調査レポートの自動作成パイプライン。
- 未確認事項（UNKNOWN）: Addness社内Webhookエンドポイントの厳密な仕様。

## 主張・一次資料・時刻
- [PART1直近調査の公式照合] Claude Code公式CLIリファレンスおよびNode.js環境要件と一致。 | CONFIRMED_DOC | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 制約・注意点: 外部SaaS連携時のAPIキー管理とレートリミットに留意が必要。 / 今後の応用: Addnessや外部CRMと接続した顧客フォローおよび競合調査レポートの自動作成パイプライン。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 未確認事項(UNKNOWN): Addness社内Webhookエンドポイントの厳密な仕様。 | UNKNOWN | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。
