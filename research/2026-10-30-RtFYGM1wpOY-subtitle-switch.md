---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：REA - AIエージェント向けリバースエンジニアリング・ツールキット [RtFYGM1wpOY]"
description: "コーディングエージェントに静的解析・逆コンパイル・証拠束を使わせるローカル完結のRE道具REAを紹介した動画の研究ノート。字幕のみ根拠で、数値や仕様は未照合。"
tags:
  - "AI技術研究室"
  - "リバースエンジニアリング"
  - "AIエージェント"
video_id: "RtFYGM1wpOY"
logical_id: "youtube:RtFYGM1wpOY:research"
transcript_logical_id: "youtube:RtFYGM1wpOY:transcript"
resource: "https://www.youtube.com/watch?v=RtFYGM1wpOY"
canonical_url: "https://www.youtube.com/watch?v=RtFYGM1wpOY"
published_at: "2026-10-07"
---

# 研究ノート：REA（AIエージェント向けREツールキット）

## 独自要約

REAは、コーディングエージェントがバイナリやJS/Electronアプリを調べ、文字列・参照・逆コンパイル結果を「証拠束」として得るためのローカル実行ツールである。CLIとMCPサーバーが同じ契約で動き、解析エンジン（Ghidra等）は利用者が用意する。動画は未確認事項を不明として報告する設計と、できないことの明示を信頼の根拠として強調する。

## チャプター

- [導入：エージェントに本格的なRE道具を](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=0s)
- [一つのプロンプトで調査を任せる流れ](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=29s)
- [三段階（逆コンパイル→追跡→自前実装）と規模・保守状況](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=40s)
- [導入手順・要件・エンジン設定・MCP登録](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=97s)
- [doctorによる環境確認とプロバイダ構成](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=204s)
- [証拠束・スナップショット・CLIとサーバーの同一性](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=235s)
- [実行ファイルの解析デモ（セクション・関数）](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=311s)
- [文字列検索から参照関数・逆コンパイルへ](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=358s)
- [JavaScript/Electronの静的解析](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=424s)
- [静的解析の限界（動的関係は未解決）](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=487s)
- [ビルド比較とデバッガ観測](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=505s)
- [シナリオ実行と再構築の比較、ファームウェア/Android](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=540s)
- [できないこと・エンジン別ライセンス・終了処理](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=590s)
- [元ソースは復元できないという明言](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=638s)
- [エージェントの用途と機能化](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=656s)
- [ロードマップ・変更履歴・テスト体制](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=672s)
- [アンインストールと総括](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=725s)

## 重要な知見

1. 主張の中心は「ローカル完結・約94のサブコマンド」。解析は利用者の端末で行うと説明される（[9s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=9s)）。
2. セットアップは変更対象ファイルを事前提示し、承認制・ドライランありと述べる（[105s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=105s)）。
3. 環境診断のdoctorが不足を正直に報告し、修正手段まで示すとされる（[204s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=204s)）。
4. 出力は「観測内容・出所・確信度・未知事項」を持つ証拠束で、根拠なき主張は認めない設計（[235s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=235s)）。
5. CLIとサーバーは同一のワークフローと契約を共有し、結果が一致する（[279s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=279s)）。
6. 文字列検索→参照関数→逆コンパイルという二手の追跡例が示される（[358s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=358s)）。
7. JS/Electronは実行せず静的に解析し、チャンネル一覧などを復元する例が示される（[457s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=457s)）。
8. 静的解析では動的関係が未解決のまま残ると明記される（[489s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=489s)）。
9. 実行シナリオの原版と再構築版を比べ、最初の相違点を示す方式（[540s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=540s)）。
10. エンジン未設定時は代替回答を作らず拒否する設計で、エンジンは利用者が用意する（[592s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=592s)）。
11. 元ソースの復元や、アプリの複製はできないと動画自身が述べる（[638s](https://www.youtube.com/watch?v=RtFYGM1wpOY&t=638s)）。

## この研究室への応用

- 「未知を未知と書く」証拠束の考え方は、本研究ノートの「限界・未確認」運用や、エージェントの出力検証の設計に参考になる。
- 同一契約をCLIとMCPで提供する構成は、自前ツールをエージェントと人間の双方から使える形にする際の雛形になりうる。
- 実導入する場合は、まず信頼できる検証用バイナリや自作物に限り、ライセンスと利用許可を確認した上で試す。

## 限界・未確認

- 根拠は自動字幕のみ。映像（画面表示、コマンド出力、表）は未確認。
- 公式資料（リポジトリ、README、ドキュメント、リリースノート）との照合は未実施。コマンド数・プロバイダ数・ファイル数・版数などの数値は動画の主張であり、正確性はUNKNOWN。
- 自動字幕の誤変換の可能性がある。製品名は字幕中で「Rhea」「R E A」「RAE」と揺れており、正式名称・綴りはUNKNOWN。
- 対応OS、必要バージョン、ライセンス、配布方法、セキュリティ特性などの外部仕様はUNKNOWN。
- 動画は紹介色が強く、第三者による検証や性能比較は含まれない。
