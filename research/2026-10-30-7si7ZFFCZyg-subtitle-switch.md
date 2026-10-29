---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：AIリバースエンジニアリング道具「REA」で何が崩れ何が残るか"
description: "REAは難解な解析ツールをAIに持たせる道具箱。投稿者の自作ゲームで隠しコマンド・暗号文・得点式を7分半で言い当てた。手間という壁が崩れ、サーバー側・データ・信頼が残るという見立てを整理。"
tags:
  - "AI技術研究室"
  - "リバースエンジニアリング"
  - "REA"
video_id: "7si7ZFFCZyg"
logical_id: "youtube:7si7ZFFCZyg:research"
transcript_logical_id: "youtube:7si7ZFFCZyg:transcript"
resource: "https://www.youtube.com/watch?v=7si7ZFFCZyg"
canonical_url: "https://www.youtube.com/watch?v=7si7ZFFCZyg"
published_at: "2026-10-18"
---

# 研究ノート：AIリバースエンジニアリング道具「REA」

## 独自要約

REAは、従来は専門家しか扱えなかった解析ツールをAIが自力で使えるようにする道具箱として紹介されている。投稿者は自作ゲームに隠しコマンドと暗号化メッセージ、得点計算を仕込み、名前を消した完成品だけをAIに渡して3問を出した。結果は全問正解で、所要は約7分半だった。投稿者は、できること自体は従来と同じで変わったのは手間だと位置づける。そのうえで、手元に届くソフトは読まれる前提になり、価値はサーバー側・蓄積データ・信頼へ移ると見立てている。

## チャプター

- 導入：話題の道具REAと問いの提示 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=0s>
- 人気の規模と動画の3本柱 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=63s>
- 1. REAとは何か（設計図と完成品の例え） — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=83s>
- 従来の解析ツールとREAの位置づけ — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=143s>
- AIに道具箱を持たせる仕組みと復元の限界 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=164s>
- 2. 自作ゲームでの実験（法的注意と準備） — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=263s>
- 出題と結果 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=336s>
- AIの調査手順と自己申告の限界 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=357s>
- 3. 何が崩れ何が残るか — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=427s>
- 投稿者の見立てとまとめ — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=512s>

## 重要な知見

1. 復元されるのは元の設計図ではなく、AIによる推測、その根拠、分からなかった点の記録だとされる。消えた名前は戻らない。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=164s>
2. 解析自体は昔から可能で、NSA公開の道具など既存手段がある。変わったのは必要な手間だと述べられる。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=143s>
3. 本職の解析者が電卓アプリを約28分で解析・再現したという紹介がある（手作業は数日〜1週間と説明）。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=220s>
4. 実験では隠しコマンド、暗号化メッセージ、得点の決まり方の3問に全問正解、約7分半。設計図は隔離して見えない条件にしたと説明される。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=351s>
5. AIは残存文字列から手掛かりを得て、参照箇所をたどり、キー入力の照合や鍵の特定へ進んだと説明される。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=357s>
6. AIは「実際には動かしていない」と限界を申告したと紹介される。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=408s>
7. 崩れたのは「誰も調べない」という手間の壁。手元に届くソフトは読まれる前提で考えるべきだとされる。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=433s>
8. 利点として、手元のアプリや家電の通信内容を専門家以外も確かめやすくなる点が挙げられる。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=473s>
9. 残るのはサーバー側の処理、蓄積データ、信頼。投稿者の予測では、ソフトを手元に渡さず配信型にする流れが進む。 — <https://www.youtube.com/watch?v=7si7ZFFCZyg&t=489s>

## この研究室への応用

- 「AIに専用ツール群を持たせて調査を反復させる」設計の事例として、エージェント型ツール連携の研究材料にできる。
- 検証設計の参考：正解を隠した隔離環境で、少数の明確な設問を出して評価する方法。
- 自作成果物の防御評価（難読化や秘匿の強度確認）を、許可された自分の資産に限って試す際の着想になる。
- 「手間の壁」が崩れた後の防御は、サーバー側設計・データ・信頼に置くという論点を整理する軸にできる。

## 限界・未確認

- 映像は未確認で、字幕テキストのみを根拠にしている。画面上の表示や結果の証拠は見ていない。
- 公式資料（REAの公式リポジトリ・文書、紹介された数値や事例の一次情報）は未照合。
- 字幕は自動字幕で、誤変換の可能性がある（ツール名「REA」や解析ツール名の表記、星の数などの数値を含む）。
- 実験は投稿者1名・1本の小規模ゲームによる単発の結果で、一般化はできない。再現性は未確認。
- REAの正式名称、提供元、ライセンス、対応環境、使用モデル等の外部仕様：UNKNOWN。
- 星の数・再生数・28分の事例・日本法の整理は投稿者の発言であり、正確性は未検証。法的判断の根拠にしない。
