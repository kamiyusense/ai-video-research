---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Claude Code のサブエージェントの仕組み・書き方・使い分け"
description: "Claude Code のサブエージェントについて、文脈の分離、定義ファイルの書き方、道具の絞り方、任せ方、メイン会話との使い分けを字幕から整理した研究ノート。自動字幕のため未検証。"
tags:
  - "AI技術研究室"
  - "Claude Code サブエージェント"
video_id: "PYjCf84y068"
logical_id: "youtube:PYjCf84y068:research"
transcript_logical_id: "youtube:PYjCf84y068:transcript"
resource: "https://www.youtube.com/watch?v=PYjCf84y068"
canonical_url: "https://www.youtube.com/watch?v=PYjCf84y068"
published_at: "2026-10-29"
---

# 独自要約

サブエージェントは、検索結果やログなどで会話が散らかる作業を別の文脈で処理し、要点だけを返す仕組みと説明されている。Markdownファイル1つで定義でき、置き場所で適用範囲が決まる。道具は許可・除外で絞る。任せ方は3段階。対話が多い作業や速さ重視の作業はメイン会話向きとされる。

# チャプター

- [冒頭：サブエージェントを使うべきか](https://www.youtube.com/watch?v=PYjCf84y068&t=0s)
- [散らかる作業を別の文脈で引き受ける](https://www.youtube.com/watch?v=PYjCf84y068&t=5s)
- [仕組み：独自の文脈・指示・道具](https://www.youtube.com/watch?v=PYjCf84y068&t=46s)
- [組み込みのサブエージェント](https://www.youtube.com/watch?v=PYjCf84y068&t=71s)
- [何を知った状態で始まるか](https://www.youtube.com/watch?v=PYjCf84y068&t=100s)
- [作り方：ファイル1つ](https://www.youtube.com/watch?v=PYjCf84y068&t=142s)
- [置き場所と優先順位](https://www.youtube.com/watch?v=PYjCf84y068&t=193s)
- [道具の絞り方](https://www.youtube.com/watch?v=PYjCf84y068&t=211s)
- [応用4点：スキル先読み・記憶・隔離・続き](https://www.youtube.com/watch?v=PYjCf84y068&t=297s)
- [書き方の落とし穴](https://www.youtube.com/watch?v=PYjCf84y068&t=390s)
- [任せ方の3段階と説明欄](https://www.youtube.com/watch?v=PYjCf84y068&t=461s)
- [公式が挙げる使い方3つ](https://www.youtube.com/watch?v=PYjCf84y068&t=540s)
- [同時実行数の上限](https://www.youtube.com/watch?v=PYjCf84y068&t=588s)
- [メイン会話が向く場面とサブが向く場面](https://www.youtube.com/watch?v=PYjCf84y068&t=602s)
- [スキルとの使い分け・無効化](https://www.youtube.com/watch?v=PYjCf84y068&t=651s)
- [まとめ用の例と総括](https://www.youtube.com/watch?v=PYjCf84y068&t=691s)
- [最初に作るなら](https://www.youtube.com/watch?v=PYjCf84y068&t=760s)

# 重要な知見

1. 目的は文脈の保護。大量の出力を別の窓で処理し、要約だけをメインに返す。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=5s)
2. 各サブエージェントは独自の文脈・指示・道具権限を持つが、使用量はメインと同じ上限に数えられると述べられている。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=46s)
3. 組み込みは探索用・計画用・汎用の3種。探索と計画はCLAUDE.mdを読まず軽く始まるとされる。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=71s)
4. フォーク以外は白紙の文脈で始まり、Claudeがまとめた依頼文だけを受け取る。守らせたい決まりは依頼文に書く。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=100s)
5. 定義はMarkdown1ファイル。上部が設定、本文が指示。Claudeに作成を頼むこともできる。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=142s)
6. プロジェクト配下に置けばリポジトリ経由でチーム共有、ホーム配下なら全プロジェクトで使える。同名は優先度の高い方が採用。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=193s)
7. 道具は許可リストと除外リストで絞る。両方指定すると除外が先に効く。Bashの特定コマンドだけ止めたい場合は権限の拒否設定を使う。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=211s)
8. 応用として、スキルの先読み、記憶フォルダ、ワークツリー隔離、履歴を保った再開がある。探索と計画は再開不可。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=303s)
9. 必須項目は名前と説明のみ。未知の項目名は黙って無視されるため、デバッグ起動のログで確認する。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=390s)
10. 数値設定は単位表記（例：200K）が誤読される罠がある。数字はそのまま書く。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=431s)
11. 任せ方は、名前を出して頼む、@で指定、セッション全体を指定の3段階。自動委任には説明欄が手がかりになる。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=461s)
12. 用途は、大量出力の隔離、独立した調査の並列化、調査から修正への連鎖。並列は文脈とトークンを消費する。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=540s)
13. 同時実行は既定で上限があり、環境変数で変更できると説明されている。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=588s)
14. 対話で詰める作業、文脈共有が必要な作業、小さな修正はメイン会話向き。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=602s)
15. 使い回す手順はスキル、同じ指示の担当を繰り返し呼ぶならサブエージェントを自作。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=651s)
16. 使わせたくない場合は権限の拒否や環境変数で無効化できる。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=668s)

# この研究室への応用

- 失敗テストだけを報告するテスト実行係を最初の試作にする。[根拠](https://www.youtube.com/watch?v=PYjCf84y068&t=760s)
- 長い調査やログ解析をサブエージェントに分け、メイン会話の文脈消費を抑える運用を試す。
- 読み取り専用のレビュー係と、編集可能な修正係を分け、道具権限で役割を区別する。
- 定義ファイルをリポジトリで共有し、設定の誤字を防ぐ確認手順（デバッグ起動）を用意する。

# 限界・未確認

- 映像は未確認で、字幕のみに基づく。
- 公式資料とは未照合。数値の既定値（同時実行数、ネスト深さ、スキル数、説明の長さ上限など）や設定名、環境変数名は UNKNOWN。
- 自動字幕のため誤変換の可能性が高い（例：「係り」「ようやく」等の表記揺れ、設定名のカタカナ化）。項目名・コマンド名は原文で確認が必要。
- 外部仕様（Claude Codeの現行挙動、バージョン差）は UNKNOWN。
- 動画内で言及される10月24日回のフォーク解説は未参照。
