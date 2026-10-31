---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "【参考資料】Xブックマーク：MCP・プラグイン・ツール紹介"
description: "Claude Code向けMCPサーバーのおすすめと、Obsidian用AIプラグインの更新まとめの2件。"
logical_id: "ref:x-bookmarks-202610:mcp-plugins"
source_kind: "X_POST_COLLECTION"
source_tier: "SECONDARY_SUMMARY"
content_status: "SUMMARY_ONLY"
acquisition_method: "相棒がGrok Botで作った分類レポート（2026-10-29）を元に、各URLを公開API（api.fxtwitter.com）と検索で照合、2026-10-30。2026-10-31 にGrok Botの元投稿チェック（読み取りのみ）を受け、Claudeが api.fxtwitter.com で原文を再取得して照合・修正"
checked_at: "2026-10-31"
posted_at_timezone: "JST"
tags: ["参考資料", "Xブックマーク", "MCP", "プラグイン", "Obsidian", "Claudian", "検証手段"]
items:
  - author: "@kimuai08"
    url: "https://x.com/kimuai08/status/2082428727401869753"
    link_status: "CONFIRMED"
    posted_at: "2026-07-29"
    note: "引用ポスト https://x.com/kimuai08/status/2114563306430374375 （2026-10-26）もあり、どちらをブックマークしたかは UNKNOWN"
  - author: "@minami_freeup"
    url: "https://x.com/minami_freeup/status/2114465795287982390"
    link_status: "CONFIRMED"
    posted_at: "2026-10-26"
---

# Xブックマーク：MCP・プラグイン・ツール紹介

## まとめ
Claude Code向けMCPサーバーのおすすめと、Obsidian用AIプラグインの更新まとめの2件。

## 1件ずつ
### @kimuai08
- URL：https://x.com/kimuai08/status/2082428727401869753（CONFIRMED。2026-10-26 の引用ポスト x.com/kimuai08/status/2114563306430374375 もあり、どちらをブックマークしたかは UNKNOWN）
- 投稿日：2026-07-29
- 要約：X記事「Claude Code生みの親『ボリス』がオススメする最強のMCPサーバー8選」：Context7、Playwright、Figma、Linear、Sentry、Cloudflare、Stripe、GitHub。題名は「ボリスがオススメ」だが、8つを選んだのは記事の書き手で、選定基準は「提供元の公式」「初心者でも効果を体感しやすい」「ボリス（Boris Cherny）の3原則のどれかを実装できる」。3原則は、検証手段を渡す／1日1回以上の作業は仕組みにする／外部ツールを作業面に持ち込む。ボリス本人がWeb作業で使うのはPlaywright MCPではなくClaude Codeのブラウザ拡張、と記事内に書かれている。MCPで書き込み・削除まで一気に許可すると事故る、という注意もある。

### @minami_freeup
- URL：https://x.com/minami_freeup/status/2114465795287982390（CONFIRMED）
- 投稿日：2026-10-26
- 要約：X記事「Obsidianの中でAIが使えるプラグインClaudianの進化がすごい！」：半年で約70回のアップデートを3点にまとめたもの。①AIを選べるようになった（Codexなど。8月からClaude無しでも使える）②画面が作業場になった（左に会話一覧とファイル、右にチャット）③前の続きから頼める（`[[ ]]`でメモ指定、`@`で過去の会話、スキル同期、作業中の割り込み指示）。

## 限界
- 要約の大半はGrok Botの分類レポート（二次情報）。CONFIRMED は投稿本文を取得して内容一致を見たもの、CANDIDATE は似た投稿は見つかったが一致を断定できないもの、UNKNOWN はURLが見つからないもの。
- 投稿日（posted_at）は日本時間（JST）。
- X記事2本（@kimuai08・@minami_freeup）は、Claudeが api.fxtwitter.com で本文を取得して照合した。数字はすべて投稿者側の主張。
