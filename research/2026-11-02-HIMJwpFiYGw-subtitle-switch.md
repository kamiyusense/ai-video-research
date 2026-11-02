---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Build an MCP Server in 15 Minutes (2026 Spec)"
description: "MCP仕様2026-07-28に基づき、Python単一ファイルのMCPサーバーを作り、Inspectorで検証し、Claude Code・Cursor・OpenClawに接続する手順と落とし穴、安全上の注意を整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "MCPサーバー構築"
  - "動画研究"
video_id: "HIMJwpFiYGw"
logical_id: "youtube:HIMJwpFiYGw:research"
transcript_logical_id: "youtube:HIMJwpFiYGw:transcript"
resource: "https://www.youtube.com/watch?v=HIMJwpFiYGw"
canonical_url: "https://www.youtube.com/watch?v=HIMJwpFiYGw"
published_at: "2026-11-01"
---

# 研究ノート：Build an MCP Server in 15 Minutes (2026 Spec)

## 独自要約

新しいMCP仕様（2026-07-28）では初期化ハンドシェイクが廃止され、ステートレス化された。動画はPython公式SDKでTODOコメント検索ツールを1ファイルで実装し、AI不要のInspector CLIで検証したうえで、3種のエージェントに同じサーバーを登録する流れを示す。stdoutへの出力禁止、絶対パス、承認確認、ツール説明を信用しない姿勢が要点。

## チャプター

- [導入と全体計画](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=0s)：15分で単一のPythonファイルを作り、新仕様上で3エージェントから使う。
- [今回の5項目の計画](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=21s)：仕様変更、実装、AI抜きの試験、接続、失敗例と安全性。
- [MCPとは何か](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=50s)：tools・resources・promptsの3要素。通信はJSON-RPCで、ローカルは標準入出力。
- [2026-07-28の変更点](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=85s)：ステートレス化、server/discover、セッション削除、resultType、一部機能の非推奨化。
- [環境構築](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=136s)：uvとPython SDK（2.0以上）を使う。
- [サーバー実装](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=167s)：find_todosツール、型ヒントとdocstringの役割、読み取り専用注釈。
- [stdout禁止の規則](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=202s)：ログはstderr経由にする。
- [Inspectorによる検証](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=218s)：protocol eraのlegacy・modern・autoの違いとtools/list、tools/call。
- [生プロトコルの確認](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=253s)：自作の簡易クライアントでserver/discoverを確認。
- [Claude Codeへの接続](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=274s)：claude mcp add、ダブルダッシュの意味、プロジェクトスコープの承認待ち。
- [Cursorへの接続](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=321s)：mcp.json設定とCLIでの有効化。
- [OpenClawへの接続](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=357s)：mcp addとprobe、ツール名の接頭辞の違い。
- [つまずきやすい5点](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=388s)：print混入、_meta欠落、バージョン不一致、相対パス、承認。
- [セキュリティ](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=443s)：ローカルサーバーの権限、ツール説明の扱い、プロンプトインジェクション。
- [まとめと次回予告](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=480s)：読み取り専用から始める。次回はHTTP公開と認証。

## 重要な知見

1. 新仕様はハンドシェイクを廃し、各リクエストがバージョンとクライアント能力を_metaで運ぶ（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=85s)）。
2. サーバーはserver/discoverの実装が必須とされ、対応版と能力を返す（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=98s)）。
3. 公式SDK利用なら変更の大半は吸収されるが、不具合時のため知っておく必要がある（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=126s)）。
4. 型ヒントが入力スキーマ、docstringがモデル向け説明になるので、説明文はモデル向けに書く（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=167s)）。
5. 「stdout is the wire」。余計な出力はJSON-RPCを壊す（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=202s)）。
6. Inspector CLIならAIもAPIキーも不要で試験でき、modernは新版固定、autoはdiscover後にフォールバックする（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=218s)）。
7. Claude Codeでは「--」以降がサーバー側の引数になり、プロジェクトスコープは承認前は保留になる（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=274s)）。
8. Cursor CLIでは未承認だと読み込まれず、有効化コマンドが必要だった（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=321s)）。
9. 同一サーバーを無変更で3エージェントに使えるが、ツール名の表記は環境で異なる（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=357s)）。
10. uv --directoryで作業フォルダが変わるため、相対パスの既定値は誤対象を走査する。絶対パスを渡す（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=388s)）。
11. ローカルサーバーは利用者の権限で動き、ツール説明は信頼できない入力として扱う。版固定・秘密情報の分離・最小フォルダ権限が対策（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=443s)）。
12. 動画の方針は、まず読み取り専用ツールから始め、書き込みは必要時のみ追加すること（[根拠](https://www.youtube.com/watch?v=HIMJwpFiYGw&t=475s)）。

## この研究室への応用

- 社内の調査・整理用ツールを、読み取り専用のMCPサーバーとして1ファイルで試作する際の雛形にできる。
- 導入前の検証手順（AI抜きでInspectorにより一覧と呼び出しを確認）を標準チェックリストに取り込める。
- 複数エージェント共通の接続手順書に、絶対パス・stdout禁止・承認確認の3点を明記できる。
- 外部MCPサーバー導入時のレビュー項目として、ツール一覧の事前確認と版固定を採用できる。

## 限界・未確認

- 映像は未確認で、字幕テキストのみに基づく。画面内の表示やコードの内容は確認していない。
- 公式資料（仕様の変更履歴、SDK文書、各エージェントの文書）とは未照合。
- 字幕の取得区分は手動だが、正確性は未検証で、固有名詞や数値の誤変換の可能性がある。
- 仕様の正式な必須要件、SDKの版番号と挙動、各製品のコマンド仕様、非推奨化の詳細：UNKNOWN。
- 動画内の「本人の環境で取得した」という主張や、チャット画面が再現だという説明は、そのまま検証できていない。
- 概要欄のコードと出典は参照していない。
