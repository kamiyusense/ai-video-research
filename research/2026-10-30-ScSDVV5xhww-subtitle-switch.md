---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Uncensored AI + REA Can Reverse Engineer Anything"
description: "リバースエンジニアリング用MCPリポジトリ(REA)を、無検閲モデルとオープンソースのエージェント実行環境に組み合わせ、QuickTime互換アプリを作る手順と限界を整理した動画研究ノート。"
tags:
  - "AI技術研究室"
  - "リバースエンジニアリング支援AI"
  - "無検閲モデル"
video_id: "ScSDVV5xhww"
logical_id: "youtube:ScSDVV5xhww:research"
transcript_logical_id: "youtube:ScSDVV5xhww:transcript"
resource: "https://www.youtube.com/watch?v=ScSDVV5xhww"
canonical_url: "https://www.youtube.com/watch?v=ScSDVV5xhww"
published_at: "2026-10-12"
---

# 研究ノート：Uncensored AI + REA Can Reverse Engineer Anything

## 独自要約

配信者は、GhidraとつなぐMCPサーバ型リポジトリ「REA」を、商用モデルの拒否を避けるため無検閲モデルで動かす方法を紹介する。構成は、エージェント実行環境、無検閲モデル（ローカルまたは従量課金の中継サービス）、REAの3点。QuickTime Player互換アプリを初版約4ドル、仕上げまで追加5〜6ドルで作ったと述べる。ただし完全再現ではなく、サーバ側資源は再現できない。リポジトリ自体に新規性はなく、道具の集約が価値だという評価である。

## チャプター

- [導入：話題のREAと無検閲モデルの狙い](https://www.youtube.com/watch?v=ScSDVV5xhww&t=0s)
- [QuickTime再構築の前後デモ](https://www.youtube.com/watch?v=ScSDVV5xhww&t=38s)
- [GLM 5.2でほぼ一発生成](https://www.youtube.com/watch?v=ScSDVV5xhww&t=84s)
- [REAの仕組みの概説（Ghidra連携のMCP）](https://www.youtube.com/watch?v=ScSDVV5xhww&t=100s)
- [限界：SmartArtなど未再現部分](https://www.youtube.com/watch?v=ScSDVV5xhww&t=135s)
- [新規性の評価とガードレール強化の予想](https://www.youtube.com/watch?v=ScSDVV5xhww&t=170s)
- [3つの構成要素：実行環境・モデル・REA](https://www.youtube.com/watch?v=ScSDVV5xhww&t=198s)
- [導入手順と実行プロンプト](https://www.youtube.com/watch?v=ScSDVV5xhww&t=261s)
- [成果・所要時間・費用](https://www.youtube.com/watch?v=ScSDVV5xhww&t=322s)
- [総括と案内](https://www.youtube.com/watch?v=ScSDVV5xhww&t=367s)

## 重要な知見

1. REAはGhidraと連携するMCPサーバで、配布済みアプリの内部をエージェントに調べさせる用途と説明される（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=123s)）。
2. 配信者は、オーケストレーションに高性能モデルは不要と主張し、GLM 5.2で大半を一発生成したという（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=84s)）。
3. 精度は100%ではなく機能欠落が起こる。例として、サーバ上にある図表ライブラリは複製できないと述べる（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=150s)）。到達度は「約8割」という自己申告である（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=166s)）。
4. リポジトリは道具を一箇所に集約しただけで、革新的ではないと評価している（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=170s)）。
5. 商用モデルでも使えるが、対象によっては摩擦があり、今後ガードレールが強化されるとの予想を述べる（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=189s)）。
6. 構成は、差し替え可能なモデルを載せる実行環境、ローカルまたは中継サービス経由の無検閲モデル、REAの3点（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=198s)、[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=228s)）。
7. 中継サービスは従量課金で、数ドルから使えると説明される（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=290s)）。
8. 導入はREAのリンクと依頼文をエージェントに渡す形で、1分未満で入るという（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=300s)）。初版は20〜30分程度（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=322s)）。
9. 費用は初版約4ドル、仕上げに追加5〜6ドル（[根拠](https://www.youtube.com/watch?v=ScSDVV5xhww&t=355s)）。

## この研究室への応用

- 自作・自社所有、または利用許諾のあるバイナリの解析と互換実装の検討に、MCP＋Ghidraの構成が使えるか検証する。
- 「道具を集約してエージェントに実行へ集中させる」設計は、他のMCP・ツール束ね設計の参考になる。
- 第三者製品の複製は、著作権・利用規約・ライセンス上の問題があり得る。対象は権利的に問題のないものに限る。
- 商用モデルの安全対策を回避する目的での利用は推奨しない。拒否される場合は、正当な用途と許諾の範囲を再確認する。

## 限界・未確認

- 字幕は自動生成（英語）で、誤変換の可能性がある。固有名詞（REA、ツール名、サービス名、モデル名）は表記が揺れており、正確な名称は未確認。
- 映像は未確認で、画面上のデモや表示内容は字幕からの推測を含まない範囲でのみ扱った。
- 公式資料（リポジトリ、各サービス、モデルの仕様・価格）は未照合。外部仕様はUNKNOWN。
- 成果物の完成度、費用、所要時間、「約8割」は配信者の自己申告で、再現性は未検証。
- 法的適合性（ライセンス、利用規約、地域の法令）はUNKNOWN。
