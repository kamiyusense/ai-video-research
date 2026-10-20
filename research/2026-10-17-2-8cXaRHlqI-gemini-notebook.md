# 【天才AI化】ClaudeのフルMAXパワーを出すAI神連携はNotebookLMとObsidianを使うんやで。【Gemini Notebook】

- record_id: `youtube:2-8cXaRHlqI`
- video_id: `2-8cXaRHlqI`
- canonical_url: https://www.youtube.com/watch?v=2-8cXaRHlqI
- original_url: https://www.youtube.com/watch?v=2-8cXaRHlqI
- publication_date: 2026-06-21 (YouTube一次確認一致)
- checked_at: 2026-10-17
- source_scope: GEMINI_PAST_RESEARCH_NOTE_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:AI技術研究室_過去調査14本_完全総合辞書_20261017
- Gemini Notebook source: AI技術研究室_過去調査14本_完全総合辞書_20261017
- Gemini readback (self-reported): UNKNOWN
- GitHub independent verification: NOT_RUN
- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB
- changes: NEW

## 独自要約
Claude Code単体での調査によるコンテキスト圧迫と利用枠枯渇（月12日問題）、およびCLAUDE.md肥大化によるトークン消費を防ぐため、NotebookLM（調査・Studio 9種生成）とObsidian（テーマ別Markdown保管・内部リンク・グラフビュー）を繋ぐ手法を解説。非公式OSS「NotebookLM CLI」やClaude Desktop用.mcpb拡張による連携実演と、非公式ツールの仕様変更・セキュリティ注意点を明示。

## 動画目次・確認済みタイムライン（チャプター）
- [00:00〜02:27](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=0s) | **概要・Claude Codeの「月12日問題（利用枠枯渇）」** | 区間 00:00〜02:27 の解説: 概要・Claude Codeの「月12日問題（利用枠枯渇）」 | time_source: TIMESTAMPED_CAPTIONS | topics: Claude Code, 月12日問題
- [02:27〜04:22](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=147s) | **トークン枯渇の原因（コンテキスト肥大化とサブエージェント同一枠消費）** | 区間 02:27〜04:22 の解説: トークン枯渇の原因（コンテキスト肥大化とサブエージェント同一枠消費） | time_source: TIMESTAMPED_CAPTIONS | topics: Claude Code, 月12日問題, CLAUDE.md肥大化
- [04:22〜06:52](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=262s) | **3ツールの役割分担（NotebookLM＝調査、Obsidian＝社内DB、Claude Code＝司令塔）** | 区間 04:22〜06:52 の解説: 3ツールの役割分担（NotebookLM＝調査、Obsidian＝社内DB、Claude Code＝司令塔） | time_source: TIMESTAMPED_CAPTIONS | topics: Claude Code, NotebookLM, Obsidian
- [06:52〜08:18](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=412s) | **リサーチ処理のNotebookLMオフロードによる体感トークン1/10圧縮** | 区間 06:52〜08:18 の解説: リサーチ処理のNotebookLMオフロードによる体感トークン1/10圧縮 | time_source: TIMESTAMPED_CAPTIONS | topics: NotebookLM
- [08:18〜10:19](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=498s) | **会議議事録3回分からの「担当・期限・未解決」抽出デモ** | 区間 08:18〜10:19 の解説: 会議議事録3回分からの「担当・期限・未解決」抽出デモ | time_source: TIMESTAMPED_CAPTIONS | topics: Claude Code, 月12日問題, CLAUDE.md肥大化
- 10:19〜11:41 | **Studio機能9種生成の実演** | 区間 10:19〜11:41 の解説: Studio機能9種生成の実演 | time_source: UNKNOWN | topics: Claude Code, 月12日問題, CLAUDE.md肥大化
- [11:41〜13:44](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=701s) | **CLAUDE.md 単体記憶の限界とObsidianテーマ別分割（LLM Wiki）** | 区間 11:41〜13:44 の解説: CLAUDE.md 単体記憶の限界とObsidianテーマ別分割（LLM Wiki） | time_source: TIMESTAMPED_CAPTIONS | topics: Obsidian, LLM Wiki
- [13:44〜17:36](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=824s) | **Obsidian Vault構築と前月差分抽出プロンプト** | 区間 13:44〜17:36 の解説: Obsidian Vault構築と前月差分抽出プロンプト | time_source: TIMESTAMPED_CAPTIONS | topics: Obsidian
- [17:36〜18:59](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=1056s) | **セットアップ2方式（NotebookLM CLI / Claude Desktop用 .mcpb）** | 区間 17:36〜18:59 の解説: セットアップ2方式（NotebookLM CLI / Claude Desktop用 .mcpb） | time_source: TIMESTAMPED_CAPTIONS | topics: NotebookLM, NotebookLM CLI, .mcpb
- [18:59〜22:18](https://www.youtube.com/watch?v=2-8cXaRHlqI&t=1139s) | **非公式OSSツール利用時のセキュリティ警告・仕様変更リスク** | 区間 18:59〜22:18 の解説: 非公式OSSツール利用時のセキュリティ警告・仕様変更リスク | time_source: TIMESTAMPED_CAPTIONS | topics: Claude Code, 月12日問題, CLAUDE.md肥大化

## 詳細技術知識・再利用ノート
- 整理番号・区分: No.15 (Part 2: 過去調査14本 (No.13〜26)) / 投稿者(Gemini記載): 【さき】のAIでええやん。 / 調査日: 2026-10-16
- YouTube一次メタデータ照合: タイトル=一致 / 投稿者=一致
- 動画長・公開日一次照合: YouTube一次実測長=22:18 (1338s) vs Gemini記載長=22:18 (一致(±2s以内)) | YouTube一次公開日=2026-06-21 vs Gemini記載公開日=2026-06-21 (一致)
- チャプター時刻一次検証内訳: 全10章中 概要欄チャプター一致(YOUTUBE_CHAPTER_METADATA)=0章, 字幕語彙一致(TIMESTAMPED_CAPTIONS)=9章, 一次根拠未確認(UNKNOWN)=1章
- 証拠強度区分: PART2（Gemini過去研究ノート由来・章別一次照合適用）
- 全体要約（原文保持）: Claude Code単体での調査によるコンテキスト圧迫と利用枠枯渇（月12日問題）、およびCLAUDE.md肥大化によるトークン消費を防ぐため、NotebookLM（調査・Studio 9種生成）とObsidian（テーマ別Markdown保管・内部リンク・グラフビュー）を繋ぐ手法を解説。非公式OSS「NotebookLM CLI」やClaude Desktop用.mcpb拡張による連携実演と、非公式ツールの仕様変更・セキュリティ注意点を明示。
- 主要技術キーワード: Claude Code, 月12日問題, CLAUDE.md肥大化, NotebookLM, Obsidian, LLM Wiki, NotebookLM CLI, .mcpb, 非公式OSSリスク
- 公式仕様・一次資料照合報告（一次URL未添付時はREPORTED_BY_AUTHOR扱い）: Claude Code公式Memory仕様（CLAUDE.mdは200行未満推奨、特定知識は外部ファイルへ分離）および.mcpb公式規格と一致。非公式NotebookLM CLIのセキュリティリスク指摘も公式MCP指針と一致。
- 制約・注意点: 「体感1/10」は投稿者の主観値。Studioスライドは画像出力でありPowerPoint文字編集不可。
- 今後の応用・自動化案: リサーチ処理をNotebookLMへ逃がすことでClaude Codeのコンテキスト窓と利用枠を温存する設計。
- 未確認事項（UNKNOWN）: 言及された非公式NotebookLM CLIの正確なGitHubリポジトリURL。

## 主張・一次資料・時刻
- [Gemini公式照合報告(一次URL未添付・要独立確認)] Claude Code公式Memory仕様（CLAUDE.mdは200行未満推奨、特定知識は外部ファイルへ分離）および.mcpb公式規格と一致。非公式NotebookLM CLIのセキュリティリスク指摘も公式MCP指針と一致。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 制約・注意点: 「体感1/10」は投稿者の主観値。Studioスライドは画像出力でありPowerPoint文字編集不可。 / 今後の応用: リサーチ処理をNotebookLMへ逃がすことでClaude Codeのコンテキスト窓と利用枠を温存する設計。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 未確認事項(UNKNOWN): 言及された非公式NotebookLM CLIの正確なGitHubリポジトリURL。 | UNKNOWN | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

## 関連する既存研究・課題との接続

- `youtube:RZLAP2CLUM8:research` (COMPLEMENTS): 自動推定の候補（未確認）：共通の主題「markdown・神連携・cli」 | status: CANDIDATE | evidence: 共通語: markdown, 神連携, cli, obsidian, リサーチ ／ 本ノート: 題名「【天才AI化】ClaudeのフルMAXパワーを出すAI神連携はNotebook…」 ／ 相手: 題名「【情報収集を完全自動化】NotebookLM・Claude Code・Obsi…」
- `youtube:BStkW1HTfmk:research` (COMPLEMENTS): 自動推定の候補（未確認）：共通の主題「vault・markdown・claude.md」 | status: CANDIDATE | evidence: 共通語: vault, markdown, claude.md, mcp, obsidian ／ 本ノート: 章「CLAUDE.md 単体記憶の限界とObsidianテーマ別分割（LLM Wi…」 ／ 相手: 章「CLAUDE.md / AGENTS.md / MEMORY.md の基本構成…」
- `youtube:ZY7YuYHLlIQ:research` (COMPLEMENTS): 自動推定の候補（未確認）：共通の主題「文字編集不可・画像出力・studio」 | status: CANDIDATE | evidence: 共通語: 文字編集不可, 画像出力, studio, notebooklm, スライド ／ 本ノート: 章「Studio機能9種生成の実演」 ／ 相手: 章「Studioスライドの罠：画像出力であり文字編集不可の仕様解説」
- `youtube:JXmk7hmbS3c:research` (COMPLEMENTS): 逆向きの候補（自動・未確認）：共通の主題「claude.md・cli・mcp」 | status: CANDIDATE | evidence: 共通語: claude.md, cli, mcp, obsidian, サブエージェント ／ 相手: 章「⑤ CLAUDE.md への行動指針とスキル別エージェントマッピング記載」 ／ 本ノート: 章「CLAUDE.md 単体記憶の限界とObsidianテーマ別分割（LLM Wi…」
- `youtube:MnzEE0fLxBs:research` (UPDATES): 逆向きの候補（自動・未確認）：共通の主題「studio・notebooklm・powerpoint」 | status: CANDIDATE | evidence: 共通語: studio, notebooklm, powerpoint, スライド, notebook ／ 相手: 章「UI構成（左：ソース、中央：チャット、右：Studio）」 ／ 本ノート: 章「Studio機能9種生成の実演」 ／ 投稿日時: 2026-09-17 → 2026-06-21
- `youtube:NCQZiT0e59g:research` (COMPLEMENTS): 逆向きの候補（自動・未確認）：共通の主題「obsidian・studio・mcp」 | status: CANDIDATE | evidence: 共通語: obsidian, studio, mcp ／ 相手: 章「視聴者Q&A②：Obsidianへの評価とGemini TTS（音声読み上げ）…」 ／ 本ノート: 章「3ツールの役割分担（NotebookLM＝調査、Obsidian＝社内DB、C…」
- `youtube:XckM9eFa_vg:research` (COMPLEMENTS): 逆向きの候補（自動・未確認）：共通の主題「vault・claude.md・obsidian」 | status: CANDIDATE | evidence: 共通語: vault, claude.md, obsidian, markdown ／ 相手: 章「ObsidianでのVaultオープンとマークダウン視覚化デモ」 ／ 本ノート: 章「Obsidian Vault構築と前月差分抽出プロンプト」
- `youtube:ZjUJ-35acaU:research` (COMPLEMENTS): 逆向きの候補（自動・未確認）：Gemini Notebook / NotebookLMへの情報集約・Studio出力・知識索引運用を補完 | status: CANDIDATE | evidence: 相手ノートの記載: キーワード・テーマ類似による候補接続（動画本編言及未検証）

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。
