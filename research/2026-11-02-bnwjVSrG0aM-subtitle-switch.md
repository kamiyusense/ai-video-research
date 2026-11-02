---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：GeminiとGemini Notebookの連携とインデックスノートブックの作り方 [bnwjVSrG0aM]"
description: "Geminiアプリからノートブックを検索・作成・更新できる連携アプリ化の機能範囲と限界、タイトル判断による検索漏れを防ぐ「インデックスノートブック」設計を、字幕のみから整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "Gemini Notebook連携"
  - "インデックスノートブック"
video_id: "bnwjVSrG0aM"
logical_id: "youtube:bnwjVSrG0aM:research"
transcript_logical_id: "youtube:bnwjVSrG0aM:transcript"
resource: "https://www.youtube.com/watch?v=bnwjVSrG0aM"
canonical_url: "https://www.youtube.com/watch?v=bnwjVSrG0aM"
published_at: "2026-10-27"
---

# 研究ノート：Gemini×Gemini Notebook連携とインデックスノートブック

## 独自要約

2026年10月23日の更新で、Geminiのチャットからノートブックの横断検索、内容確認、新規作成、テキストソースの追加・更新ができるようになったと、話者は説明している。ただ連携しただけでは、AIがタイトルだけで対象を絞り、表層的な部分だけを拾い、勝手に要約するという検索漏れが起きるという。対策として、全ノートブックの目次と守るべきルールを書いた「インデックスノートブック」を置く方法を、話者の実演つきで紹介している。

## チャプター

- 導入・テーマ提示：[0s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=0s)
- 待望の機能と従来の不便さ：[30s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=30s)
- 連携の4段階の進化（2026年1月〜10月）：[164s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=164s)
- 連携でできる4つのこと：[222s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=222s)
- 横断検索の実演：[314s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=314s)
- 特定ノートブック指定とソース確認：[380s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=380s)
- ノートブックの作成と育成（実演）：[538s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=538s)
- できないこと（スタジオ機能・原本書換）：[674s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=674s)
- 全中身を暗記しない挙動：[746s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=746s)
- 3つのサボり現象：[878s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=878s)
- インデックス有無による結果比較：[1042s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1042s)
- インデックスノートブックとは：[1103s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1103s)
- システムルールズの書き方：[1256s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1256s)
- Geminiに目次を自動生成させる手順：[1424s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1424s)
- まとめ：[1565s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1565s)
- 告知（メンバーシップ）・締め：[1693s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1693s)

## 重要な知見

1. 話者によると、Geminiアプリの連携アプリとしてノートブックが追加され、個人・法人のGoogleアカウントで提供が始まっている。根拠：[90s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=90s)
2. できることは、一覧取得と横断検索、特定ノートブックの検索とソース確認、作成・名称変更・削除、ソース追加とテキストソース更新の4つ。根拠：[222s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=222s)
3. 更新できるのはMDなどのテキストソースで、Googleドライブ経由のWord・PDFなど原本が別にあるものは直接編集できないと説明している。根拠：[246s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=246s)
4. チャットでの議論や横断検索の結果を、そのまま新しいノートブックとして保存できる。実演では作成直後はソース0件で、後から4件入った。根拠：[538s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=538s)
5. 音声解説・スライド・マインドマップなどのスタジオ機能はGeminiからは指示できないと話者は述べている。根拠：[674s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=674s)
6. Driveから読み込んだPDFやドキュメントの原本は、連携オンの状態では書き換えを拒否されたという話者の観察。根拠：[699s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=699s)
7. 話者の説明では、Geminiはまずノートブックのタイトル一覧を見て関連しそうな数冊に絞り、その範囲だけを部分検索する。根拠：[746s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=746s)
8. 準備なしの横断検索で起きる問題として、タイトル偏重による検索漏れ（[897s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=897s)）、冒頭やまとめ表など表層チャンクの偏重（[940s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=940s)）、一部だけで全体と見なす勝手な要約（[967s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=967s)）の3つを挙げている。
9. 同じ質問で、インデックスなしでは拾ったソースが4件にとどまり、ありの場合は網羅性が大きく違ったと実演で比較している。根拠：[1042s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1042s)
10. インデックスの発想は、話者自身がNotebookLM時代に試行錯誤で編み出したもの。AI開発での階層型RAGやセマンティックルーティングに近いと後から知ったという。根拠：[1169s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1169s)
11. 全ノートブックをカテゴリー別に整理し、ソース名・件数・知見を載せた総合目次を1冊のノートブックにする。根拠：[1103s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1103s)
12. 目次ソースのタイトルに大文字で「システム」を意味する語を入れ、冒頭にルールを書く。ルールは、タイトルだけで判断せず目次から対象を特定することと、要約せず原文の粒度を保つこと。後者は任意で、要約を許容するなら不要と話者は述べている。根拠：[1256s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1256s)、[1270s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1270s)
13. 目次は手作業ではなくGeminiに作らせる。一覧取得、20〜30冊ずつの確認、カテゴリー分類、カタログ作成、ルール明記、ノートブック登録を依頼する。根拠：[1424s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1424s)
14. ノートブックが増えたら、目次がテキストソースであることを利用して更新を依頼する。根拠：[1544s](https://www.youtube.com/watch?v=bnwjVSrG0aM&t=1544s)

## この研究室への応用

- 複数のノートブックを知識ベースにする場合、連携を有効にする前に、目次役のインデックスノートブックを設計する。
- 目次ソースの冒頭にシステムルールズを置く設計は、プロジェクトの指示書やインデックス文書を置く運用と共通するため、他のAI環境でも試せる。
- 検証案として、同じ質問をインデックス有無で比較し、拾われたソース数と情報の深さを記録する。
- 目次はテキストソースにして、ノートブックの増減のたびに更新する運用にする。
- 原本がDrive上のWord・PDFのものは、編集可能なテキスト版を併置する案が考えられる（動画の主張ではなく研究室側の推測）。

## 限界・未確認

- 映像は未確認で、字幕のみを根拠にしている。画面上の操作や表示は確認していない。
- 自動字幕のため誤変換の可能性がある。例えば冊数は「76冊」「766冊」「70冊以上」と表記が揺れており、正確な数は不明。製品名の表記も揺れている。
- Googleの公式資料・リリースノートとは未照合。日付（2026年1月、4月、7月16日、10月23日）、名称変更、提供範囲は話者の説明のままで、外部仕様の正否はUNKNOWN。
- 「ほぼ完璧」「100%近い精度」といった効果は話者の経験に基づく主張で、再現性や定量的な根拠は動画内で示されていない。
- タイトルだけで絞る挙動や3つのサボり現象は、内部実装の確認ではなく話者の観察と説明であり、内部仕様はUNKNOWN。
- ノートブック数やソース数の上限、対象プラン・地域・料金の条件はUNKNOWN。
- 動画の後半にメンバーシップの告知があるが、本研究には使っていない。
