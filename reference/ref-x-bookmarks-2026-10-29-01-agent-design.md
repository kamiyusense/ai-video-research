---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "参考ノート：エージェント設計・自動運用・レビュー（Xブックマーク5件）"
description: "Xでブックマークした5件（サブエージェントの畳み方、AIコードレビュー、無人実行環境、QA手順）をGrok Botが分類した要約の写し。ポスト本文は未確認。"
tags:
  - "AI技術研究室"
  - "参考資料"
  - "エージェント設計"
logical_id: "ref:x-bookmarks:2026-10-29:agent-design"
source_kind: "x_post_collection"
source_tier: "SECONDARY_SUMMARY"
source_made_by: "Grok Bot（相棒がXブックマークを整理させたレポート）"
content_status: "SUMMARY_ONLY"
acquired_at: "2026-10-30"
acquisition_method: "相棒がチャットに貼ったレポートの転記"
resource: "UNKNOWN"
canonical_url: "UNKNOWN"
related_records:
  - target_id: "ref:slides:139dGZvm:subagent-fold-check"
    relation: "COMPLEMENTS"
    note: "1件目と2件目は同じAnthropic記事を扱う。スライド側に、記事と突き合わせた照合結果がある"
---

# エージェント設計・自動運用・レビュー（Xブックマーク5件）

## 独自要約

サブエージェントはメイン1本に畳む設計の勧め、AIでコードレビューを自動化する体制、承認作業から解放される無人実行環境、わざと壊すQA手順の5件。共通点は「人間がボトルネックになる所をAIに寄せつつ、確認の仕組みは残す」こと。Grok Botの要約の写しなので、数字（約2倍速、40%など）は未照合。

## 項目

- @makaneko_AI：Anthropic公式の「サブエージェントは極力メイン1本に畳む」設計の推奨の解説（品質↑・コスト↓・約2倍速の事例、例外条件つき）。リンク：https://x.com/makaneko_AI/status/2114619893907906725（本文は未取得）
- @29meat_ai：記事「9割が知らないOpus 5.5の性能をぶち上げるエージェント理論」。上と同じAnthropic公式記事をかみ砕いた解説
- @addyosmani：記事「How the Claude Code team does code review」。大半をAIレビューで自動化し、人間は1人まで（マージPR数2倍超・revert率40%以上減、とのこと）
- DevelopersIO（Classmethod）：「ガチで放置できる Claude Code実行環境の作り方」。auto modeで安全に無人実行する環境づくりと、承認から解放された後のレビュー負担
- @AiAircle34052：リリース前にOpus 5.5のサブエージェント5体（連打役・変な入力役・遅い回線役・ずるい人役・初見役）でアプリをわざと壊させるQA手順

## 重要な知見

- 1・2件目は同じ元記事。スライド（照合メモ）では、ポストの見出し「使わないほうがいい」と記事の題「When to fold」にずれがあると確認済み（ref:slides:139dGZvm:subagent-fold-check）。
- 無人実行とAIレビューは、人間の確認を減らす代わりに、どこで止めるかの設計が要る、という話。

## この研究室への応用

- Symphony／ループの「検品役」や「わざと壊す役」の設計の材料。
- 検品（ReviewやQA）をAIに寄せる場合の、止める条件の参考。

## 限界・未確認

- Xポスト本文は読めていない（HTTP 402）。上の数字・主張はGrok Botの要約の写しで、原文との照合は未実施。
- 3件目と4件目、5件目のURLは、レポートに書かれていない。
