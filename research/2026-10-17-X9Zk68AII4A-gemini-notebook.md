---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "【研究カード】 【神機能】Claude Codeで『Evalの改善スキル』が登場！本当に教えたいSkillを徹底解説"
logical_id: "youtube:X9Zk68AII4A:research"
record_id: "youtube:X9Zk68AII4A"
video_id: "X9Zk68AII4A"
resource: "https://www.youtube.com/watch?v=X9Zk68AII4A"
canonical_url: "https://www.youtube.com/watch?v=X9Zk68AII4A"
published_at: "2026-10-03T03:00:04-07:00"
published_at_jst: "2026-10-03T19:00:04+09:00"
publication_date: "2026-10-03"
published_at_source: "YouTube視聴ページの publishDate（2026-10-20取得）"
transcript_logical_id: "youtube:X9Zk68AII4A:transcript"
transcript_notebook_source_id: "c456adc4-0e0c-47ac-ba15-18519676f937"
research_notebook_source_id: "ac71a06b-1dc5-43ec-994a-e164ce7dd669"
transcript_status: "UNVERIFIED"
front_matter_note: "2026-10-21 OKF荷札を先頭に追加（本文は変更なし）"
related_records:
  - target_id: "youtube:NCQZiT0e59g:research"
    relation: "COMPLEMENTS"
    note: "どちらもAIの自己改善ループ（RSI）を扱う。片方はAI社員の構成要素の1つとして、もう片方はEval改善スキルの実装として"
    evidence: "両研究ノートの独自要約（④自己改善ループ（RSI）／build-eval・hillclimbによるRSI）"
    status: "CANDIDATE"
    added_at: "2026-10-21"
---
# 【神機能】Claude Codeで『Evalの改善スキル』が登場！本当に教えたいSkillを徹底解説

- record_id: `youtube:X9Zk68AII4A`
- video_id: `X9Zk68AII4A`
- canonical_url: https://www.youtube.com/watch?v=X9Zk68AII4A
- original_url: https://www.youtube.com/watch?v=X9Zk68AII4A
- publication_date: 2026-10-03 (YouTube一次確認 / Gemini記載値: 2026-10-15)
- checked_at: 2026-10-17
- source_scope: YOUTUBE_TRANSCRIPT_AND_OFFICIAL_DOCS | NOTEBOOK_SOURCE:AI技術研究室_直近調査12本_完全総合辞書_20261017
- Gemini Notebook source: AI技術研究室_直近調査12本_完全総合辞書_20261017
- Gemini readback (self-reported): UNKNOWN
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
- 整理番号・区分: No.04 (Part 1: 直近調査12本 (No.01〜12)) / 投稿者(Gemini記載): まさお / AI活用チャンネル / 調査日: 2026-10-16
- YouTube一次メタデータ照合: タイトル=一致 / 投稿者=不一致(YouTube一次=「まさおAIじっくり解説ch」 vs Gemini記載=「まさお / AI活用チャンネル」)
- 動画長・公開日一次照合: YouTube一次実測長=21:11 (1271s) vs Gemini記載長=19:45 (不一致) | YouTube一次公開日=2026-10-03 vs Gemini記載公開日=2026-10-15 (不一致)
- チャプター時刻一次検証内訳: 全6章中 概要欄チャプター一致(YOUTUBE_CHAPTER_METADATA)=0章, 字幕語彙一致(TIMESTAMPED_CAPTIONS)=0章, 一次根拠未確認(UNKNOWN)=6章
- 証拠強度区分: PART1（Notebook内のYouTubeソース由来・章別一次照合適用）
- 全体要約（原文保持）: Claude Codeのプラグイン機能「Skill」を用いたEval（評価関数）改善ワークフローの実演。自己改善ループ（RSI）を実現する『build-eval』および『hillclimb』スキルの仕組みを詳解。テストデータセットの自動生成、ベースライン測定、プロンプト・コードの自動反復改善、および過剰適合（過学習）を防ぐホールドアウト検証の設計手法を解説。
- 主要技術キーワード: Claude Code Skill, build-eval, hillclimb, Eval駆動開発, 自己改善ループ (RSI), ホールドアウト検証, 過剰適合防止
- 公式仕様・一次資料照合報告（一次URL未添付時はREPORTED_BY_AUTHOR扱い）: Claude Code公式Skillプラグイン仕様およびAnthropic評価ベンチマーク指針と整合。
- 制約・注意点: 反復回数を増やしすぎるとAPI消費が急増するためステップ上限設定が必須。
- 今後の応用・自動化案: 自律エージェントのプロンプトとコード品質を自動向上させるCI/CDパイプラインへのEval統合。
- 未確認事項（UNKNOWN）: hillclimb内部アルゴリズムにおける収束判定の完全な自動閾値パラメータ。
- YouTube概要欄の公式チャプター（一次照合参照用）: 00:00 オープニング・Claude 公式の eval 記事 / 01:50 過剰適合とは? OCR ツールの例 / 03:31 train と test に分けて過剰適合を防ぐ / 05:10 例題: メール振り分けアプリ (68%) / 05:52 頼りになる eval の 4 つの条件 / 07:41 build-eval を実際に使ってみる / 08:52 過剰適合の原因と 3 つの防ぎ方 / 10:44 hillclimb の回し方と失敗の分類 / 12:53 Sonnet 5 で費用減・スコア 98.9% / 16:02 claude-api skill の改善例 / 17:32 まとめ: 両方で上がった修正だけ残す / 19:40 エンディング・メンバーシップ案内

## 主張・一次資料・時刻
- [Gemini公式照合報告(一次URL未添付・要独立確認)] Claude Code公式Skillプラグイン仕様およびAnthropic評価ベンチマーク指針と整合。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 制約・注意点: 反復回数を増やしすぎるとAPI消費が急増するためステップ上限設定が必須。 / 今後の応用: 自律エージェントのプロンプトとコード品質を自動向上させるCI/CDパイプラインへのEval統合。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- 未確認事項(UNKNOWN): hillclimb内部アルゴリズムにおける収束判定の完全な自動閾値パラメータ。 | UNKNOWN | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

## 関連する既存研究・課題との接続
- `youtube:lC5jxpYmatE` (EXTENDS): 課題ドリブン・Skill・Computer Use・ハーネス設計に対する評価・自己改善・実行ループを拡張
- `proposal:P006` (COMPLEMENTS): 未解決課題ストック(P006)の再評価・検証ループ設計を補完

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。
