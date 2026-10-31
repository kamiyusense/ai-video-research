---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "【参考資料】Xブックマーク：トークン・使用量の節約"
description: "使用量を食う習慣を見つけるプロンプトと、トークン圧縮OSSの2件。"
logical_id: "ref:x-bookmarks-202610:token-saving"
source_kind: "X_POST_COLLECTION"
source_tier: "SECONDARY_SUMMARY"
content_status: "SUMMARY_ONLY"
acquisition_method: "相棒がGrok Botで作った分類レポート（2026-10-29）を元に、各URLを公開API（api.fxtwitter.com）と検索で照合、2026-10-30。2026-10-31 にGrok Botの元投稿チェック（読み取りのみ）を受け、Claudeが api.fxtwitter.com で原文を再取得して照合・修正"
checked_at: "2026-10-31"
posted_at_timezone: "JST"
tags: ["参考資料", "Xブックマーク", "トークン", "使用量", "圧縮", "セッションログ"]
items:
  - author: "@Voxyz_ai"
    url: "https://x.com/Voxyz_ai/status/2114416707385073819"
    link_status: "CONFIRMED"
    posted_at: "2026-10-26"
  - author: "@liambraus"
    url: "https://x.com/liambraus/status/2114432797649584611"
    link_status: "CONFIRMED"
    posted_at: "2026-10-26"
---

# Xブックマーク：トークン・使用量の節約

## まとめ
使用量を食う習慣を見つけるプロンプトと、トークン圧縮OSSの2件。

## 1件ずつ
### @Voxyz_ai
- URL：https://x.com/Voxyz_ai/status/2114416707385073819（CONFIRMED）
- 投稿日：2026-10-26
- 要約：直近7日のセッションログから使用量を一番食う習慣トップ3を見つけ、防ぐルールをCLAUDE.md/AGENTS.mdに足すプロンプト（Codex版あり）。プロンプト自体に「承認するまで何も変えない」「生のログを読まず記録済みのトークン数を集計」「秘密を表示しない」という安全策が入っている。似た話として @AiAircle34052 の x.com/AiAircle34052/status/2114605697463947517 （7日分のログから分析ダッシュボードを作るプロンプトの紹介）がある。

### @liambraus
- URL：https://x.com/liambraus/status/2114432797649584611（CONFIRMED）
- 投稿日：2026-10-26
- 要約：OSS「Headroom」：エージェントとLLMの間でJSON・コード・ログを圧縮しトークンを最大95%削減（`headroom wrap claude`）。リポジトリ：https://github.com/headroomlabs-ai/headroom （リプライに記載。リプライ自体は未取得だが、同じURLを @cnemalek も投稿している）。スペイン語。数字は投稿者の主張で未検証。

## 限界
- 要約の大半はGrok Botの分類レポート（二次情報）。CONFIRMED は投稿本文を取得して内容一致を見たもの、CANDIDATE は似た投稿は見つかったが一致を断定できないもの、UNKNOWN はURLが見つからないもの。
- 投稿日（posted_at）は日本時間（JST）。
- 記事（X Articles）の本文は読んでいない。数字はすべて投稿者側の主張。
