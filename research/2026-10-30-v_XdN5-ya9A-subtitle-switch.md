---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：REA(Reverse Engineer Anything)とClaude Codeでアプリを解析し再実装する [v_XdN5-ya9A]"
description: "オープンソースの解析ツール群REAとGhidraをClaude Codeに接続し、アプリの仕組みを調べて自前コードで再実装する流れを扱う動画の研究ノート。字幕は自動生成で未検証、外部仕様は未照合。"
tags:
  - "AI技術研究室"
  - "リバースエンジニアリング"
  - "Claude Code"
  - "REA"
  - "Ghidra"
video_id: "v_XdN5-ya9A"
logical_id: "youtube:v_XdN5-ya9A:research"
transcript_logical_id: "youtube:v_XdN5-ya9A:transcript"
resource: "https://www.youtube.com/watch?v=v_XdN5-ya9A"
canonical_url: "https://www.youtube.com/watch?v=v_XdN5-ya9A"
published_at: "2026-10-23"
---

# 研究ノート：REAでアプリを解析し再実装する

## 独自要約（300字以内）

動画は、解析ツール群REAと逆コンパイラGhidraをClaude Codeに接続し、手元のアプリの仕組みを平易な言葉で説明させる手順を示す。導入は2文の指示で済むと主張する。続いて、解析で得た理解をもとに、Office類似の4アプリ・ダッシュボード・インストーラを自前コードで作った実演を紹介する。コピーではなく「理解して再実装」する法的立場を強調し、未対応機能や署名なしの制約も述べる。数値や法的主張は未照合である。

## チャプター

- [冒頭：過去のリバースエンジニアリングの例と問題提起](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=0s)
- [アプリは中身が見えない「箱」だという主張](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=35s)
- [この動画のゴール：任意のアプリをClaudeに解説させる](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=113s)
- [REAの紹介と使えるAI環境](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=152s)
- [インストール指示とMCP、診断コマンドでの自己修復](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=219s)
- [Web系アプリと機械語アプリの違い](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=297s)
- [Ghidraの位置づけ](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=336s)
- [Ghidraの導入と4つの構成要素](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=357s)
- [最初のテスト：Windows標準ファイルの解析](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=428s)
- [「理解してから再現する」ループとWebサイトのテンプレート化](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=457s)
- [自作の文書アプリを使った解析デモ](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=498s)
- [法的な注意と、どこまで近づけるかの見積もり](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=564s)
- [4アプリとスイートの構成、デザインと検証の進め方](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=604s)
- [ダッシュボードの作成](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=724s)
- [インストーラ化と動作確認](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=777s)
- [署名なしの警告と未対応機能](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=834s)
- [法的な線引きと初回解析が遅い点](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=862s)
- [まとめと視聴者への案内](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=912s)

## 重要な知見

1. REAは、ソフトウェア解析用のツールを多数束ねたオープンソースのキットとして紹介される。AIが適切なツールを選び、根拠付きで報告する構成とされる（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=152s)）。
2. 導入は、リポジトリのクローンと依存関係の導入を自然言語で依頼する形で行う。MCPはAIにツールを接続する仕組みとして説明される（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=219s)）。
3. 診断コマンドが警告を出した際、エラーをClaudeに渡して修復させる運用が示される。再起動後に新ツールが読み込まれる（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=297s)）。
4. Web技術系アプリは追加エンジンなしで読め、機械語アプリには逆コンパイラが必要という整理が語られる（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=336s)）。
5. Ghidraの導入では、必要部品の取得・改ざん確認・接続・診断再実行までをClaudeが行ったと述べられる（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=357s)）。
6. 解析結果は、各発見に証拠を付けた一覧として出力される。確証が持てない箇所は「不明」と明示されたという（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=498s)）。
7. Webサイトはレイアウトと構造のみをテンプレートとして再現し、画像・動画・ロゴは複製しない方針が述べられる（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=457s)）。
8. Office相当の再実装は、日常用途の大半には届くが機能全体の一部にとどまる、というClaudeの見積もりが紹介される（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=564s)）。
9. 各アプリは、レイアウト選択・実装・自動テスト・修正・別AIによるデザインレビューの手順で作られ、完了の証明を求める指示が重視される（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=604s)）。
10. 完成物はデスクトップアプリとしてインストーラ化され、制約（署名なし、一部ファイルの読込未対応、書式崩れ）が自己申告される（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=834s)）。
11. 法的な線引きとして、許可された範囲での学習・研究・互換目的の調査と、他者のコードの転用や保護回避を区別している（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=862s)）。
12. 初回解析は時間がかかり、固まったように見えることがあると注意される（[根拠](https://www.youtube.com/watch?v=v_XdN5-ya9A&t=900s)）。

## この研究室への応用

- 自作・許諾済みのアプリに限り、AIと解析ツールの接続で構造把握を速められるかを小規模に試す余地がある。
- 「証拠付き報告」「不確実な点の明示」「完了の証明を求める」指示設計は、研究ノート作成や検証系ワークフローにも流用できる。
- 診断コマンドの結果をAIに渡して自己修復させる運用は、環境構築の手間を減らす参考になる。
- 計画を段階化し、レイアウト案から人が選ぶ進め方は、生成物の品質管理の型として使える。

## 限界・未確認

- 映像は未確認で、字幕テキストのみを根拠にしている。画面上の操作や成果物は確認していない。
- 字幕は自動生成のため、固有名詞（ツール名・アプリ名・リポジトリ名など）に誤変換の可能性がある。
- 公式資料（REA、Ghidra、各ライブラリ）との照合は未実施。ツール数、対応範囲、導入手順、性能はUNKNOWNとする。
- 冒頭の歴史的事例、特定開発者の成果、法的解釈、Officeへの近さの割合は動画内の主張で、裏付けはUNKNOWN。
- 法的助言ではない。実際の解析は、利用規約・ライセンス・各地域の法令を別途確認する必要がある。
- 動画の最後で言及される外部コミュニティのプロンプト集は、内容を確認していない。
