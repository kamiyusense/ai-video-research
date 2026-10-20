# 【情報収集を完全自動化】NotebookLM・Claude Code・Obsidianの神連携ワークフローを徹底解説

- record_id: `youtube:RZLAP2CLUM8`
- video_id: `RZLAP2CLUM8`
- canonical_url: https://www.youtube.com/watch?v=RZLAP2CLUM8
- original_url: https://www.youtube.com/watch?v=RZLAP2CLUM8
- publication_date: 2026-09-10 (YouTube一次確認一致)
- checked_at: 2026-10-17
- source_scope: GEMINI_PAST_RESEARCH_NOTE_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:AI技術研究室_過去調査14本_完全総合辞書_20261017
- Gemini Notebook source: AI技術研究室_過去調査14本_完全総合辞書_20261017
- Gemini readback (self-reported): UNKNOWN
- GitHub independent verification: NOT_RUN
- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB
- changes: NEW

## 独自要約
情報収集から提案書作成までの3ステップ（①NotebookLMへの複数情報集約、②Claude Codeによる要約抽出と提案骨子作成、③Obsidianへの構造化Markdown保存と内部リンク構築）を実演。意思決定のログをObsidianに残し、翌月以降の差分分析を自動化するワークフローを提示。

## 動画目次・確認済みタイムライン（チャプター）
- UNKNOWN | **概要・情報過多時代の情報収集・提案書作成課題** | Gemini報告区間(00:00〜02:30 / 一次時刻未確認のため再生リンク非生成): 概要・情報過多時代の情報収集・提案書作成課題 | time_source: UNKNOWN | topics: 提案書作成
- UNKNOWN | **ステップ1：NotebookLMへの複数情報ソース（PDF、Web、YouTube）集約** | Gemini報告区間(02:30〜06:15 / 一次時刻未確認のため再生リンク非生成): ステップ1：NotebookLMへの複数情報ソース（PDF、Web、YouTube）集約 | time_source: UNKNOWN | topics: NotebookLM
- UNKNOWN | **ステップ2：Claude Codeによる要約抽出と提案骨子・ドラフト作成** | Gemini報告区間(06:15〜10:40 / 一次時刻未確認のため再生リンク非生成): ステップ2：Claude Codeによる要約抽出と提案骨子・ドラフト作成 | time_source: UNKNOWN | topics: Claude Code
- UNKNOWN | **ステップ3：Obsidianへの構造化Markdown保存と内部リンク（[[ ]]）構築** | Gemini報告区間(10:40〜14:20 / 一次時刻未確認のため再生リンク非生成): ステップ3：Obsidianへの構造化Markdown保存と内部リンク（[[ ]]）構築 | time_source: UNKNOWN | topics: Obsidian, 内部リンク
- UNKNOWN | **判断過程（ログ）の蓄積と翌月以降の差分分析ワークフロー** | Gemini報告区間(14:20〜17:10 / 一次時刻未確認のため再生リンク非生成): 判断過程（ログ）の蓄積と翌月以降の差分分析ワークフロー | time_source: UNKNOWN | topics: 差分分析
- UNKNOWN | **まとめ・リサーチ業務の9割削減効果** | Gemini報告区間(17:10〜18:42 / 一次時刻未確認のため再生リンク非生成): まとめ・リサーチ業務の9割削減効果 | time_source: UNKNOWN | topics: NotebookLM, Claude Code, Obsidian

## 詳細技術知識・再利用ノート
- 整理番号・区分: No.14 (Part 2: 過去調査14本 (No.13〜26)) / 投稿者(Gemini記載): AIの中の人 / 調査日: 2026-10-16
- YouTube一次メタデータ照合: タイトル=一致 / 投稿者=一致
- 動画長・公開日一次照合: YouTube一次実測長=12:43 (763s) vs Gemini記載長=18:42 (不一致) | YouTube一次公開日=2026-09-10 vs Gemini記載公開日=2026-09-10 (一致)
- チャプター時刻一次検証内訳: 全6章中 概要欄チャプター一致(YOUTUBE_CHAPTER_METADATA)=0章, 字幕語彙一致(TIMESTAMPED_CAPTIONS)=0章, 一次根拠未確認(UNKNOWN)=6章
- 証拠強度区分: PART2（Gemini過去研究ノート由来・章別一次照合適用）
- 全体要約（原文保持）: 情報収集から提案書作成までの3ステップ（①NotebookLMへの複数情報集約、②Claude Codeによる要約抽出と提案骨子作成、③Obsidianへの構造化Markdown保存と内部リンク構築）を実演。意思決定のログをObsidianに残し、翌月以降の差分分析を自動化するワークフローを提示。
- 主要技術キーワード: NotebookLM, Claude Code, Obsidian, 情報収集自動化, 提案書作成, 内部リンク, 差分分析, 意思決定ログ
- 公式仕様・一次資料照合報告（一次URL未添付時はREPORTED_BY_AUTHOR扱い）: Obsidian公式データストレージ仕様およびClaude Codeファイル読み書き仕様と一致。
- 制約・注意点: NotebookLM側の出力をClaude Codeへ手動またはCLIで渡す連携ステップが必要。
- 今後の応用・自動化案: NotebookLMで粗削りした一次情報をObsidianでナレッジベース化しClaude Codeで最終成果物化。
- 未確認事項（UNKNOWN）: 投稿者が実務で使用しているObsidian専用テンプレートプラグイン名。
- YouTube概要欄の公式チャプター（一次照合参照用）: 00:00 ハイライト / 00:29 OPトーク / 01:48 NotebookLM ClaudeCode obsidianの比較 / 04:43 NotebookLM ClaudeCode obsidianの連携 / 07:20 競合調査・提案書・知識保存 / 11:11 本日のまとめ

## 主張・一次資料・時刻
- [Gemini公式照合報告(一次URL未添付・要独立確認)] Obsidian公式データストレージ仕様およびClaude Codeファイル読み書き仕様と一致。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 制約・注意点: NotebookLM側の出力をClaude Codeへ手動またはCLIで渡す連携ステップが必要。 / 今後の応用: NotebookLMで粗削りした一次情報をObsidianでナレッジベース化しClaude Codeで最終成果物化。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 未確認事項(UNKNOWN): 投稿者が実務で使用しているObsidian専用テンプレートプラグイン名。 | UNKNOWN | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

## 関連する既存研究・課題との接続

- `youtube:2-8cXaRHlqI:research` (COMPLEMENTS): 自動推定の候補（未確認）：共通の主題「markdown・神連携・cli」 | status: CANDIDATE | evidence: 共通語: markdown, 神連携, cli, obsidian, リサーチ ／ 本ノート: 題名「【情報収集を完全自動化】NotebookLM・Claude Code・Obsi…」 ／ 相手: 題名「【天才AI化】ClaudeのフルMAXパワーを出すAI神連携はNotebook…」
- `youtube:JXmk7hmbS3c:research` (COMPLEMENTS): 自動推定の候補（未確認）：共通の主題「pdf・obsidian・cli」 | status: CANDIDATE | evidence: 共通語: pdf, obsidian, cli ／ 本ノート: 章「ステップ1：NotebookLMへの複数情報ソース（PDF、Web、YouTu…」 ／ 相手: 章「③ Discord MCP接続（生成画像・PDFをスマホへ自動送信・確認）」
- `youtube:BStkW1HTfmk:research` (COMPLEMENTS): 逆向きの候補（自動・未確認）：ObsidianローカルVaultによる長期記憶・ナレッジ構造化設計を補完 | status: CANDIDATE | evidence: 相手ノートの記載: キーワード・テーマ類似による候補接続（動画本編言及未検証）
- `youtube:ZjUJ-35acaU:research` (COMPLEMENTS): 逆向きの候補（自動・未確認）：Gemini Notebook / NotebookLMへの情報集約・Studio出力・知識索引運用を補完 | status: CANDIDATE | evidence: 相手ノートの記載: キーワード・テーマ類似による候補接続（動画本編言及未検証）

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。
