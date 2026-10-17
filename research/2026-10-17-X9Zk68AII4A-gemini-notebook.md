# 【神機能】Claude Codeで『Evalの改善スキル』が登場！本当に教えたいSkillを徹底解説

- record_id: `youtube:X9Zk68AII4A`
- video_id: `X9Zk68AII4A`
- canonical_url: https://www.youtube.com/watch?v=X9Zk68AII4A
- original_url: https://www.youtube.com/watch?v=X9Zk68AII4A
- publication_date: 2026-10-15
- checked_at: 2026-10-17
- source_scope: YOUTUBE_TRANSCRIPT_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:AI技術研究室_直近調査12本_完全総合辞書_20261017
- Gemini Notebook source: AI技術研究室_直近調査12本_完全総合辞書_20261017
- Gemini readback (self-reported): PASS
- GitHub independent verification: NOT_RUN
- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB
- changes: NEW

## 独自要約
Claude Codeのプラグイン機能「Skill」を用いたEval（評価関数）改善ワークフローの実演。自己改善ループ（RSI）を実現する『build-eval』および『hillclimb』スキルの仕組みを詳解。テストデータセットの自動生成、ベースライン測定、プロンプト・コードの自動反復改善、および過剰適合（過学習）を防ぐホールドアウト検証の設計手法を解説。

## 動画目次・確認済みタイムライン（チャプター）
- UNKNOWN | **概要・プロンプト職人の勘に頼る改善の限界** | Gemini報告区間(00:00〜02:20 / 一次時刻未確認のため再生リンク非生成): 概要・プロンプト職人の勘に頼る改善の限界 | time_source: UNKNOWN | topics: Claude Code Skill, build-eval, hillclimb
- UNKNOWN | **Skill機能のアーキテクチャとコマンド拡張の仕組み** | Gemini報告区間(02:20〜05:40 / 一次時刻未確認のため再生リンク非生成): Skill機能のアーキテクチャとコマンド拡張の仕組み | time_source: UNKNOWN | topics: Claude Code Skill, build-eval, hillclimb
- UNKNOWN | **build-eval：評価指標とテストケースの自動策定** | Gemini報告区間(05:40〜09:50 / 一次時刻未確認のため再生リンク非生成): build-eval：評価指標とテストケースの自動策定 | time_source: UNKNOWN | topics: build-eval
- UNKNOWN | **hillclimb実演：山登り法による自動自己改善ループ実行** | Gemini報告区間(09:50〜14:15 / 一次時刻未確認のため再生リンク非生成): hillclimb実演：山登り法による自動自己改善ループ実行 | time_source: UNKNOWN | topics: hillclimb
- UNKNOWN | **過剰適合の罠とホールドアウトテストによる防御法** | Gemini報告区間(14:15〜17:30 / 一次時刻未確認のため再生リンク非生成): 過剰適合の罠とホールドアウトテストによる防御法 | time_source: UNKNOWN | topics: Claude Code Skill, build-eval, hillclimb
- UNKNOWN | **まとめ・実務導入に向けた3ステップ** | Gemini報告区間(17:30〜19:45 / 一次時刻未確認のため再生リンク非生成): まとめ・実務導入に向けた3ステップ | time_source: UNKNOWN | topics: Claude Code Skill, build-eval, hillclimb

## 詳細技術知識・再利用ノート
- 整理番号・区分: No.04 (Part 1: 直近調査12本 (No.01〜12)) / 投稿者: まさお / AI活用チャンネル / 調査日: 2026-10-16
- 動画長・公開日照合: Gemini記載長=19:45, 記載公開日=2026-10-15 | YouTube一次実測長=21:11 (1271s), 一次公開日=2026-10-03
- 証拠強度区分: PART1（Notebook内のYouTubeソース由来）
- 全体要約（原文完全保持）: Claude Codeのプラグイン機能「Skill」を用いたEval（評価関数）改善ワークフローの実演。自己改善ループ（RSI）を実現する『build-eval』および『hillclimb』スキルの仕組みを詳解。テストデータセットの自動生成、ベースライン測定、プロンプト・コードの自動反復改善、および過剰適合（過学習）を防ぐホールドアウト検証の設計手法を解説。
- 主要技術キーワード: Claude Code Skill, build-eval, hillclimb, Eval駆動開発, 自己改善ループ (RSI), ホールドアウト検証, 過剰適合防止
- 公式仕様・一次資料照合詳細: Claude Code公式Skillプラグイン仕様およびAnthropic評価ベンチマーク指針と整合。
- 制約・注意点: 反復回数を増やしすぎるとAPI消費が急増するためステップ上限設定が必須。
- 今後の応用・自動化案: 自律エージェントのプロンプトとコード品質を自動向上させるCI/CDパイプラインへのEval統合。
- 未確認事項（UNKNOWN）: hillclimb内部アルゴリズムにおける収束判定の完全な自動閾値パラメータ。
- YouTube概要欄の公式チャプター（一次照合参照用）: 00:00 OP / 01:50 過剰適合とは / 03:31 trainとtest分離 / 05:10 メール振り分け例題 / 05:52 evalの4条件 / 07:41 build-eval実演 / 08:52 過剰適合の3防御法 / 10:44 hillclimbの回し方 / 12:53 Sonnet 5スコア98.9% / 16:02 claude-api skill改善 / 17:32 まとめ

## 主張・一次資料・時刻
- [PART1直近調査の公式照合] Claude Code公式Skillプラグイン仕様およびAnthropic評価ベンチマーク指針と整合。 | CONFIRMED_DOC | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 制約・注意点: 反復回数を増やしすぎるとAPI消費が急増するためステップ上限設定が必須。 / 今後の応用: 自律エージェントのプロンプトとコード品質を自動向上させるCI/CDパイプラインへのEval統合。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 未確認事項(UNKNOWN): hillclimb内部アルゴリズムにおける収束判定の完全な自動閾値パラメータ。 | UNKNOWN | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

## 関連する既存研究・課題との接続
- `youtube:lC5jxpYmatE` (EXTENDS): 動画05のSkill・ハーネス設計に対し、build-evalとhillclimbによる定量評価・自己改善ループ(RSI)を追加
- `proposal:P006` (COMPLEMENTS): 未解決課題の再挑戦評価に向けたホールドアウト検証付きEval駆動開発手順を提供

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。
