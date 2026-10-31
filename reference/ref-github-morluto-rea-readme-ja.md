---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "参考ノート：REA（Reverse Engineer Anything）日本語README"
description: "バイナリ・アプリ・Web・Android・ファームウェア等をMCP経由でエージェントに解析させるツールREAのREADME（日本語）の要約。インストール方法、対応環境、依存ツール、ライセンスと利用上の注意を整理している。"
tags:
  - "AI技術研究室"
  - "参考資料"
  - "REA"
  - "MCP"
logical_id: "ref:github:morluto-rea:readme-ja"
source_kind: "github_readme"
source_tier: "PRIMARY"
content_status: "READ_VIA_TOOL_SUMMARY"
acquired_at: "2026-10-30"
acquisition_method: "GitHubのREADMEを取得ツールでテキスト化（要約を通した読み）"
resource: "https://github.com/morluto/rea/blob/main/docs/readme/README_ja.md"
canonical_url: "https://github.com/morluto/rea/blob/main/docs/readme/README_ja.md"
related_records:
  - target_id: "youtube:7si7ZFFCZyg:research"
    relation: "COMPLEMENTS"
    note: "同じREAを扱う動画の研究ノート"
---

# REA（Reverse Engineer Anything）README（日本語）

## 独自要約

REAは、バイナリ、アプリ、実行時の動作を、MCPを通じてエージェントに解析させるツール。分析結果には根拠と制限事項が付き、分析は利用者の環境でローカルに行われる。応用例は、既存アプリの仕組みを調べて自分のプロジェクトに実装することや、Webの記録からAIエージェント向けの学習環境（RL環境）を作ること。本体はMITライセンス。

## 内容の流れ

- 目的と使い道
- 主な機能：ネイティブバイナリの逆コンパイル（Hopper／Ghidra／IDA／Kuna）、JavaScript／Electron、.NET、PyInstaller、Android APK（JADX）、Flutter、Unity IL2CPP、Godot、WASM、Webサイトの観測、HAR／pcap、Android実機（adb）、ファームウェア、プロセス動作、SQLite、モデルファイル
- インストール：`npx rea-agents setup`（エージェントを選んで変更を承認、完了後に再起動）、または `npm install --global rea-agents`。更新は `rea update`／`npx rea-agents@latest setup`
- 対応環境：Node.js 22.x／24.x／26以降と npm、Chrome系ブラウザー。Windowsは「Ghidra対応が実験的」。LinuxとmacOSで、プロセス動作の解析にネイティブPTYが必要
- 依存ツール（利用者が用意）：Ghidra／IDA／Hopper／Kuna、JADX＋JDK＋adb、TShark、Binwalk／Unblob、WABT、など
- ライセンス・注意：本体はMIT。商用ツールのライセンスは利用者が用意。クラック版・盗まれたキーは認められない。静的解析はアプリを実行しないが、実行時キャプチャは利用者の権限で対象を実行する。エージェントに渡した結果は、そのモデルのデータポリシーの下で扱われる。目的は法令に従った研究・教育・相互運用・保存など

## 重要な知見

- 設定の `npx rea-agents setup` は、エージェントの設定を書き換え、既存設定をバックアップする。
- 解析の結果を渡すと、そのモデル提供者のデータポリシーが適用される。

## この研究室への応用

- 研究対象は、REAの動画（7si7ZFFCZyg ほか）。導入するなら、設定の書き換えと、ローカル解析の範囲の確認が先。

## 限界・未確認

- READMEは取得ツールの要約を通して読んだ。細かい手順・コマンドは原文で確認が必要。
- 実際にこの環境で動くか、Windowsでの動作は未検証。
