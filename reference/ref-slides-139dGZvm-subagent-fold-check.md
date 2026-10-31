---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "参考ノート：サブエージェントは、いつたたむか（照合メモ 2026/10/28）"
description: "Xポスト『サブエージェントは使わないほうがいい』と、元になったAnthropic記事『When to fold subagents into your main agent loop』を突き合わせたスライド。ポストと記事のずれ、記事の3条件、評価セット先行の手順を整理している。"
tags:
  - "AI技術研究室"
  - "参考資料"
  - "サブエージェント"
logical_id: "ref:slides:139dGZvm:subagent-fold-check"
source_kind: "google_slides"
source_tier: "SECONDARY_SUMMARY"
content_status: "READ_VIA_TOOL_SUMMARY"
acquired_at: "2026-10-30"
acquisition_method: "公開Googleスライドを取得ツールでテキスト化（要約を通した読み）"
resource: "https://docs.google.com/presentation/d/139dGZvm-_j-uxk1VThjjq9pOcc7vvWbwcdZ0GqFyIfA/edit"
canonical_url: "https://docs.google.com/presentation/d/139dGZvm-_j-uxk1VThjjq9pOcc7vvWbwcdZ0GqFyIfA/edit"
published_at: "2026-10-28"
related_records:
  - target_id: "ref:x-bookmarks:2026-10-29:agent-design"
    relation: "COMPLEMENTS"
    note: "ブックマーク1・2件目の元記事を一次側から照合した内容"
---

# サブエージェントは、いつたたむか（照合メモ）

## 独自要約

ポスト（@makaneko_AI、2026-10-26）の「サブエージェントは使わないほうがいい」は、元記事（Anthropic Applied AIチーム、claude.com、2026-10-22「Building agents: When to fold subagents into your main agent loop」）の主旨と食い違う。記事は「全部1本」ではなく、3つの設計（1つのプロンプト／サブエージェント／1本のループ＋必要時に読み込むスキル）を比べ、3つ目が品質で上回ることが多く、コスト・待ち時間も低いことが多いとする。ただし「サブエージェントにも居場所がある」として、使うべき3条件を挙げる。

## 内容の流れ

- きっかけ：ポストの見出しと、メイン1本にまとめる設計の推奨
- 元記事：比べた3つの設計、大きな組織で起きる5つの失敗（文脈の受け渡し・乱立・寄せ集めプロンプト・局所的な評価・待ち時間）
- それでもサブエージェントを使う条件：①1本が文脈の膨らみで性能を落とす、②並列作業を、終わったら捨てられる新しい文脈で進めたい、③1本ではツールを選びきれない、または指示が食い違う
- 分け方は「文脈」で決める。強いのは検証・並列作業・権限の切り分け
- たたみ方は、先に比べる仕組み（評価セット10例ほど）を作ってから、少しずつたたみ、点が下がるなら残す
- 紹介された道具：single-agent-loop-kit（Apache-2.0、161 stars〔2026-10-28時点〕、「Reference implementation. Not maintained」）

## 重要な知見

- 見出しと記事の主旨がずれるポストは、一次記事で照合する。
- 畳む前に比べる。畳んで速くなっても、通っていた処理が壊れることがある。
- 点が下がるなら、そのサブエージェントは残す。

## この研究室への応用

- 検証役（test-reviewer）や、全ファイルを並列に読んで捨てる調査役は「残す側」になりそう（スライド内の推測）。
- 評価セットを先に作る手順は、Symphony／ループの変更前後の比較にも使える。

## 限界・未確認

- 記事とリポジトリは、取得ツールの要約を通して読んだため、細かい言い回しは原文で確かめる必要がある。
- 「手元への当てはめ」はスライド作成者の推測。
