---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Evaluator–Optimizerと修復ループ、回帰テストで「できました」を検証する"
description: "AIの完了宣言ではなくテスト結果で合否を決める修復ループの解説動画の研究ノート。作る役と評価役の分離、回帰テスト、テスト改ざん点検を整理。字幕は自動生成で未検証。"
tags:
  - "AI技術研究室"
  - "Evaluator–Optimizer"
  - "修復ループ"
  - "回帰テスト"
video_id: "exyQn8Rfos4"
resource: "https://www.youtube.com/watch?v=exyQn8Rfos4"
canonical_url: "https://www.youtube.com/watch?v=exyQn8Rfos4"
published_at: "2026-10-31"
logical_id: "youtube:exyQn8Rfos4:research"
transcript_logical_id: "youtube:exyQn8Rfos4:transcript"
---

# 研究ノート：テストが落ちたら戻る（Evaluator–Optimizer）

## 独自要約（300字以内）

AIが「できました」と言っても完成とは限らない。この動画は、文化祭サイトの問い合わせフォームを題材に、合否を言葉でなくテストで決める構成を示す。直す役と評価する役を分け、失敗理由を次の修正へ渡す。新機能のテストが緑でも既存動作を壊す回帰が起きうるため、守る動作と前回結果を評価役に渡す。さらにテスト自体の書き換えをファイルの差分で点検し、上限と人の確認も置く。

## チャプター（字幕開始秒ベース）

- 導入：空送信でも「送信しました」と出る問題 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=0s>
- 今日の問いと3つの要点 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=26s>
- 実演の前提（自作の修復ループ、本物の言語モデルを別々に呼ぶ） — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=57s>
- フォームの欠陥とテスト4件（新規2件・回帰2件） — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=87s>
- 改善役・評価役・テスト実行の役割分担 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=170s>
- 合否の基準をテスト出力に置く理由 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=209s>
- 1周目：新規テストは通るが回帰が発生 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=267s>
- 2周目：指摘を受けて修正し4件が通る — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=351s>
- 守る動作を最初から渡した場合との比較 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=393s>
- テスト書き換えの点検（ハッシュ比較） — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=441s>
- 止める設計と持ち帰り・宿題 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=495s>
- 次回予告（定期実行）と番組サイト紹介 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=558s>

## 重要な知見

1. 完成の判定は言葉でなくテストが担う。空欄でも送信できる欠陥は、新規テストが失敗することで機械的に検出された。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=104s>
2. 作る役と検査する役を分け、評価役は合否に加えて落ちたテストごとの原因と直し方を返す。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=170s>
3. 機械で検査できる条件はテストが測り、基準のない評価は評価役の好みで回り続けるおそれがある。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=209s>
4. 評価役に守るべき既存動作を渡さないと、直した結果が別の動作を壊す回帰が起きた（内容欄まで必須化）。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=302s>
5. 全体仕様と前回出力を渡すと、2周目で回帰が解消し4件が通った。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=351s>
6. 動画内の比較では、守る動作を最初から渡した方が1周、渡さない方が複数周を要した。ただし同じ結果になる保証はないと述べている（少数試行）。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=393s>
7. テストの期待値を書き換えれば緑にできるため、テストファイルの差分点検をループの外に置く。書き換え時は点検が検出し不合格となった。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=456s>
8. 緑で確認できるのは用意したテスト範囲だけで、テストの不足は人が見る。成功条件・上限・失敗時の承認者を決める。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=485s>

## この研究室への応用

- 自動化パイプラインで、AIの完了報告ではなくテスト終了コードと出力を合否の根拠にする。
- 改善役への入力に「壊してはいけない動作」と前回のテスト結果を必ず含めるテンプレートを作る。
- テストファイルのハッシュ比較など、改ざん検知をループ外の固定手順にする。
- 周回上限と、失敗時に記録を読む承認者を設計書に明記する。
- 宿題として示された「前から動いていて壊したくない動作を2つ選び、入力・操作・期待結果を書く」を、自作品の回帰テスト作りに使う。 — <https://www.youtube.com/watch?v=exyQn8Rfos4&t=545s>

## 限界・未確認

- 映像は未確認で、字幕テキストのみから作成した。画面上の表示やコードの内容は確認していない。
- 公式資料との照合は未実施。動画が参照する外部の設計文書や仕様は UNKNOWN。
- 字幕は自動生成で、誤変換が多い（例：評価役・改善役の表記ゆれ、「回帰」の誤記、数値や用語の欠落）。本ノートの用語は文脈からの推定を含む。
- 実演は自作の小規模例（テスト4件、少数回の試行）であり、一般化できるかは UNKNOWN。
- ハッシュ方式の詳細や使用モデル名などは字幕から確定できず UNKNOWN。
- 動画末尾のサイト紹介部分は本題の知見に含めていない。
