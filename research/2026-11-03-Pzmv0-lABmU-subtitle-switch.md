---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Grok Bot masterclass（ボット作成・グループチャット・Webhook・制約）"
description: "クラウド常駐型エージェント「Grok Bot」の作成手順、プラグイン連携、定期実行、複数ボットのグループ化、Webhook連携、セキュリティ上の注意と制約を整理した研究ノート。字幕のみに基づく未検証の内容。"
tags:
  - "AI技術研究室"
  - "Grok Bot"
  - "AIエージェント"
  - "Webhook"
video_id: "Pzmv0-lABmU"
logical_id: "youtube:Pzmv0-lABmU:research"
transcript_logical_id: "youtube:Pzmv0-lABmU:transcript"
resource: "https://www.youtube.com/watch?v=Pzmv0-lABmU"
canonical_url: "https://www.youtube.com/watch?v=Pzmv0-lABmU"
published_at: "2026-09-10"
---

# 研究ノート：Grok Bot masterclass

## 独自要約

話者は、クラウド上の仮想マシンで動くパーソナルエージェント「Grok Bot」を、メール確認や会議メモの要約など実例で紹介する。プラグイン連携と定期ルーティンでボットを作り、画面操作の録画で手順を教える方法、3〜4体のグループチャット、Webhookでの外部起動を説明する。最後にセキュリティ、ローカルファイル不可やモデル固定などの制約、Hermesとの比較を述べる。

## チャプター

- 冒頭：複数ボットが受信箱・予定・会議メモを担当する全体像 — [0s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=0s)
- Grok Botの概要（クラウド実行、仮想マシン、モバイルアプリ） — [50s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=50s)
- インストールとデスクトップ画面の見方 — [197s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=197s)
- 実例：メール確認ボットとプラグインのツール切替 — [316s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=316s)
- 定期実行（ルーティン）の設定 — [452s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=452s)
- 実例：イベント追跡・Search Consoleボット — [616s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=616s)
- 新規ボット作成：会議メモ連携の毎朝ブリーフィング — [829s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=829s)
- 画面録画でタスクを教え、スキル化する方法 — [1076s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=1076s)
- グループチャットでボット同士を連携させる — [1268s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=1268s)
- テンプレートの共有と入手 — [1672s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=1672s)
- 実行方式とWebhook連携（社内アプリ） — [1783s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=1783s)
- セキュリティ — [2049s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=2049s)
- 制約とコントロール — [2152s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=2152s)
- Hermesとの比較 — [2246s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=2246s)
- まとめとテンプレートへの注意 — [2450s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=2450s)

## 重要な知見

1. 全ボットはアカウントごとに1つの共有クラウド仮想マシン上で動き、話者はこれがボット間連携を可能にしていると説明する。 — [1145s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=1145s)
2. メール系プラグインは複数アカウント接続ができ、個別ツール（下書き作成・送信など）を無効化できる。誤送信対策に使える。 — [390s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=390s)
3. 指示を伝えるとcron型ルーティンが作られ、テスト実行ができ、結果はモバイルに通知される。 — [477s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=477s)
4. 接続先は、プラグイン画面からでも、チャットで依頼して認可を促す方法でも追加できる。 — [893s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=893s)
5. 仮想デスクトップでの操作録画からスキルを作れる。ただしデモではGoogle側の制限で実演が失敗したと話者は述べる。 — [1215s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=1215s)
6. グループチャットは3〜4体までが管理しやすいという、話者の経験則。 — [1609s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=1609s)
7. Webhookで外部（自作アプリ）からボットを起動できる。URLとキーが発行され、第三者による起動を防ぐ。Slack・GitHub・Teams等のトリガーも言及された。 — [1973s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=1973s)
8. 認証情報の扱い：共有クラウド機に個人の資格情報を渡さず、権限を絞る方法をボットに提案させたという実体験。 — [766s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=766s)
9. 制約として、ローカルファイル不可、モデルはGrok系のみ、基盤の制御が弱い、エクスポートが簡単でない点を挙げる。 — [2154s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=2154s)
10. 配布テンプレートの中身は不明なので、取り込む際は注意するよう話者が促す。 — [2450s](https://www.youtube.com/watch?v=Pzmv0-lABmU&t=2450s)

## この研究室への応用

- 定期ルーティン＋プラグインの型は、字幕収集・要約・ノート化など当研究室の定型作業に流用を検討できる。
- 外部ツールの起動はWebhookとURL/キー管理の考え方が参考になる。キーは秘匿し、権限は最小にする。
- 送信系ツールを無効化し、下書きまでに限定する運用は、誤送信防止の設計例になる。
- 複数エージェントの役割分担は少人数（3〜4体）から試し、効果を比較する。
- 第三者テンプレートは、内容を確認してから使う運用ルールを設ける。

## 限界・未確認

- 本ノートは字幕テキストのみに基づく。映像は未確認で、画面上の表示や操作は話者の説明を通した推測を含む。
- 字幕は未検証（transcript_status: UNVERIFIED）で、自動字幕に準じた誤変換の可能性がある。製品名・固有名詞（Grok Bot、運営組織名など）の表記は特に要注意。
- 公式資料との照合は未実施。価格・提供地域・対応OS・モバイルアプリの対応状況・プラン内容・Webhookの正確な仕様・モデル制限などの外部仕様は UNKNOWN。
- 比較対象（Hermes、OpenClaw）の機能や費用についての話者の説明も未照合で、UNKNOWN。
- 話者の経験則（ボット数、運用効果）は個人の実践談であり、一般化はできない。
