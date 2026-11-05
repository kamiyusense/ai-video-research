---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "開ループ・閉ループ、内ループ・外ループによるAI自動化の研究ノート [RzE2chSYAN4]"
description: "AI自動化を、評価の有無(開/閉)と起動主体(内/外)の2軸で整理した動画の研究ノート。使い分けの判断基準と外ループ設計の3要点を、自動字幕に基づき要約。"
tags:
  - "AI技術研究室"
  - "AI自動化のループ設計"
video_id: "RzE2chSYAN4"
logical_id: "youtube:RzE2chSYAN4:research"
transcript_logical_id: "youtube:RzE2chSYAN4:transcript"
resource: "https://www.youtube.com/watch?v=RzE2chSYAN4"
canonical_url: "https://www.youtube.com/watch?v=RzE2chSYAN4"
published_at: "2026-11-04"
---

# 研究ノート：開/閉ループ・内/外ループ

## 独自要約

AIに毎回指示を出す運用から、AIが自律的に動く仕組みの設計へ移る考え方を扱う。結果を次の行動へ反映するか(開ループ/閉ループ)と、AI自身の反復か外部からの起動か(内ループ/外ループ)の2軸で整理し、4通りの組み合わせを示す。どれが優れるかではなくタスク性質で選ぶ点が主張。外ループは起動・停止・引き継ぎの3点で設計する。

## チャプター

- [開始 7s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=7s)：導入。4つのループを使い分ける狙い
- [開始 60s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=60s)：基本の考え方と「8つの原則」への言及
- [開始 93s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=93s)：開ループと閉ループの違い(ブログ記事の例)
- [開始 190s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=190s)：閉ループが常に最適とは限らない理由
- [開始 308s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=308s)：内ループと外ループの違い
- [開始 377s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=377s)：外ループの起動方式①定期実行
- [開始 417s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=417s)：外ループの起動方式②イベント監視(Webhook)
- [開始 493s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=493s)：外ループが必要なタスク/不要なタスク
- [開始 561s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=561s)：外ループ設計の3つのコツ
- [開始 668s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=668s)：4ループの組み合わせ(2×2)
- [開始 758s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=758s)：まとめ、失敗談、特典の案内
- [開始 826s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=826s)：勉強会の告知
- [開始 849s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=849s)：チャンネル方針

## 重要な知見

1. 開ループは結果を次の行動に反映せず、閉ループは評価して反映する。話者の事例では、別のAIが下書きを採点し基準未満なら書き直させる。[根拠 93s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=93s)
2. 閉ループ導入の判断軸は、評価基準を設定できるか、有効なフィードバックができるか、効果とコストが見合うかの3点。市場に出さないと良し悪しが分からないタスクは、まず開ループで出す方がよいとされる。[根拠 190s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=190s)
3. 閉ループは具体的な改善指示を返せないと同じ失敗を繰り返し、無限ループやコスト増になり得ると述べられる。[根拠 222s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=222s)
4. 内ループはAI自身の実行中の反復、外ループは外側の仕組みがAIを起動する構造。[根拠 308s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=308s)
5. 外ループの起動は定期実行とイベント監視の2種類。ツールの機能名は字幕上で不明瞭。[根拠 367s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=367s)
6. イベント監視の例として、エラー監視ツールの通知をWebhookで受け、AIに原因調査と要否判定をさせる運用が語られる。[根拠 436s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=436s)
7. 外ループは、同種の仕事が繰り返し発生する場合に有効。その都度作る営業資料のような単発作業には不要とされる。[根拠 493s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=493s)
8. 外ループ設計の3要点は、起動タイミング(多発時のまとめ処理や回数制限)、停止条件(回数・費用上限、人間の承認)、引き継ぎ先(進捗や課題をファイルに残す)。[根拠 561s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=561s)
9. 内外それぞれを開/閉にできるため4通りの組み合わせがあり、全部を閉ループにすることが重要ではないとされる。[根拠 668s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=668s)
10. 話者自身、閉ループを欲張って評価と修正が止まらなくなった経験を語る。[根拠 798s](https://www.youtube.com/watch?v=RzE2chSYAN4&t=798s)

## この研究室への応用

- 定型の調査・レポート作成は、定期実行の外ループ候補として検討できる。
- 自動化の前に、評価基準と改善指示を書けるかを確認し、書けなければ開ループから始める。
- 外ループには、反復回数・費用の上限、人間承認の要否、進捗記録ファイルをあらかじめ設ける。
- 各自動化を「内=開/閉」「外=開/閉」の2×2で分類して記録する。

## 限界・未確認

- 映像は未確認。字幕のみを根拠としており、画面上の図や資料は反映していない。
- 字幕は自動生成で、誤変換の可能性がある(例：用語や固有名詞の一部が不明瞭)。transcript_statusはUNVERIFIED。
- 公式資料との照合は未実施。
- 外部サービス・各ツールの機能名や仕様(定期実行機能、Webhook連携、エラー監視ツール)：UNKNOWN。
- 「8つの原則」の全項目は字幕から特定できず、UNKNOWN。
- 話者の事例や数値(採点基準など)は自己申告で、検証していない。
- 特典・勉強会などの宣伝要素は知見として扱っていない。
