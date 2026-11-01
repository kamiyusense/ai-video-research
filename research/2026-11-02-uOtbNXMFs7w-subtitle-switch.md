---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：自己改善するAI秘書「Hermes Agent」の仕組みとVPSセットアップ [uOtbNXMFs7w]"
description: "Hermes Agentを、モデルを動かす仕組み（ハーネス）として整理し、記憶とスキルの自動学習、デスクトップ版の導入、VPSでの24時間運用、Telegram連携までを字幕から読み解いた研究ノート。"
tags:
  - "AI技術研究室"
  - "Hermes Agent"
  - "AIエージェント"
  - "VPS"
video_id: "uOtbNXMFs7w"
logical_id: "youtube:uOtbNXMFs7w:research"
transcript_logical_id: "youtube:uOtbNXMFs7w:transcript"
resource: "https://www.youtube.com/watch?v=uOtbNXMFs7w"
canonical_url: "https://www.youtube.com/watch?v=uOtbNXMFs7w"
published_at: "2026-09-26"
---

# 研究ノート：Hermes Agentの仕組みとVPSセットアップ

## 独自要約

Hermes Agentは、AIモデルそのものではなく、モデルを動かす仕組み（ハーネス）である。会話から好みを記憶し、繰り返す作業をスキル化し、使わないスキルを整理する点が特徴とされる。動画はまずデスクトップ版をChatGPTの有料枠で動かす手順を示す。続いて、VPSにDockerで展開した常時稼働の環境へデスクトップ版をつなぎ、Telegramのボットでスマホからも同じ環境を使う流れを紹介する。投稿者はClaude Codeのフォルダー単位の管理と対比し、複数案件を横断して人のように覚えさせたい用途に向くと述べる。一方で、利用できる定額枠の制約、設定の手間、外部サーバーへ情報を置くリスクも挙げている。

## チャプター

- [導入：Hermes Agentを紹介する趣旨](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=0s)
- [Hermes Agentとは何か：モデルとハーネスの区別](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=50s)
- [なぜ採用するのか：記憶・スキル化の仕組みが最初からある](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=234s)
- [デメリット：定額枠で使えるモデルの制限とセットアップの手間](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=403s)
- [話しかける入り口：CLI・TUI・デスクトップ・チャットアプリ](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=553s)
- [デスクトップアプリの導入とモデル設定](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=736s)
- [標準スキル・画像生成などの試用](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=911s)
- [自己学習の挙動：記憶とスキル化、不要スキルの削除](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1031s)
- [記憶の実演：簡潔な回答の好みを覚える](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1101s)
- [24時間稼働させる利点](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1186s)
- [常時稼働の方法：専用機とVPS](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1305s)
- [VPSの契約とHermes Agentの展開](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1458s)
- [ダッシュボードへのログイン](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1756s)
- [デスクトップアプリをリモート環境に接続](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1858s)
- [リモート側のモデル設定](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1996s)
- [データの置き場所と送信先に関する注意](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=2240s)
- [Telegram連携とスマホからの定期タスク](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=2292s)
- [告知・締め](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=2613s)

## 重要な知見

1. Claude CodeやChatGPT系の製品は「モデル」と「動かす仕組み」の組み合わせであり、Hermes Agentは後者にあたる、という整理である。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=86s)
2. 記憶の単位が異なる。Claude Codeは起動フォルダー単位、Hermes Agentは複数の入口を1つのプロファイルに紐づけて覚える、と説明される。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=327s) [根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=700s)
3. 定額枠で使えるのはOpenAI系のみで、他社の定額プランはそのままでは使えないと述べられる。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=433s)
4. 標準で数十個のスキルとツールが入っている。動画内では57個と表示されたと述べる。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=921s)
5. 一定ターン数以上の会話や、ツール利用が多いタスクの後に、背景で会話を見直して記憶やスキルを作る、と投稿者は実装を見て説明する。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1038s) 一定期間使われないスキルは自動削除される仕組みもあるという。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1073s)
6. VPSは重い計算より記憶容量が重要で、8GB程度で足りるとの見立てである。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1470s)
7. 動画はホスティング事業者のタイアップで、割引クーポンの案内を含む。初月価格は後に上がる点にも注意が促される。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1405s) [根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=1498s)
8. リモート側のモデル設定では認証情報が借りたサーバーに残るため、リスクを理解し自己責任で使うよう述べている。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=2001s)
9. モデルによる処理の内容はOpenAIにも送られ、機密情報を扱う場合は仕組みの理解が必要とされる。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=2253s)
10. Telegramのボット経由で、数分後にニュースを送らせるといった定期タスクをスマホから作る実演がある。[根拠](https://www.youtube.com/watch?v=uOtbNXMFs7w&t=2445s)

## この研究室への応用

- 案件を横断して好みや判断を覚えさせたい用途（動画制作、見積書、進捗管理）では、フォルダー単位の運用と比べる価値がある。
- 検証案として、まず手元のデスクトップ版で記憶とスキル化の挙動を確認し、その後に常時稼働環境へ移す段階的な進め方が考えられる。
- 機密性の低い情報収集（ニュースの定期通知など）から始め、扱うデータの範囲を決めてから広げるのが妥当と考える。
- 記憶やスキルが増えたときの品質確認と、不要な記憶の棚卸しの運用ルールを別途検討したい。

## 限界・未確認

- 映像は未確認で、字幕のみを根拠にしている。画面操作や表示内容は確認できていない。
- 公式資料は未照合である。機能の有無・挙動・料金・対応モデルの最新仕様はUNKNOWN。
- 字幕は自動生成で、固有名詞や製品名、モデル名、数値に誤変換の可能性がある（例：製品名の表記ゆれ、モデル名の綴り）。
- 自己学習の発動条件や自動削除の期間など実装の詳細は、投稿者の口頭説明に依るもので、具体値はUNKNOWN。
- VPSの料金・割引・プラン内容は動画公開時点の説明で、現在の条件はUNKNOWN。タイアップ内容のため、評価には偏りがありうる。
- 字幕の終盤の一部は、本ノートの作成時点で取得した範囲に依存する。投稿者の主張は検証されていない。
- 指定のテンプレート（research_note_prompt_template.md）は作業フォルダーに見当たらず、参照できていない。指示文の形式に従って作成した。
