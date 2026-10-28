---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "【研究ノート】How to Use Hermes AI Agent [wETSpF4ef6E]"
description: "Hermes AIエージェントをWindowsに導入し、ローカルモデル接続、ブラウザ操作、記憶、スキル化、定期実行までを実演する動画の研究ノート。字幕のみに基づく未検証の整理。"
tags:
  - "AI技術研究室"
  - "Hermes AI Agent"
  - "ローカルLLM"
  - "AIエージェント自動化"
video_id: "wETSpF4ef6E"
logical_id: "youtube:wETSpF4ef6E:research"
transcript_logical_id: "youtube:wETSpF4ef6E:transcript"
resource: "https://www.youtube.com/watch?v=wETSpF4ef6E"
canonical_url: "https://www.youtube.com/watch?v=wETSpF4ef6E"
published_at: "2026-10-23"
---

# Hermes AI Agentの使い方（研究ノート）

## 独自要約

無料のオープンソースAIエージェントHermesを、Windowsのデスクトップ版で導入し、推奨のローカルモデルへ接続する手順が示される。ファイル作成、ブラウザ経由のYouTubeコメント返信下書きと投稿、記憶、スキル化、毎朝の定期実行、メッセージアプリ連携までを一通り実演する入門動画。

## チャプター

- [導入・全体像](https://www.youtube.com/watch?v=wETSpF4ef6E&t=0s)：扱う内容（導入、ローカルモデル、記憶、スキル、自動化）の予告。
- [インストール](https://www.youtube.com/watch?v=wETSpF4ef6E&t=35s)：公式サイトからWindows用デスクトップインストーラを取得。Mac/Linux対応とコマンドライン導入にも言及。
- [AIモデル接続](https://www.youtube.com/watch?v=wETSpF4ef6E&t=66s)：クラウド（Nous Portal）かローカルかを選択。ローカルの推奨モデルを自動セットアップ。
- [基本操作とファイル作成](https://www.youtube.com/watch?v=wETSpF4ef6E&t=127s)：画面構成の説明と、デスクトップへのフォルダ・文書作成の実演。
- [ブラウザ操作](https://www.youtube.com/watch?v=wETSpF4ef6E&t=197s)：ブラウザ接続の説明。
- [YouTubeコメント対応](https://www.youtube.com/watch?v=wETSpF4ef6E&t=221s)：新規セッション、ブラウザ接続、直近コメントの確認、返信下書き、承認後の投稿。
- [記憶機能](https://www.youtube.com/watch?v=wETSpF4ef6E&t=333s)：返信方針を覚えさせ、新規セッションで保持を確認。
- [スキル](https://www.youtube.com/watch?v=wETSpF4ef6E&t=403s)：作業手順を再利用可能なスキルとして作成し、名前指定で実行。
- [定期実行](https://www.youtube.com/watch?v=wETSpF4ef6E&t=508s)：毎日午前9時のスケジュールジョブを作成。
- [メッセージ連携とまとめ](https://www.youtube.com/watch?v=wETSpF4ef6E&t=571s)：WhatsAppやTelegram等との連携、他用途への展望。

## 重要な知見

1. 動画では、チャット応答だけでなくPC上で実際に操作を行えるエージェントとして説明される。デスクトップ上のフォルダと文書の作成で示された（[根拠](https://www.youtube.com/watch?v=wETSpF4ef6E&t=154s)）。
2. 推奨ローカルモデルは約18GBの保存容量が必要とされ、有料API利用を避けられると説明される。十分なメモリが必要とも述べられる（[根拠](https://www.youtube.com/watch?v=wETSpF4ef6E&t=95s)）。
3. ブラウザ操作は、コマンドで接続した後、ログイン済みのブラウザ画面を使って行われる（[根拠](https://www.youtube.com/watch?v=wETSpF4ef6E&t=229s)）。
4. 安全な進め方として、最初は「公開しない」よう指示して下書きだけ作らせ、確認・承認後に投稿させている（[根拠](https://www.youtube.com/watch?v=wETSpF4ef6E&t=279s)）。
5. 記憶は、新規セッションでも好みや方針が保持されることで確認された（[根拠](https://www.youtube.com/watch?v=wETSpF4ef6E&t=380s)）。
6. スキルは再利用可能な手順書で、完了済みの作業から作成できると説明される。実行時は記憶も併用された（[根拠](https://www.youtube.com/watch?v=wETSpF4ef6E&t=408s)）。
7. 定期実行には、Hermesがバックグラウンドで動作し、ブラウザセッションにアクセスできる状態が必要との注意がある（[根拠](https://www.youtube.com/watch?v=wETSpF4ef6E&t=563s)）。
8. メッセージアプリ連携により、PCを開かずスマホから指示できると説明される（[根拠](https://www.youtube.com/watch?v=wETSpF4ef6E&t=571s)）。

## この研究室への応用

- ローカルモデル併用の自動化を試す際の検証手順（導入→単純タスク→ブラウザ→記憶→スキル→定期実行）として、この順序は参考になる。
- 外部サービスへの投稿を伴う処理は、「下書き→人間の承認→投稿」の二段階にする設計が有用そうである。
- 動画字幕の調査・研究ノート作成のような反復作業を、スキル化と定期実行で自動化できるかを小規模に検証する価値がある。
- 検証時は、使用PCのメモリ・保存容量、ログイン済みブラウザの権限範囲、誤投稿時の対処を事前に確認する。

## 限界・未確認

- 映像は未確認。画面操作や表示内容は字幕の言及から推測した範囲にとどまる。
- 公式資料は未照合。機能、対応環境、価格、設定手順の正確性は確認していない。
- 字幕は取得方法の記載上は手動字幕だが、transcriptの状態は未検証であり、誤変換の可能性がある。特にモデル名・サービス名・版数表記は要確認。
- 推奨モデルの正式名称・版数・必要メモリ量の詳細：UNKNOWN。
- Hermesの提供元、ライセンス、セキュリティ仕様、データ保存先、権限モデル：UNKNOWN。
- 動作は発表者の環境での一例であり、他環境での再現性、性能、コメント返信の品質は未確認。
- プロンプトは概要欄にあるとされるが、内容は字幕に含まれず未確認。
- 研究ノート雛形（research_note_prompt_template.md）は作業ディレクトリに見当たらず参照できなかったため、指示文の形式に従って作成した。
