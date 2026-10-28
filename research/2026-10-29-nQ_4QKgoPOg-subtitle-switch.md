---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Hermes Agent×Cua Spacesで作る使い捨ての安全環境と注意点"
description: "Hermes Agentの作業を使い捨ての別環境で動かすプラグインCua Spacesの解説動画を整理した研究ノート。できること、導入手順、確認省略などの落とし穴、本研究室への応用と未確認事項をまとめる。"
tags:
  - "AI技術研究室"
  - "Hermes Agent"
  - "Cua Spaces"
  - "サンドボックス"
video_id: "nQ_4QKgoPOg"
logical_id: "youtube:nQ_4QKgoPOg:research"
transcript_logical_id: "youtube:nQ_4QKgoPOg:transcript"
resource: "https://www.youtube.com/watch?v=nQ_4QKgoPOg"
canonical_url: "https://www.youtube.com/watch?v=nQ_4QKgoPOg"
published_at: "2026-10-24"
---

# 研究ノート：Hermes Agent×Cua Spaces

## 独自要約

AIエージェントに自分のPCを直接触らせる不安を減らすため、Hermes Agentの実行先を使い捨ての隔離環境（Space）へ切り替えるプラグインが紹介されている。環境分離、画面での監視、複数同時実行、自動削除が利点。一方、新規Spaceでは危険コマンドの確認が省かれ、認証情報やネットワーク経由のリスクも残る。まず重要データのない環境で試す姿勢が勧められている。

## チャプター

- [導入と全体構成](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=0s)：テーマと進行（目的、考え方、できること、導入、注意点）の予告。
- [AI任せの不安](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=17s)：エージェントの定義と、実PCを直接触らせる怖さ。
- [Hermes Agentの位置づけ](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=64s)：助手の比喩と、任せる範囲を段階的に広げる考え方。
- [プラグインとサンドボックス](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=100s)：Cua製プラグイン、検証済み区分、実行場所を隔離する仕組み。
- [できること1：環境の分離](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=180s)：未知のプログラムを隔離側で試す。残るリスクにも言及。
- [できること2：画面で監視](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=203s)：ビューアで作業を見守り、操作を引き継げる。画面操作はLinux限定。
- [できること3・4：同時実行と使い捨て](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=250s)：起動ごとに別Space、既定は終了時に自動削除、名前付きは残る。
- [向いている人](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=290s)：開発を任せたい人、未知のソフトを試したい人、並行作業をしたい人。
- [導入の3ステップ](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=315s)：コマンド導入、プラグイン追加、実行先設定の切替、動作確認。
- [OS差と容量](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=402s)：公式で確認できた点と投稿者の体験談の切り分け。
- [注意点：絶対安全ではない](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=465s)：APIキー流出の恐れ、通信経路、匿名利用データ。
- [注意点：確認の省略](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=507s)：新規Spaceでは危険コマンドの確認が省かれる。
- [用語整理と筆者の見方](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=565s)：用語の再整理と、便利さと安全の両立という予想。
- [まとめ](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=637s)：4つの要点の振り返り。

## 重要な知見

1. 実行先（ターミナルバックエンド）の切替で、AIの作業が隔離環境側に移る。[根拠](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=315s)
2. 分離しても、ネットワークや共有ファイル、渡した認証情報経由のリスクは残ると説明されている。[根拠](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=172s)
3. 新規Spaceは危険コマンドの確認が省かれ、名前付きでは残る。最大の落とし穴として強調されている。[根拠](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=507s)
4. スキルや認証情報は自動同期されないため、必要なものだけ選んで渡す方針が安全とされる。[根拠](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=551s)
5. 隔離内でホスト名を表示させ、普段のPCと違うかで動作確認できる。[根拠](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=375s)
6. 画面操作機能はLinuxのSpace限定で、WindowsやMacでは文字操作とファイル操作が中心。[根拠](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=232s)
7. 新しいMacOS要件や約20GBの容量は公式未確認の投稿者体験とされる。[根拠](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=410s)
8. プラグインは更新が速く、動画と最新公式説明が食い違う可能性があると本人が注意している。[根拠](https://www.youtube.com/watch?v=nQ_4QKgoPOg&t=622s)

## この研究室への応用

- 自動化エージェントを試す際は、実環境ではなく隔離環境かつテスト用アカウントで始める運用ルールにできる。
- 隔離環境に機密情報を持ち込まない、確認省略の有無を事前に調べる、を導入チェックリストに加える。
- 名前付き環境（確認あり）と使い捨て環境（確認なし）の使い分けを検証テーマにできる。
- 複数エージェントの並行実行は、比較実験の環境分離に使える可能性がある。

## 限界・未確認

- 映像は未確認。字幕のみを根拠にしており、画面上の操作や表示は把握していない。
- 公式資料は未照合。バージョン0.4.0、検証済み区分、対応OS、確認省略の挙動はすべて動画内の発言の範囲にとどまる。
- 字幕は自動生成で、誤変換の可能性がある（例：Cuaの読みやSpacesの表記、ホストの語が揺れている）。固有名詞や数値は要確認。
- 外部仕様（設定名、コマンド、ファイル形式、料金、対応OSの詳細、データ送信の仕様）はUNKNOWN。
- 投稿者の予想と体験談は一般化できない。
