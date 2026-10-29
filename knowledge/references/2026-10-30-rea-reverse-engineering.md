---
okf_version: "0.2"
type: "REFERENCE_NOTE"
title: "【参考資料】REA：あらゆるものをリバースエンジニアリング（GitHub README）"
description: "REAは、AIエージェントにMCP経由で解析ツール（Hopper/Ghidra/IDA/Kuna、JADX等）をつなぎ、ネイティブバイナリ、JavaScript/Electronアプリ、.NET、ウェブサイト、APKなどを調べさせるオープンソースの道具。`npx rea-agents setup` でClaude Code、Codex、Gemini CLI、Grok Build等に登録する。"
logical_id: "ref:github-morluto-rea"
source_kind: "GITHUB_REPO"
source_tier: "PRIMARY"
content_status: "READ"
acquisition_method: "raw.githubusercontent.com の docs/readme/README_ja.md を取得、2026-10-30"
resource: "https://github.com/morluto/rea/blob/main/docs/readme/README_ja.md"
canonical_url: "https://github.com/morluto/rea"
author: "morluto"
license: "MIT（READMEのバッジ表記）"
checked_at: "2026-10-30"
tags: ["参考資料", "リバースエンジニアリング", "MCP", "Skill", "解析ツール"]
related_records:
  - target_id: "youtube:7si7ZFFCZyg:research"
    relation: "SAME_TOPIC"
    note: "REAを扱う動画の研究ノート"
    status: "CANDIDATE"
    evidence: "研究ノートの見出し「REAとは何か」。READMEとの内容照合は未実施"
---

# REA（Reverse Engineer Anything）

## 何か
エージェントが「このアプリのこの機能はどう動いているか」を、ソースコードなしで調べるための MCP サーバー。REAが解析ツールで調べて根拠（コード、参照、未解明の点）を返し、エージェントがそれを使って説明・実装・テストをする。

## 使い方の要点
- 導入：Node.js と npm がある環境で `npx rea-agents setup`。使うエージェントを選び、予定の変更を確認して承認する。
- 対応エージェント：Claude Code、Codex、Cursor、Gemini CLI、Grok Build など。ローカルMCPに対応していれば手動登録も可。
- 依頼例：「Notesアプリの検索機能の仕組みを調べ、根拠を示して、私のプロジェクトにも同様の機能を実装して」。
- 公式配布元は morluto/rea、rea.tools、npm の rea-agents だけ。似た名前のリポジトリは公式と確認できない、とREADME自身が警告している。

## 調べられる対象（抜粋）
ネイティブバイナリ（疑似コード・アセンブリ）、JavaScript/Electron（モジュール・IPC）、ウェブサイト（ページ構造・通信）、.NET、Android APK・実機、ファームウェア、パケットキャプチャ、SQLite、GGUF/safetensors のモデルファイル、Unity IL2CPP、Godot、WASM など30種類以上。必要な外部ツールは対象ごとに違う。

## 安全面の注意
- 静的なJavaScript/.NET検査は対象を実行しない。実行時キャプチャは自分の権限で対象を実際に動かす。
- 解析はローカルだが、結果はエージェントのモデル提供元に渡る（READMEのFAQ）。
- 他人のアプリの解析は利用規約・法律の確認が必要（READMEに免責事項の節あり。中身は未精読）。

## 限界
- 読んだのは日本語READMEのみ。リンク先の個別ガイドは未読。
- 導入・実行はしていない（MOCKもLIVEも無し）。
