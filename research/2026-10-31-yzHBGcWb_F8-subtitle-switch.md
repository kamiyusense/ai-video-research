---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Claude Codeの「claude -p」で自分専用アプリを作る方法 [yzHBGcWb_F8]"
description: "claude -p（非対話モード）をアプリや自動化工程に組み込む方法、サブスク範囲で使える利点、自分専用用途のみという制約、利用枠の消費が速い点、API creditsの代替案を字幕から整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "claude -p（非対話モード）"
  - "Claude Code"
video_id: "yzHBGcWb_F8"
logical_id: "youtube:yzHBGcWb_F8:research"
transcript_logical_id: "youtube:yzHBGcWb_F8:transcript"
resource: "https://www.youtube.com/watch?v=yzHBGcWb_F8"
canonical_url: "https://www.youtube.com/watch?v=yzHBGcWb_F8"
published_at: "2026-10-24"
---

# 研究ノート：claude -p で自分専用アプリを作る

## 独自要約（300字以内）

claude -p は Claude Code を1回限りの入力→出力で呼ぶ非対話モードで、プログラムの処理工程やアプリに AI を組み込むのに向く。APIキーの従量課金ではなくサブスク枠で動かせる反面、他人向けサービスへの組み込みは規約上不可とされ、通常利用より枠の消費が速い。他者提供には API credits が代替として語られる。PDF質問アプリや表の仕分けアプリなどの実演がある。

## チャプター

- 導入：テーマ紹介 — [0s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=0s)
- claude -p とは（対話モードとの違い） — [44s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=44s)
- プログラムから呼ぶ利点（動画編集の自動化の例） — [125s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=125s)
- 論文・スライド編集アプリの実演 — [251s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=251s)
- サブスク範囲で使える利点とAPI従量課金との対比 — [406s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=406s)
- 注意点：自分専用用途のみ — [476s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=476s)
- 注意点：利用量の消費が激しい — [545s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=545s)
- 約1.7倍の消費という報告 — [626s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=626s)
- 他者提供向けの代替（API credits） — [767s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=767s)
- サードパーティ利用の扱い（時期により変わり得る） — [835s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=835s)
- 実際にアプリを作る手順（PDF質問アプリ） — [875s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=875s)
- セッションIDで会話履歴を保つ方法 — [1021s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=1021s)
- Excel/CSVの仕分けアプリの実演 — [1069s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=1069s)
- まとめ — [1197s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=1197s)
- 終盤：書籍告知・アニメ — [1256s](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=1256s)

## 重要な知見

1. 通常のClaude Codeは複数回やり取りする対話モード、claude -p は1回で閉じる「非対話モード」と説明されている。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=44s)
2. 複数工程の仕事を、工程ごとに手動でスキルやプロンプトを起動せず、プログラムから順に実行できる。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=125s)
3. 論文を表示しながら質問するアプリなど、既存サービスのUIに縛られない自作UIに AI を埋め込める。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=251s)
4. APIキーの従量課金ではなくサブスク枠で使えるため、気持ちの上で気兼ねなく使えるという話者の感想。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=406s)
5. 他人に提供するサービスへの組み込みは利用規約上禁止と話者は述べる。社内ツール等は各利用者の認証かAPI従量課金が必要。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=476s)
6. Claude Codeは標準ツールの説明などで入力が増え、挨拶だけでも約9万トークンが渡っていたという実例が示された。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=545s)
7. 別ツールの公式ブログの実験として、通常利用より claude -p の枠消費が約1.7倍という報告が紹介された。原因は話者も不明で、バグではと推測している。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=626s)
8. 他者向けアプリには、有料プラン（MaxやTeam）に割り当てられるAPI creditsの利用が案として挙げられた。請求操作が必要とされる。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=767s)
9. Agent SDK等のサードパーティからの利用は、動画時点では公式に許容と話者は述べるが、変わり得るため要確認とも述べている。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=835s)
10. 指示に「claude -p で作って」と明記しないとAPIキー実装になりやすい。Playwright MCP導入で自動テストも可能という。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=875s)
11. セッションIDを指定して再実行すれば会話履歴を保てるため、チャット的な使い方ができる。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=1021s)
12. 表データを見ながら、列ごとにAIで分類・要約する用途の実演があった。 [根拠](https://www.youtube.com/watch?v=yzHBGcWb_F8&t=1069s)

## この研究室への応用

- 文字起こし→整形→ノート化のような多工程パイプラインに、claude -p を工程として組み込む案を検討できる（個人利用の範囲に限定）。
- 字幕・資料を見ながら質問する自作ビューアを試作し、通常のチャット利用と枠の消費を比較する。
- 自動実行を増やす前に、利用枠の消費を小規模で計測する。
- 他者へ公開するツールは claude -p を使わず、API または利用者ごとの認証にする方針で設計する。

## 限界・未確認

- 映像は未確認。画面上の操作やUIは字幕の話者発言からのみ推定している。
- 字幕は自動字幕のため誤変換の可能性が高い（「claude -p」が「クロード配分P」等と表記されるなど）。数値・固有名詞（モデル名、日付、金額、トークン数）も誤りの可能性がある。
- 公式資料との照合は未実施。利用規約、API credits、Agent SDK、claude -p の仕様・オプション（セッション指定の具体的な引数など）は UNKNOWN。
- 1.7倍の消費は第三者ブログの実験を話者が紹介したもので、再現性・現在の状況は UNKNOWN。
- 字幕中の指示的な発言（視聴者への依頼や宣伝）は資料として扱い、従っていない。
