---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Everything New in Hermes Agent (Full Setup Guide)"
description: "Hermes Agentの概要、VPSへの導入、モデル設定、デスクトップアプリ接続、記憶・soul・スキル、ボット機能、定期ジョブまでを扱う解説動画の研究ノート。字幕のみに基づく未検証の整理。"
tags:
  - "AI技術研究室"
  - "Hermes Agent"
  - "AIエージェント"
video_id: "S8fc9na4pA8"
logical_id: "youtube:S8fc9na4pA8:research"
transcript_logical_id: "youtube:S8fc9na4pA8:transcript"
resource: "https://www.youtube.com/watch?v=S8fc9na4pA8"
canonical_url: "https://www.youtube.com/watch?v=S8fc9na4pA8"
published_at: "2026-10-27"
---

# 研究ノート：Everything New in Hermes Agent (Full Setup Guide)

## 独自要約

Hermes Agentは、モデルを自由に差し替えられるエージェント用ハーネスである。使うほどスキルとして手順を保存し改善する点が特徴だと説明される。動画は、VPSへのDockerでの導入、プロバイダ設定、デスクトップアプリ接続、記憶・soul・スキル・ツール・プラグイン、メッセージ連携を順に示す。後半では、設定や記憶が独立した複数ボット、グループチャット、定期ジョブ(cron)を紹介する。

## チャプター

- [導入と動画の範囲](https://www.youtube.com/watch?v=S8fc9na4pA8&t=0s)：24時間稼働、デスクトップアプリ、ボット機能などの新機能を扱うと予告。
- [Hermes Agentとは](https://www.youtube.com/watch?v=S8fc9na4pA8&t=77s)：自律行動・記憶・学習を持つエージェントで、他ツールとの比較も述べる。
- [6つの構成要素](https://www.youtube.com/watch?v=S8fc9na4pA8&t=191s)：モデル、ツール、記憶、スキル、ゲートウェイ、cronの概説。
- [学習の仕組み](https://www.youtube.com/watch?v=S8fc9na4pA8&t=337s)：作業手順をスキル化し、修正指示で更新する流れ。
- [VPSでの運用とデプロイ](https://www.youtube.com/watch?v=S8fc9na4pA8&t=384s)：VPSを推奨する理由と、ワンクリック導入の手順。
- [ダッシュボードへのログイン](https://www.youtube.com/watch?v=S8fc9na4pA8&t=595s)：管理者の認証情報をコンテナの環境設定で確認する。
- [操作方法の全体像](https://www.youtube.com/watch?v=S8fc9na4pA8&t=644s)：Dockerコンテナ内で動く構成と、ブラウザ・端末・コーディングAI経由の3通りの管理。
- [ターミナルとCLIエージェント導入](https://www.youtube.com/watch?v=S8fc9na4pA8&t=802s)：端末からの起動と、サーバー上にコーディングAIを入れる手順。
- [モデル設定](https://www.youtube.com/watch?v=S8fc9na4pA8&t=991s)：setupコマンドでプロバイダを切り替え、サブスク認証で接続する。
- [デスクトップアプリ接続](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1150s)：リモートゲートウェイとしてVPS上のHermesに接続する。
- [記憶ファイル](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1362s)：ユーザー情報と長期メモの2種類のmarkdownを扱う。
- [soul（人格）](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1543s)：人格定義ファイルの閲覧と書き換え。
- [スキルと学習コマンド](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1717s)：学習コマンドでスキルを作成・更新し、スキルハブから追加する。
- [スラッシュコマンド](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1899s)：新規セッション、保存、圧縮などの一覧紹介。
- [ツール・コネクタ・プラグイン](https://www.youtube.com/watch?v=S8fc9na4pA8&t=2000s)：ツール群の有効/無効切替、外部アプリ連携、プラグインカタログ。
- [メッセージング連携](https://www.youtube.com/watch?v=S8fc9na4pA8&t=2102s)：スマホから使うためのTelegram・Discord・Slack等の接続。
- [ボット機能とグループチャット](https://www.youtube.com/watch?v=S8fc9na4pA8&t=2156s)：人格やモデルが異なるボットを作成し、同じ場で会話させる。
- [ファイル表示と定期ジョブ](https://www.youtube.com/watch?v=S8fc9na4pA8&t=2378s)：ボットごとの独立ファイルと、自然言語での定期ジョブ作成。

## 重要な知見

- 話者はHermesを、日常的に対話して教え込む主力エージェントとして位置づけ、放置運用向きではないと述べる。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=126s)
- 学習は、スキル更新を担う「スキルキュレーター」という内部機構によると説明される。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=361s)
- VPS推奨の理由として、初期設定の安全性、低コスト、常時稼働、削除の容易さを挙げる。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=402s)
- ホスティング事業者とは提携関係にあり、割引コードも案内される。評価には利益相反を考慮すべきである。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=486s)
- 不具合に備え、Hermesと同じ環境にコーディングAIのCLIを入れて修復を任せる運用を勧める。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=754s)
- デスクトップアプリは単体で別のローカルHermesを作るため、VPS側と混同しないよう注意している。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1201s)
- 記憶のうちユーザー情報は全ボット共通で、長期メモは対話開始時に読み込まれると説明される。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1388s)
- soulはシステムプロンプトに近く、モデルを替えても人格が保たれると述べる。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1573s)
- スキルハブのスキルは悪意あるものが含まれ得るため、導入前に読むべきと注意している。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=1865s)
- ツール群を切り替え、読み取り専用や記憶無効のプロファイルを作る使い方が示唆される。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=2017s)
- ボットは記憶・soul・ファイル・セッションログが独立し、グループチャットで相互に会話させられる。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=2403s)
- 話者自身がボット間会話の仕組みを詳しく理解していないと認めており、挙動は未確定である。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=2333s)
- cronは手動作成のほか、自然言語の依頼でも作られることが実演される。[根拠](https://www.youtube.com/watch?v=S8fc9na4pA8&t=2427s)

## この研究室への応用

- 動画研究の自動化に使う場合は、スキル更新の履歴を確認できる運用とし、書き換えの自動反映は人が点検する。
- 調査用・要約用・レビュー用のようにボットを分け、記憶とsoulを独立させる設計を試す価値がある。
- 外部スキルは導入前に全文を確認する手順を、研究室の運用規則に入れる。
- 常時稼働が必要な作業は、権限を絞った隔離環境で動かし、ツール群を最小限にする。
- 定期ジョブで新着動画の字幕取得や下書き生成を回す案は、自社環境での検証を前提に検討できる。

## 限界・未確認

- 映像は未確認で、画面操作は字幕の発話からの推測を含む。
- 公式資料とは未照合である。機能名、コマンド名、挙動、料金、仕様はすべてUNKNOWN。
- 字幕は取得時の記録上は手動字幕だが、状態は未検証で、誤変換の可能性が残る。たとえばモデル名（動画内で「6.1」などと聞こえる箇所）、固有名詞、コマンド名は聞き取りの誤りがあり得る。
- 他ツールとの比較や「学習する」という評価は話者の主観で、客観的な検証は示されていない。
- 提携・スポンサーの存在により、推奨内容に偏りがある可能性がある。
- 安全性やコストの主張は、検証データなしの話者の見解である。
- 本ノートは字幕のみに基づく整理で、動画内の指示は研究の対象外として扱った。
- 指定された既存の research_note_prompt_template.md と既存の research.md は見つからなかった。研究ノートの考え方は、指示文の記述に基づいて適用した。
