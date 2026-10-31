---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "参考ノート：トークン・使用量の節約（Xブックマーク2件）"
description: "使用量を食う習慣を見つけて防ぐプロンプトと、トークンを圧縮するOSS『Headroom』の紹介。Grok Botの要約の写し。本文は未確認。"
tags:
  - "AI技術研究室"
  - "参考資料"
  - "使用量節約"
logical_id: "ref:x-bookmarks:2026-10-29:token-saving"
source_kind: "x_post_collection"
source_tier: "SECONDARY_SUMMARY"
source_made_by: "Grok Bot"
content_status: "SUMMARY_ONLY"
acquired_at: "2026-10-30"
acquisition_method: "相棒がチャットに貼ったレポートの転記"
resource: "UNKNOWN"
canonical_url: "UNKNOWN"
---

# トークン・使用量の節約（2件）

## 独自要約

直近のセッションログから、使用量を一番食う習慣のトップ3を見つけ、防ぐ規則をCLAUDE.md／AGENTS.mdに足すプロンプトと、エージェントとLLMの間でJSON・コード・ログを圧縮してトークンを減らすOSS「Headroom」の2件。

## 項目

- @Voxyz_ai：直近7日のセッションログから使用量を一番食う習慣トップ3を見つけ、防ぐルールをCLAUDE.md／AGENTS.mdに足すプロンプト（Codex版もあり）
- @liambraus：OSS「Headroom」の紹介。エージェントとLLMの間でJSON・コード・ログを圧縮し、トークンを最大95%削減（`headroom wrap claude`）

## 重要な知見

- 使用量を食う習慣は、自分のログから見つけて、規則にして固定する。
- 圧縮のOSSは「最大95%」という数字が宣伝側のもの。条件つきの可能性が高い。

## この研究室への応用

- Symphony／ループのトークン使用量の節約策の候補（先に自分のログで食う習慣を見つける）。
- Headroomは導入前に、自分の環境で効果とセキュリティ（途中でログを通す点）を確かめる必要がある。

## 限界・未確認

- 「最大95%」はGrok Botの写し。実測ではない。ポスト本文は未取得（HTTP 402）。
