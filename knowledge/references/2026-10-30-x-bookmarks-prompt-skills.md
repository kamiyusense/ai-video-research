---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "【参考資料】Xブックマーク：プロンプト術・Skills（作り方と安全性）"
description: "プロンプトを書き直させる技、Skillを自作させる方法、公開Skillの脆弱性調査の3件。"
logical_id: "ref:x-bookmarks-202610:prompt-skills"
source_kind: "X_POST_COLLECTION"
source_tier: "SECONDARY_SUMMARY"
content_status: "SUMMARY_ONLY"
acquisition_method: "相棒がGrok Botで作った分類レポート（2026-10-29）を元に、各URLを公開API（api.fxtwitter.com）と検索で照合、2026-10-30。2026-10-31 にGrok Botの元投稿チェック（読み取りのみ）を受け、Claudeが api.fxtwitter.com で原文を再取得して照合・修正"
checked_at: "2026-10-31"
posted_at_timezone: "JST"
tags: ["参考資料", "Xブックマーク", "プロンプト", "Skill", "Skill自作", "脆弱性", "SkillSpector"]
items:
  - author: "@Adamaestr0_"
    url: "https://x.com/Adamaestr0_/status/2114469090979147966"
    link_status: "CONFIRMED"
    posted_at: "2026-10-26"
  - author: "@cnemalek"
    url: "https://x.com/cnemalek/status/2114464225431109691"
    link_status: "CONFIRMED"
    posted_at: "2026-10-26"
  - author: "@bottopia_studio"
    url: "https://x.com/bottopia_studio/status/2114536452386369544"
    link_status: "CONFIRMED"
    posted_at: "2026-10-26"
---

# Xブックマーク：プロンプト術・Skills（作り方と安全性）

## まとめ
プロンプトを書き直させる技、Skillを自作させる方法、公開Skillの脆弱性調査の3件。

## 1件ずつ
### @Adamaestr0_
- URL：https://x.com/Adamaestr0_/status/2114469090979147966（CONFIRMED）
- 投稿日：2026-10-26
- 要約：「Anthropicのエンジニアが教えた4行」：送信前に、専門家ならやるが自分は頼んでいないこと・素材・手法と道具・正しさを示すものの4行を足して、プロンプトを書き直させる技。スペイン語。元ネタは Felix Rieseberg（Claude担当のエンジニアリードと自己紹介）の投稿 https://x.com/felixrieseberg/status/2110023283169247623 とそのチュートリアル。

### @cnemalek
- URL：https://x.com/cnemalek/status/2114464225431109691（CONFIRMED。プロンプト本体は続きの https://x.com/cnemalek/status/2114464231240224944 ）
- 投稿日：2026-10-26
- 要約：繰り返しの作業を見つけてClaude Codeに自分でSkillを作らせ、試して直し、修正から学ばせるプロンプト。アラビア語。プロンプトには「質問は最大6個→表で確認→上位5作業をSkill化→実例で試す→修正は差分で提案し承認後に適用→CHANGELOG.md」と、「送信・公開・削除・支払いをするSkillは承認なしに作らない、鍵をSkillに入れない」という決まりが入っている（Grok Botの照合レポートより）。

### @bottopia_studio
- URL：https://x.com/bottopia_studio/status/2114536452386369544（CONFIRMED）
- 投稿日：2026-10-26
- 要約：公開エージェントSkill 3.1万件の調査で26.1%に脆弱性、5.2%に悪意の疑い。NVIDIAの無料チェッカー「SkillSpector」の紹介。韓国語。一番多いのは情報を外へ持ち出す型（13.3%）、次が勝手に権限を広げる型（11.8%）、スクリプト入りのSkillは文章だけのSkillより2.12倍危険。SkillSpector（NVIDIA製・無料）は投稿者の記載で、一次情報は未確認。調査した研究陣の名前は投稿に無い。

## 限界
- 要約の大半はGrok Botの分類レポート（二次情報）。CONFIRMED は投稿本文を取得して内容一致を見たもの、CANDIDATE は似た投稿は見つかったが一致を断定できないもの、UNKNOWN はURLが見つからないもの。
- 投稿日（posted_at）は日本時間（JST）。
- 記事（X Articles）の本文は読んでいない。数字はすべて投稿者側の主張。
