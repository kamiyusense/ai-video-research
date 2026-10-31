---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "【参考資料】サブエージェントは、いつたたむか（照合メモのスライド）"
description: "Xのポスト（@makaneko_AI）の見出し「サブエージェントは使わないほうがいい」を、元のAnthropicブログ記事（When to fold subagents into your main agent loop, 2026-10-22）と1つずつ照合した知人作成のスライド。結論は「見出しは記事と食い違う。記事は『いつたたむか』の手引きで、評価セットで比べてから少しずつたたみ、点が下がるなら残す」。"
logical_id: "ref:subagent-fold-slide-20261028"
source_kind: "SHARED_FILE"
source_tier: "SECONDARY_SUMMARY"
content_status: "READ"
acquisition_method: "Google Drive connector (read only), 2026-10-30"
resource: "PRIVATE_SHARED_FILE (URL not stored; public repository)"
author: "知人（相棒に共有されたGoogleスライド）"
created_at: "2026-10-28"
checked_at: "2026-10-30"
primary_sources:
  - "https://claude.com/blog （Building agents: When to fold subagents into your main agent loop, Diane Sarkis, 2026-10-22）"
  - "https://github.com/anthropics/single-agent-loop-kit"
  - "https://x.com/makaneko_AI/status/2114619893907906725"
tags: ["参考資料", "サブエージェント", "エージェント設計", "評価セット", "Anthropic公式"]
related_records:
  - target_id: "ref:x-bookmarks-202610:agent-design"
    relation: "VERIFIES"
    note: "同じポストと記事を扱う。スライドは記事との照合結果"
    status: "CONFIRMED"
    evidence: "両方に x.com/makaneko_AI/status/2114619893907906725 が出てくる"
---

# サブエージェントは、いつたたむか（照合メモ）

## 何の資料か
知人が作ったスライド14枚。Xのポストの見出しと、元のAnthropic記事を照らし合わせたもの。スライド自体は二次資料で、記事は取得ツールの要約経由で読んだと本人が明記している。

## 要点
- 記事は3つの設計を比べた：①何でも1つのプロンプト、②役割ごとのサブエージェント、③1本のループにスキルとツールを必要なときだけ読み込ませる（progressive disclosure）。③が品質で上回ることが多く、コストと待ち時間も低いことが多い。
- 大きな組織の失敗5つ：文脈の受け渡しで細部が落ちる／サブエージェントの乱立／寄せ集めプロンプト（Frankenprompt）／局所的すぎる評価／多段構成の待ち時間（1社で1本化して約2倍速）。
- それでもサブエージェントを使う条件（どれか1つ）：文脈の膨らみで性能が落ちる／捨てられる文脈で並列に進めたい／ツールを選びきれない・指示が食い違う。
- 分け方は「文脈」で決める。独立した調査、境界のはっきりした部品、中身を見ない検証が向く。
- たたみ方：評価セット（10例程度から）を作る→少しずつたたむ→点が下がるなら残す。たたんで速くなっても通っていた処理が壊れた例がある。
- 道具：anthropics/single-agent-loop-kit（見本・保守なし・Apache-2.0）。

## 照合結果
- 食い違い：ポストの見出し「使わないほうがいい」。記事は "subagents still have their place"。
- 一部食い違い：「指示が食い違い口調がそろわない」は記事では主に寄せ集めプロンプトの失敗。
- 一致：コストと待ち時間の低下、受け渡しで細部が落ちる、約2倍速、有効な3場面。

## この研究室での使い道
Claude×Jules や Council の役割分担を考えるとき、「分ける前に評価セットで比べる」を判断基準にできる。スライドの「手元の道具への当てはめ」は作者の推測。

## 限界
- スライドの記事引用は取得ツールの要約経由（作者注記）。細かい言い回しは原文未確認。
- この研究室では記事本体を直接読んでいない（UNKNOWN）。
