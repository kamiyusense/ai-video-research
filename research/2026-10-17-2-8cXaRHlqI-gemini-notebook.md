# 【天才AI化】ClaudeのフルMAXパワーを出すAI神連携はNotebookLMとObsidianを使うんやで。【Gemini Notebook】

- record_id: `youtube:2-8cXaRHlqI`
- video_id: `2-8cXaRHlqI`
- canonical_url: https://www.youtube.com/watch?v=2-8cXaRHlqI
- original_url: https://www.youtube.com/watch?v=2-8cXaRHlqI
- publication_date: 2026-06-21
- checked_at: 2026-10-17
- source_scope: GEMINI_PAST_RESEARCH_NOTE_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:AI技術研究室_過去調査14本_完全総合辞書_20261017
- Gemini Notebook source: AI技術研究室_過去調査14本_完全総合辞書_20261017
- Gemini readback (self-reported): PASS
- GitHub independent verification: NOT_RUN
- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB
- changes: NEW

## 独自要約
Claude Code単体での調査によるコンテキスト圧迫と利用枠枯渇（月12日問題）、およびCLAUDE.md肥大化によるトークン消費を防ぐため、NotebookLM（調査・Studio 9種生成）とObsidian（テーマ別Markdown保管・内部リンク・グラフビュー）を繋ぐ手法を解説。非公式OSS「NotebookLM CLI」やClaude Desktop用.mcpb拡張による連携実演と、非公式ツールの仕様変更・セキュリティ注意点を明示。

## 動画目次・確認済みタイムライン（チャプター）
- UNKNOWN | **概要・Claude Codeの「月12日問題（利用枠枯渇）」** | Gemini報告区間(00:00〜02:27 / 一次時刻未確認のため再生リンク非生成): 概要・Claude Codeの「月12日問題（利用枠枯渇）」 | time_source: UNKNOWN | topics: Claude Code, 月12日問題
- UNKNOWN | **トークン枯渇の原因（コンテキスト肥大化とサブエージェント同一枠消費）** | Gemini報告区間(02:27〜04:22 / 一次時刻未確認のため再生リンク非生成): トークン枯渇の原因（コンテキスト肥大化とサブエージェント同一枠消費） | time_source: UNKNOWN | topics: Claude Code, 月12日問題, CLAUDE.md肥大化
- UNKNOWN | **3ツールの役割分担（NotebookLM＝調査、Obsidian＝社内DB、Claude Code＝司令塔）** | Gemini報告区間(04:22〜06:52 / 一次時刻未確認のため再生リンク非生成): 3ツールの役割分担（NotebookLM＝調査、Obsidian＝社内DB、Claude Code＝司令塔） | time_source: UNKNOWN | topics: Claude Code, NotebookLM, Obsidian
- UNKNOWN | **リサーチ処理のNotebookLMオフロードによる体感トークン1/10圧縮** | Gemini報告区間(06:52〜08:18 / 一次時刻未確認のため再生リンク非生成): リサーチ処理のNotebookLMオフロードによる体感トークン1/10圧縮 | time_source: UNKNOWN | topics: NotebookLM
- UNKNOWN | **会議議事録3回分からの「担当・期限・未解決」抽出デモ** | Gemini報告区間(08:18〜10:19 / 一次時刻未確認のため再生リンク非生成): 会議議事録3回分からの「担当・期限・未解決」抽出デモ | time_source: UNKNOWN | topics: Claude Code, 月12日問題, CLAUDE.md肥大化
- UNKNOWN | **Studio機能9種生成の実演** | Gemini報告区間(10:19〜11:41 / 一次時刻未確認のため再生リンク非生成): Studio機能9種生成の実演 | time_source: UNKNOWN | topics: Claude Code, 月12日問題, CLAUDE.md肥大化
- UNKNOWN | **CLAUDE.md 単体記憶の限界とObsidianテーマ別分割（LLM Wiki）** | Gemini報告区間(11:41〜13:44 / 一次時刻未確認のため再生リンク非生成): CLAUDE.md 単体記憶の限界とObsidianテーマ別分割（LLM Wiki） | time_source: UNKNOWN | topics: Obsidian, LLM Wiki
- UNKNOWN | **Obsidian Vault構築と前月差分抽出プロンプト** | Gemini報告区間(13:44〜17:36 / 一次時刻未確認のため再生リンク非生成): Obsidian Vault構築と前月差分抽出プロンプト | time_source: UNKNOWN | topics: Obsidian
- UNKNOWN | **セットアップ2方式（NotebookLM CLI / Claude Desktop用 .mcpb）** | Gemini報告区間(17:36〜18:59 / 一次時刻未確認のため再生リンク非生成): セットアップ2方式（NotebookLM CLI / Claude Desktop用 .mcpb） | time_source: UNKNOWN | topics: NotebookLM, NotebookLM CLI, .mcpb
- UNKNOWN | **非公式OSSツール利用時のセキュリティ警告・仕様変更リスク** | Gemini報告区間(18:59〜22:18 / 一次時刻未確認のため再生リンク非生成): 非公式OSSツール利用時のセキュリティ警告・仕様変更リスク | time_source: UNKNOWN | topics: Claude Code, 月12日問題, CLAUDE.md肥大化

## 詳細技術知識・再利用ノート
- 整理番号・区分: No.15 (Part 2: 過去調査14本 (No.13〜26)) / 投稿者: 【さき】のAIでええやん。 / 調査日: 2026-10-16
- 動画長・公開日照合: Gemini記載長=22:18, 記載公開日=2026-06-21 | YouTube一次実測長=22:18 (1338s), 一次公開日=2026-06-21
- 証拠強度区分: PART2（Gemini過去研究ノート由来・一次根拠がある時刻のみリンク化）
- 全体要約（原文完全保持）: Claude Code単体での調査によるコンテキスト圧迫と利用枠枯渇（月12日問題）、およびCLAUDE.md肥大化によるトークン消費を防ぐため、NotebookLM（調査・Studio 9種生成）とObsidian（テーマ別Markdown保管・内部リンク・グラフビュー）を繋ぐ手法を解説。非公式OSS「NotebookLM CLI」やClaude Desktop用.mcpb拡張による連携実演と、非公式ツールの仕様変更・セキュリティ注意点を明示。
- 主要技術キーワード: Claude Code, 月12日問題, CLAUDE.md肥大化, NotebookLM, Obsidian, LLM Wiki, NotebookLM CLI, .mcpb, 非公式OSSリスク
- 公式仕様・一次資料照合詳細: Claude Code公式Memory仕様（CLAUDE.mdは200行未満推奨、特定知識は外部ファイルへ分離）および.mcpb公式規格と一致。非公式NotebookLM CLIのセキュリティリスク指摘も公式MCP指針と一致。
- 制約・注意点: 「体感1/10」は投稿者の主観値。Studioスライドは画像出力でありPowerPoint文字編集不可。
- 今後の応用・自動化案: リサーチ処理をNotebookLMへ逃がすことでClaude Codeのコンテキスト窓と利用枠を温存する設計。
- 未確認事項（UNKNOWN）: 言及された非公式NotebookLM CLIの正確なGitHubリポジトリURL。

## 主張・一次資料・時刻
- [PART2研究ノート経由の公式照合] Claude Code公式Memory仕様（CLAUDE.mdは200行未満推奨、特定知識は外部ファイルへ分離）および.mcpb公式規格と一致。非公式NotebookLM CLIのセキュリティリスク指摘も公式MCP指針と一致。 | CONFIRMED_DOC | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 制約・注意点: 「体感1/10」は投稿者の主観値。Studioスライドは画像出力でありPowerPoint文字編集不可。 / 今後の応用: リサーチ処理をNotebookLMへ逃がすことでClaude Codeのコンテキスト窓と利用枠を温存する設計。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 未確認事項(UNKNOWN): 言及された非公式NotebookLM CLIの正確なGitHubリポジトリURL。 | UNKNOWN | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

## 関連する既存研究・課題との接続
- `youtube:BStkW1HTfmk` (COMPLEMENTS): CLAUDE.md肥大化と月12日問題を防ぐObsidianテーマ別分割(LLM Wiki)およびNotebookLM調査オフロード

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。
