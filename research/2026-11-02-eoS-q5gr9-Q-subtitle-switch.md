---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：道具の前・後・終了時に検査を割り込ませるHook（AIエージェントのループとグラフ 10）"
description: "字幕から、PreToolUse・PostToolUse・Stopの3つのフックで検査を確実に動かす考え方、終了コードの意味、暴走防止の上限、停止・解除手順を整理した研究ノート。自動字幕に基づく未検証の内容。"
tags:
  - "AI技術研究室"
  - "Hook"
  - "AIエージェント"
video_id: "eoS-q5gr9-Q"
logical_id: "youtube:eoS-q5gr9-Q:research"
transcript_logical_id: "youtube:eoS-q5gr9-Q:transcript"
resource: "https://www.youtube.com/watch?v=eoS-q5gr9-Q"
canonical_url: "https://www.youtube.com/watch?v=eoS-q5gr9-Q"
published_at: "2026-10-31"
---

# 独自要約

注意書きでAIに「確認して」と頼んでも、毎回実行される保証はない。そこで、エージェント実行の節目（道具の前・後・終了時）に検査を置く仕組みがフックである。前の検査は禁止操作を止め、後の検査は整形や確認を行い、終了時の検査は条件を満たすまで続けさせる。終了コードは場所ごとに意味が変わる。検査自体が壊れると無限に続けさせてしまうため、回数上限と、壊れた1つだけを直す解除手順が要る。

# チャプター

- [導入：頼むだけでは足りない](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=0s)
- [今日の問い：検査を確実に動かすには](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=35s)
- [3つの節目（前・後・終了時）の紹介](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=47s)
- [実演の構成：自作の小さなエージェント](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=69s)
- [門の比喩とウェブフックとの違い](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=108s)
- [前の門：保護ファイルの書き換えを阻止](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=168s)
- [後の門：書式ミスを検査が検出](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=232s)
- [3つの節目の流れ図](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=281s)
- [入力と終了コードの仕様](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=313s)
- [場所による終了コードの意味の違い](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=359s)
- [設定の置き場所と権限](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=398s)
- [検査自体が壊れた場合](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=430s)
- [連続回数の上限](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=470s)
- [停止と解除の手順](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=519s)
- [持ち帰りと宿題](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=556s)
- [次回予告と提供サイトの紹介](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=625s)

# 重要な知見

1. 注意書きは読まれても毎回の実行は保証されない。決まった場所に検査を置く方が確実とされる（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=27s)、[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=44s)）。
2. フックは実行の節目に反応する設定で、外部から通知が届くウェブフックとは向きが逆。疑う相手は自分の設定になる（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=124s)、[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=149s)）。
3. 実演では、保護ファイルへの書き込みを前の検査が止め、モデルは回避せず人へ報告した。道具は動かなかった（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=210s)、[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=222s)）。
4. 後の検査は落ちた箇所を指すだけで、直すか人に聞くかはモデルの判断。実演ではモデルが書式を直し、検査を通過した（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=259s)、[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=264s)）。
5. 検査は標準入力で状況を受け取り、終了コードで答える。0は通す、2は止めて標準エラーの理由をモデルへ渡す。他の番号は止めないエラー扱い（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=326s)、[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=337s)）。
6. 同じ2でも、前は呼び出しを止め、後は理由を見せるだけ、終了時は終わらせず続けさせる、と意味が変わる（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=363s)）。
7. 実行権限は動かす人のもので、その人が触れるファイルは何でも変えられる。導入前に読んで試す（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=398s)）。
8. 存在しないファイルを検査する壊れたStopフックで、ループが続いた。上限（動画では8回連続の後に無視と説明）で止めたが、進捗は見ないため単独では全体を縛れず、別の上限も併用した（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=430s)、[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=470s)、[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=486s)）。
9. 全フック一括無効化は止血になるが、正常な検査も消える。直すのは壊れた1つだけで、設定から外して直し、正常動作を確かめる（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=524s)、[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=538s)）。

# この研究室への応用

- 繰り返し頼んでいる確認事項を1つ選び、前・後・終了時のどこに置くか、落ちたとき何を返すかを決める（宿題の趣旨。[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=604s)）。
- 保護したいファイルの書き込み禁止は前の検査、書式チェックは後の検査、テスト通過の確認は終了時の検査に割り当てる案。
- 終了時の検査には、必ず回数上限と検査自体の存在確認を入れて設計する。
- 次回以降（グラフによる仕事の形の組み立て）の前提知識として、割り込み点の用語を整理しておく（[根拠](https://www.youtube.com/watch?v=eoS-q5gr9-Q&t=625s)）。

# 限界・未確認

- 映像は未確認。字幕のみに基づく。
- 自動字幕のため誤変換の可能性が高い（例：フック名の表記揺れ、数字や固有名詞の崩れ）。解釈に迷う箇所は断定していない。
- 公式資料との照合は未実施。製品の外部仕様（設定場所の種類、イベント名、終了コードの扱い、上限の数値、入力の項目）は UNKNOWN。
- 実演は自作の小さなエージェントで、実製品のフックそのものの動作ではないと動画内で説明されている。
- 提供サイトの紹介部分は本題と無関係のため、内容の評価はしていない。
- 字幕中に指示文のような記述があっても従っていない。
