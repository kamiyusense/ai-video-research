# 動画研究候補07｜AIエージェント×Obsidian（本編確認待ち）

- record_id: youtube:BStkW1HTfmk
- video_id: BStkW1HTfmk
- URL: https://www.youtube.com/watch?v=BStkW1HTfmk
- タイトル（公開動画一覧で確認）: 【22分で完全解説】今日からはじめる AIエージェント×Obsidian。AIへの説明し直しを卒業して、ClaudeもChatGPTも「右腕」にする方法。
- 投稿者: Leo Tohyama / AIコーチ
- 公開日（動画一覧から）: 2026-09-23
- 研究日: 2026-10-10（JST）
- 動画映像・字幕・音声: **UNKNOWN / NOT_ACQUIRED**。YouTube URLの取得が失敗、メタデータ相当と関連する前回の投稿者公式記事およびObsidian公式仕様だけを確認
- 動画内時刻: **UNKNOWN**。ここでは動画の内容・実演の説明と時刻を創作しない
- 動画本体・字幕全文: 保存せず
- 状態: METADATA_ONLY / OFFICIAL_OBSIDIAN_DOCS_REVIEWED / VIDEO_CONTENT_REVIEW_PENDING / LIVE_NOT_RUN

## 動画で扱うと公開情報から確認できたテーマ（内容確定ではない）
「AIエージェント×Obsidian」「AIへの説明し直し」「ClaudeとChatGPTを右腕として活用する方法」。正確な動画内の手順、実演の範囲、具体的な限界、タイムスタンプは動画未取得のためUNKNOWN。
前動画（Work担当制）の公開解説：https://leotohyama.com/ai-tips/migiude-ai-chatgpt-work/
**別動画の発言を今回の動画で説明したものとして転載しない。**

## Obsidian公式で独立して確認したこと
1. ObsidianはローカルMarkdownフォルダ（vault）を開くGUI。既存フォルダを「Open folder as vault」で利用できる。
   - https://obsidian.md/help/vault
2. Obsidian本体は無償、アカウント不要、個人・商用利用とも無料。有料のObsidian Sync/Publishは任意。
   - https://obsidian.md/ja/pricing
   - https://obsidian.md/blog/free-for-work/
3. 標準のBacklinks/Graph view/Search/Properties/File recoveryなどは、研究ノートの発見・つながりの確認に使用可能。
   - https://obsidian.md/help/Plugins/Core+plugins
4. ObsidianとGitHubは別サービス。Gitで同期する方法は紹介されるが、自動同期の設定には別途構成が必要。Obsidian Sync有料契約はGitHubリポジトリとの自動連携機能ではない。
   - https://obsidian.md/help/Getting+started/Sync+your+notes+across+devices
5. 共有のMarkdownフォルダにはObsidian設定の `.obsidian/` が作られる。リポジトリへ不要なローカル設定を無条件に追加しない。
   - https://obsidian.md/help/configuration-folder
6. コミュニティプラグインはPC上のファイルとネット接続等にアクセスし得る。初期導入では不使用を推奨。
   - https://obsidian.md/help/plugin-security

## GitHub担当制への適用評価（ウチの独自提案）
- **採用候補**: Obsidianは人間にとっての読む・探す・関係を見るUI。GitHubを研究正本とする。5担当のAGENTS/MEMORYとregistryは維持。
- **採用しない**: 新しいObsidian専用の研究正本、Markdown全文の二重管理、GitHubとObsidian Sync両方の同時同期、APIキーを必要とするプラグイン、自動外部AI起動の代用品という説明。
- **要検証**: Windowsでprivate GitHubの正しいブランチをローカルに置き、Obsidianから読めるか。標準リンク表示と書換え影響、.obsidianの無用なコミット防止。
- **動画本編からの移植判断**はPending。今の文書はObsidian公式仕様ベースの暫定設計であって「動画07研究完了」ではない。

## 次回追加調査
ユーザーからAI Studioの映像報告とGemini Sparkの字幕/独立調査報告、または信頼できる時刻付き原本が届いたら、動画の説明・実演・限界を正確な位置で追記。その後、今回の公式仕様ベースの提案と差分比較。未取得なら動画の詳細をUNKNOWNのまま維持。
## 差分更新 (2026-10-17 / UPDATED)

- checked_at: 2026-10-17
- source_scope: GEMINI_PAST_RESEARCH_NOTE_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:AI技術研究室_過去調査14本_完全総合辞書_20261017
- Gemini Notebook source: AI技術研究室_過去調査14本_完全総合辞書_20261017
- Gemini readback (self-reported): UNKNOWN
- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB
- changes: UPDATED

### 差分要約
AIへの毎回の説明し直しを解消するため、ローカルMarkdown（Obsidian）を全エージェントの共通記憶とするアーキテクチャを提唱。CLAUDE.md / AGENTS.md / MEMORY.md を土台とし、Googleドライブ操作（MCP経由：API 840回呼出・40分消費）とローカル直接操作（5回・4分完了）の定量速度・クォータ消費を比較実験。知識のローカル保管によるベンダーロックイン回避を実証。

### 追加・更新された動画目次・タイムライン
- UNKNOWN | **概要・AIへの毎回の説明し直しの解消** | Gemini報告区間(00:00〜02:15 / 一次時刻未確認のため再生リンク非生成): 概要・AIへの毎回の説明し直しの解消 | time_source: UNKNOWN | topics: Obsidian, ローカル共創, CLAUDE.md
- UNKNOWN | **ローカルMarkdown（Obsidian）を共通記憶とするアーキテクチャ** | Gemini報告区間(02:15〜05:40 / 一次時刻未確認のため再生リンク非生成): ローカルMarkdown（Obsidian）を共通記憶とするアーキテクチャ | time_source: UNKNOWN | topics: Obsidian
- UNKNOWN | **CLAUDE.md / AGENTS.md / MEMORY.md の基本構成とディレクトリ設計** | Gemini報告区間(05:40〜09:10 / 一次時刻未確認のため再生リンク非生成): CLAUDE.md / AGENTS.md / MEMORY.md の基本構成とディレクトリ設計 | time_source: UNKNOWN | topics: CLAUDE.md, AGENTS.md, MEMORY.md
- UNKNOWN | **定量比較実験：ローカル直接操作（4分）vs MCP経由Googleドライブ（40分・840回API）** | Gemini報告区間(09:10〜14:30 / 一次時刻未確認のため再生リンク非生成): 定量比較実験：ローカル直接操作（4分）vs MCP経由Googleドライブ（40分・840回API） | time_source: UNKNOWN | topics: Obsidian, ローカル共創, CLAUDE.md
- UNKNOWN | **知識のローカル保管によるベンダーロックイン回避とデータ主権** | Gemini報告区間(14:30〜18:20 / 一次時刻未確認のため再生リンク非生成): 知識のローカル保管によるベンダーロックイン回避とデータ主権 | time_source: UNKNOWN | topics: ベンダーロックイン回避
- UNKNOWN | **実践セットアップと複数モデル（Claude / GPT / Gemini）連携運用フロー** | Gemini報告区間(18:20〜21:00 / 一次時刻未確認のため再生リンク非生成): 実践セットアップと複数モデル（Claude / GPT / Gemini）連携運用フロー | time_source: UNKNOWN | topics: Obsidian, ローカル共創, CLAUDE.md
- UNKNOWN | **まとめ・一生モノのローカルナレッジベース構築法** | Gemini報告区間(21:00〜22:45 / 一次時刻未確認のため再生リンク非生成): まとめ・一生モノのローカルナレッジベース構築法 | time_source: UNKNOWN | topics: Obsidian, ローカル共創, CLAUDE.md

### 追加・更新された詳細技術知識
- 整理番号・区分: No.26 (Part 2: 過去調査14本 (No.13〜26)) / 投稿者(Gemini記載): Leo Tohyama / AIコーチ / 調査日: 2026-10-16
- YouTube一次メタデータ照合: タイトル=不一致(YouTube一次=「【22分で完全解説】今日からはじめる AIエージェント×Obsidian。AIへの説明し直しを卒業して、ClaudeもChatGPTも「右腕」にする方法。」 vs Gemini記載=「AIエージェントの最適解は「Obsidian×ローカル共創」だ。MCPによるクラウド連携との比較実験」) / 投稿者=一致
- 動画長・公開日一次照合: YouTube一次実測長=22:21 (1341s) vs Gemini記載長=22:45 (不一致) | YouTube一次公開日=2026-10-05 vs Gemini記載公開日=2026-09-15 (不一致)
- チャプター時刻一次検証内訳: 全7章中 概要欄チャプター一致(YOUTUBE_CHAPTER_METADATA)=0章, 字幕語彙一致(TIMESTAMPED_CAPTIONS)=0章, 一次根拠未確認(UNKNOWN)=7章
- 証拠強度区分: PART2（Gemini過去研究ノート由来・章別一次照合適用）
- 全体要約（原文保持）: AIへの毎回の説明し直しを解消するため、ローカルMarkdown（Obsidian）を全エージェントの共通記憶とするアーキテクチャを提唱。CLAUDE.md / AGENTS.md / MEMORY.md を土台とし、Googleドライブ操作（MCP経由：API 840回呼出・40分消費）とローカル直接操作（5回・4分完了）の定量速度・クォータ消費を比較実験。知識のローカル保管によるベンダーロックイン回避を実証。
- 主要技術キーワード: Obsidian, ローカル共創, CLAUDE.md, AGENTS.md, MEMORY.md, MCP比較実験, ベンダーロックイン回避, クォータ消費削減
- 公式仕様・一次資料照合報告（一次URL未添付時はREPORTED_BY_AUTHOR扱い）: Model Context Protocol (MCP) の通信オーバーヘッド仕様およびローカルファイルI/O速度特性と完全一致。
- 制約・注意点: 複数PCやスマホとの同期にはObsidian SyncまたはGit同期の設定が必要。
- 今後の応用・自動化案: すべてのエージェントが共通参照するローカルVaultの構築と、クラウドMCPの最小限化。
- 未確認事項（UNKNOWN）: Leo氏が実験で使用したGoogleドライブMCPサーバーの実装コード全文。
- YouTube概要欄の公式チャプター（一次照合参照用）: 00:00 Obsidianに注目している理由 / 00:48 Obsidianの基本 / 04:26 重要なのは機能じゃない / 06:12 右腕AIのフォルダをObsidianで見る / 08:10 共創の現場 / 10:57 右腕AIのフォルダをiCloudで同期するベストプラクティス / 12:29 なぜGoogleドライブじゃだめなのか / 15:58 窓口テスト ローカル vs Googleドライブ / 19:55 保管庫に何でも置かない / 21:32 まとめ

### 追加・更新された主張と検証
- [Gemini公式照合報告(一次URL未添付・要独立確認)] Model Context Protocol (MCP) の通信オーバーヘッド仕様およびローカルファイルI/O速度特性と完全一致。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 制約・注意点: 複数PCやスマホとの同期にはObsidian SyncまたはGit同期の設定が必要。 / 今後の応用: すべてのエージェントが共通参照するローカルVaultの構築と、クラウドMCPの最小限化。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 未確認事項(UNKNOWN): Leo氏が実験で使用したGoogleドライブMCPサーバーの実装コード全文。 | UNKNOWN | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

### 追加・更新された関連研究・課題接続
- `youtube:BStkW1HTfmk` (UPDATES): 既存研究記録に対し、Gemini Notebook調査知見・一次メタデータおよび時刻検証結果を差分統合
- [youtube:Vr3JkAT9mo8:research](2026-10-10-Vr3JkAT9mo8-work-specialists.md) (COMPLEMENTS): AGENTS.md・MEMORY.md・専門サブエージェント分業アーキテクチャを補完 | status: CANDIDATE | evidence: キーワード・テーマ類似による候補接続（動画本編言及未検証）
- [youtube:2-8cXaRHlqI:research](2026-10-17-2-8cXaRHlqI-gemini-notebook.md) (COMPLEMENTS): ObsidianローカルVaultによる長期記憶・ナレッジ構造化設計を補完 | status: CANDIDATE | evidence: キーワード・テーマ類似による候補接続（動画本編言及未検証）
- [youtube:JXmk7hmbS3c:research](2026-10-17-JXmk7hmbS3c-gemini-notebook.md) (COMPLEMENTS): ObsidianローカルVaultによる長期記憶・ナレッジ構造化設計を補完 | status: CANDIDATE | evidence: キーワード・テーマ類似による候補接続（動画本編言及未検証）
- [youtube:RZLAP2CLUM8:research](2026-10-17-RZLAP2CLUM8-gemini-notebook.md) (COMPLEMENTS): ObsidianローカルVaultによる長期記憶・ナレッジ構造化設計を補完 | status: CANDIDATE | evidence: キーワード・テーマ類似による候補接続（動画本編言及未検証）
- [youtube:XckM9eFa_vg:research](2026-10-17-XckM9eFa_vg-gemini-notebook.md) (COMPLEMENTS): ObsidianローカルVaultによる長期記憶・ナレッジ構造化設計を補完 | status: CANDIDATE | evidence: キーワード・テーマ類似による候補接続（動画本編言及未検証）

