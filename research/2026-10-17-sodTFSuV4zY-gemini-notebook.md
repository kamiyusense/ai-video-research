# デスクツアーならぬソフトウェアツアー！AIエンジニアが仕事で使ってるアプリ・サービスを一式紹介

- record_id: `youtube:sodTFSuV4zY`
- video_id: `sodTFSuV4zY`
- canonical_url: https://www.youtube.com/watch?v=sodTFSuV4zY
- original_url: https://www.youtube.com/watch?v=sodTFSuV4zY
- publication_date: 2026-10-14
- checked_at: 2026-10-17
- source_scope: YOUTUBE_TRANSCRIPT_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:AI技術研究室_直近調査12本_完全総合辞書_20261017
- Gemini Notebook source: AI技術研究室_直近調査12本_完全総合辞書_20261017
- Gemini readback (self-reported): PASS
- GitHub independent verification: NOT_RUN
- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB
- changes: NEW

## 独自要約
現役AIエンジニアがメイン機（MacBook Pro）と常時稼働サブ機（Mac mini）＋スマホをTailscale（VPN）とエージェント統合開発環境「Orca」で繋ぎ、Claude Code（MAX 20x×2契約）を主軸、OpenAI Codexをサブエージェント（画像生成・第三者コードレビュー）として並列運用する実務環境を公開。Playwright（MCP/CLI・WebMCP）、1Password Environments MCPによる秘密鍵の非露出管理、Dockerコンテナ隔離、Karabiner-Elements設定のAI自動生成など、

## 動画目次・確認済みタイムライン（チャプター）
- UNKNOWN | **オープニング・開発環境の全体像** | Gemini報告区間(00:00〜00:54 / 一次時刻未確認のため再生リンク非生成): オープニング・開発環境の全体像 | time_source: UNKNOWN | topics: Claude Code, claude -p, Codex
- UNKNOWN | **ハードウェア構成とTailscaleによるリモート開発** | Gemini報告区間(00:54〜03:12 / 一次時刻未確認のため再生リンク非生成): ハードウェア構成とTailscaleによるリモート開発 | time_source: UNKNOWN | topics: Tailscale
- UNKNOWN | **Orca（統合AI開発環境）とGit worktree並列開発** | Gemini報告区間(03:12〜07:45 / 一次時刻未確認のため再生リンク非生成): Orca（統合AI開発環境）とGit worktree並列開発 | time_source: UNKNOWN | topics: Orca, Git worktree
- UNKNOWN | **1Password Environments MCPによる機密情報非露出管理** | Gemini報告区間(07:45〜11:20 / 一次時刻未確認のため再生リンク非生成): 1Password Environments MCPによる機密情報非露出管理 | time_source: UNKNOWN | topics: 1Password Environments MCP
- UNKNOWN | **Playwright CLI & WebMCP によるWebブラウザ自動操作** | Gemini報告区間(11:20〜14:50 / 一次時刻未確認のため再生リンク非生成): Playwright CLI & WebMCP によるWebブラウザ自動操作 | time_source: UNKNOWN | topics: Playwright CLI, WebMCP
- UNKNOWN | **PhotoCraft / OpenCut によるメディア生成ワークフロー** | Gemini報告区間(14:50〜17:30 / 一次時刻未確認のため再生リンク非生成): PhotoCraft / OpenCut によるメディア生成ワークフロー | time_source: UNKNOWN | topics: PhotoCraft, OpenCut
- UNKNOWN | **Karabiner-Elements & ThumbSenseのキーバインド最適化** | Gemini報告区間(17:30〜20:15 / 一次時刻未確認のため再生リンク非生成): Karabiner-Elements & ThumbSenseのキーバインド最適化 | time_source: UNKNOWN | topics: Karabiner-Elements, ThumbSense
- UNKNOWN | **まとめ・今後のエージェントハーネス展望** | Gemini報告区間(20:15〜23:01 / 一次時刻未確認のため再生リンク非生成): まとめ・今後のエージェントハーネス展望 | time_source: UNKNOWN | topics: Claude Code, claude -p, Codex

## 詳細技術知識・再利用ノート
- 整理番号・区分: No.01 (Part 1: 直近調査12本 (No.01〜12)) / 投稿者: クロノITチャンネル / 調査日: 2026-10-16
- 動画長・公開日照合: Gemini記載長=23:01, 記載公開日=2026-10-14 | YouTube一次実測長=23:01 (1381s), 一次公開日=2026-10-14
- 証拠強度区分: PART1（Notebook内のYouTubeソース由来）
- 全体要約（原文完全保持）: 現役AIエンジニアがメイン機（MacBook Pro）と常時稼働サブ機（Mac mini）＋スマホをTailscale（VPN）とエージェント統合開発環境「Orca」で繋ぎ、Claude Code（MAX 20x×2契約）を主軸、OpenAI Codexをサブエージェント（画像生成・第三者コードレビュー）として並列運用する実務環境を公開。Playwright（MCP/CLI・WebMCP）、1Password Environments MCPによる秘密鍵の非露出管理、Dockerコンテナ隔離、Karabiner-Elements設定のAI自動生成など、AIに安全かつ高速に手足と環境を与えるベストプラクティスを提示。
- 主要技術キーワード: Claude Code, claude -p, Codex, Orca, Git worktree, Tailscale, 1Password Environments MCP, Playwright CLI, WebMCP, Dockerコンテナ隔離, PhotoCraft, OpenCut, Karabiner-Elements, ThumbSense
- 公式仕様・一次資料照合詳細: Playwright公式（Coding agentsガイド）、1Password公式（Environments Claude Codeプラグイン）、Orca公式GitHub（stablyai/orca）、PhotoCraft公式GitHub（storytold/photocraft）、Claude Code公式CLIリファレンス（claude -p）と完全一致。
- 制約・注意点: Aqua Voiceでの固有名詞認識精度、Mac mini単独でのローカルLLM同時稼働に限界あり。
- 今後の応用・自動化案: TailscaleとOrcaによる常時稼働Mac miniへのエージェント並列ディスパッチと1Password MCP安全連携。
- 未確認事項（UNKNOWN）: 投稿者自作の業務集約Webアプリの内部コード、月100ドルのChatGPT契約詳細。
- YouTube概要欄の公式チャプター（一次照合参照用）: 0:00 ソフトウェアツアー / 1:04 言語とフレームワーク / 1:57 AI / 5:29 エディタとターミナル / 9:15 開発とインフラ / 13:10 制作 / 15:16 業務 / 16:56 Macの環境 / 21:44 まとめ

## 主張・一次資料・時刻
- [PART1直近調査の公式照合] Playwright公式（Coding agentsガイド）、1Password公式（Environments Claude Codeプラグイン）、Orca公式GitHub（stablyai/orca）、PhotoCraft公式GitHub（storytold/photocraft）、Claude Code公式CLIリファレンス（claude -p）と完全一致。 | CONFIRMED_DOC | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 制約・注意点: Aqua Voiceでの固有名詞認識精度、Mac mini単独でのローカルLLM同時稼働に限界あり。 / 今後の応用: TailscaleとOrcaによる常時稼働Mac miniへのエージェント並列ディスパッチと1Password MCP安全連携。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 未確認事項(UNKNOWN): 投稿者自作の業務集約Webアプリの内部コード、月100ドルのChatGPT契約詳細。 | UNKNOWN | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

## 関連する既存研究・課題との接続
- `youtube:lC5jxpYmatE` (COMPLEMENTS): Claude Code・Codex並列環境におけるPlaywright CLI/WebMCPと1Password MCP秘密鍵隔離の実務構成を補完

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。
