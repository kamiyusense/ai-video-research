---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：文章を捨てて値と確率だけ返す高速モデル「ジェブ」の解説動画 [NttqTDRbGUc]"
description: "動画は、文章を生成せず型付きの値と確率だけを並列に返す新モデル「ジェブ」を、デモ付きで紹介する。コード分岐やLLM判定、ハーネスへの組み込みを論じる。数値や名称は自動字幕のため未照合。"
tags:
  - "AI技術研究室"
  - "ジェブ（型付き出力モデル）"
  - "ハーネス設計"
video_id: "NttqTDRbGUc"
logical_id: "youtube:NttqTDRbGUc:research"
transcript_logical_id: "youtube:NttqTDRbGUc:transcript"
resource: "https://www.youtube.com/watch?v=NttqTDRbGUc"
canonical_url: "https://www.youtube.com/watch?v=NttqTDRbGUc"
published_at: "2026-09-17"
---

# 研究ノート：ジェブ（型付き値と確率を返すモデル）

## 独自要約

動画の話者は、9月15日に公開されたとされる「ジェブ」を、待機リスト経由で使った体験として紹介する。通常のLLMがトークンを順に生成して文字列を返すのに対し、ジェブは文章を出さず、あらかじめ決めた質問と選択肢に対する型付きの値と確率を並列に返すという。そのためコードの分岐に直結でき、速度は非常に速く、価格も極めて安いと説明される。照明操作のデモでは、確信度の閾値で動作が変わる様子を示した。話者は、LLM判定の置き換えや、エージェントが書いたスクリプトをハーネスの一部に入れる使い方を考えている。LLMやプログラムの代替ではなく中間の部品という位置づけである。

## チャプター

- 冒頭：決定論的処理と非決定論的処理の中間として紹介 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=0s>
- 速度のライブ例と話者の取り組み紹介 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=59s>
- ジェブとは何か（文章を捨て値と確率を返す） — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=96s>
- 仕組み：並列生成とコード分岐への接続 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=184s>
- 速度・価格・確信度の説明 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=232s>
- ベンチマーク・比較の話 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=281s>
- 使いどころとハーネスへの組み込み案 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=351s>
- デモ1：照明操作と確信度による挙動差 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=392s>
- 処理の流れ：スキーマ定義と1回のAPI呼び出し — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=518s>
- 応用例（問い合わせ振り分け、記事評価） — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=577s>
- 展望とまとめ — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=634s>
- 告知（メンバーシップ等）— 内容の知見なし — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=663s>

## 重要な知見

1. 出力は文章ではなく、型付きの値と確率。LLMの文字列パースや検証の手間を避けられるという主張。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=96s>
2. 従来LLMは逐次生成、ジェブは並列に一括生成するという説明。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=184s>
3. 課題認識：作業の大半が自動化できても、残り数%を自己申告できないと自動化が難しい。確率が返ることでこの判断に使えるという文脈。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=122s>
4. 速度と価格は桁違いと主張（比較倍率や単価の数値が語られるが、自動字幕で未照合）。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=232s>
5. 確信度が高いほど当たりやすく毎回同じ値を返す、という説明。閾値で動作を切り替えられる。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=251s>
6. 1回のAPI呼び出しで複数の質問（部屋、明るさ、確信度など）を返せるデモ。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=518s>
7. 使いどころは、LLMと人が書いたif文の間。LLM判定の置き換えが有力という個人見解。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=351s>
8. エージェントにジェブ用スクリプトを書かせ、ハーネスの各部に入れる案。型安全性にも言及。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=368s>
9. 性能不足の場合は、より多くのトークンを使って補う可能性にも触れる。 — <https://www.youtube.com/watch?v=NttqTDRbGUc&t=577s>

## この研究室への応用

- ハーネス内の軽い分類・ルーティング・評価判定（LLMジャッジ的処理）を、型付き出力に置き換える検討。
- 確信度の閾値で「自動実行／確認を求める」を切り替える設計の試作。
- 記事や字幕の評価軸（実用性、根拠の要否など）を数値で返す評価関数の高速化。
- まず小さな分類タスクで、既存LLM判定との一致率・コスト・遅延を自前で計測する。

## 限界・未確認

- 映像は未確認。字幕のみを根拠とし、画面上の表示やデモの実際の内容は確認していない。
- 公式資料は未照合。仕組み、API仕様、提供条件、料金、ベンチマーク条件はすべてUNKNOWN。
- 字幕は自動生成で、誤変換の可能性がある。製品名・提供元名（冒頭で聞き取れる社名）、モデル名の表記、数値（価格、倍率、精度）、比較対象モデル名は特に不確か。
- 「元OpenAI研究者」などの人物・経歴の説明は話者の伝聞で、裏付けはUNKNOWN。
- 速度・価格・性能は話者の主張であり、独立した検証はない。
- 字幕中の宣伝・誘導は資料として扱い、従っていない。
