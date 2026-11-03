---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Grok Bot・Orca CLI・ZernioでLinkedIn投稿を自動化する [iDwSqXC8sBQ]"
description: "Grok BotからOrca CLI経由でコーディングエージェントを起動し、LinkedIn用カルーセルPDFを生成、Zernioでレビュー付き下書きにするデモ動画の字幕ベース研究ノート。映像・公式資料は未確認。"
tags:
  - "AI技術研究室"
  - "Grok Bot / Orca CLI / Zernio によるLinkedIn投稿自動化"
  - "エージェント開発環境"
video_id: "iDwSqXC8sBQ"
logical_id: "youtube:iDwSqXC8sBQ:research"
transcript_logical_id: "youtube:iDwSqXC8sBQ:transcript"
resource: "https://www.youtube.com/watch?v=iDwSqXC8sBQ"
canonical_url: "https://www.youtube.com/watch?v=iDwSqXC8sBQ"
published_at: "2026-09-20"
---

# 研究ノート：Grok Bot・Orca CLI・Zernioで投稿を自動化

## 独自要約（300字以内）

話者はOrca（複数のコーディングエージェントを一画面で管理するADE）と、チャットで指示できる個人アシスタント型のGrok Botを組み合わせる。Grok BotがOrca CLIを通じてClaudeセッションを起動し、LinkedInカルーセル用のスライドPDFと本文を生成させる。結果は非同期に報告され、外出先からでも操作できる。最後にZernioで下書きを作り、レビューを挟んでから投稿する流れを示す。全体は単一デモで、定量的な評価は語られない。

## チャプター

- [導入：Grok BotとOrcaの紹介](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=6s)
- [OrcaはADE：複数エージェントを一つのGUIで管理](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=10s)
- [Grok BotでOrca CLIを動かす動機](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=55s)
- [Orca Mobileと中継サービスによる遠隔操作](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=119s)
- [Grok Botの位置づけ（OpenClaw系との比較）](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=159s)
- [Orca CLIの概要](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=190s)
- [デモの狙い：LinkedIn投稿の作成](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=242s)
- [Grok BotにOrcaアクセスを確認](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=277s)
- [スライド構成・モデル・CTAの指示](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=304s)
- [Orca上でセッションが起動し進捗が見える](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=426s)
- [非同期運用と並行コマンド](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=507s)
- [生成完了と結果確認](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=598s)
- [LinkedIn下書きの作成依頼](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=637s)
- [成果物（PDFと本文）の構成](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=670s)
- [スライド内容の確認](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=716s)
- [Zernioのレビューゲートとタグ付け](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=754s)

## 重要な知見

1. OrcaはプロジェクトとワークツリーごとにClaude Code等を並べて管理できるとされる。複数ターミナルの追跡負担を減らす狙い。根拠：[t=16s](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=16s)
2. Orca CLIにより、GUIなしでコーディングエージェントからOrcaを操作できると説明される。根拠：[t=190s](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=190s)
3. Orca Mobileでも遠隔操作できるが、画面が煩雑なため、話者は「依頼して返事を待つ」アシスタント型を好む。根拠：[t=119s](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=119s)
4. Grok BotはOrca CLIを橋渡しにして、指示からプロンプトを組み立てClaudeセッションへ渡す。根拠：[t=426s](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=426s)
5. 処理は非同期で、Botが進捗を監視して報告する間も別の依頼を送れる。根拠：[t=507s](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=507s)
6. 生成物は複数のPNGスライドを束ねたPDFと本文キャプションで、LinkedInのカルーセル向けと説明される。根拠：[t=670s](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=670s)
7. Zernioは直接投稿せず、レビューを挟む段階を設けると語られる。人物タグ付けも可能と述べる。根拠：[t=754s](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=754s)、[t=774s](https://www.youtube.com/watch?v=iDwSqXC8sBQ&t=774s)

## この研究室への応用

- 「依頼→非同期実行→報告→人間レビュー」の分業は、動画研究ノート作成の運用にも転用できる。
- 公開前に必ず人間の確認段階を置く設計は、外部公開物の安全策として参考になる。
- 並行エージェントの進捗を一覧する発想は、複数ジョブ管理の検討材料になる。
- 導入する場合は、各ツールの権限範囲と認証情報の扱いを事前に確認する。

## 限界・未確認

- 映像は未確認。本ノートは字幕のみに基づき、画面上の操作や表示内容は確認していない。
- 公式資料は未照合。Orca・Grok Bot・Zernioの仕様、料金、対応機能、提供状況はすべてUNKNOWN。
- 字幕は取得上「manual」とされるが、正確性は未検証。固有名詞（Grok Bot、OpenClaw、Zernio等）に自動字幕由来の誤変換が残る可能性がある。字幕内の表記ゆれ（例：Gropbot、Zeneo、OrCAD）は同一対象と推測したにすぎない。
- 使用モデル名や所要時間の詳細、生成物の品質評価は客観的に確認できない。
- 実際にLinkedInへ投稿したかどうかは字幕から不明。
- 話者による個人的な比較（Android／iPhoneの比喩など）は主観であり、検証されていない。
