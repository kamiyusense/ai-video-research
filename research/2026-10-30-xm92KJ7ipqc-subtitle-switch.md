---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：REA（Reverse Engineer Anything）チュートリアルとデモ [xm92KJ7ipqc]"
description: "MCPサーバー型のリバースエンジニアリング支援ツールREAを、Ghidraと組み合わせてAIエージェントから使うデモ動画の研究ノート。導入手順、calコマンドの1752年の日付ジャンプ調査、限界を整理する。"
tags:
  - "AI技術研究室"
  - "リバースエンジニアリング支援MCP"
video_id: "xm92KJ7ipqc"
logical_id: "youtube:xm92KJ7ipqc:research"
transcript_logical_id: "youtube:xm92KJ7ipqc:transcript"
resource: "https://www.youtube.com/watch?v=xm92KJ7ipqc"
canonical_url: "https://www.youtube.com/watch?v=xm92KJ7ipqc"
published_at: "2026-10-14"
---

# 研究ノート：REA（Reverse Engineer Anything）

## 独自要約

REAは、バイナリ、Electronアプリ、Webサイトを調べ、その証拠をAIエージェントへ渡すMCPサーバーである。解釈はエージェント側のモデルが担う。ネイティブプログラムの解析には別途Ghidraが必要になる。動画ではOpenCodeに導入し、シンボルを除去したcalコマンド（実体はncal）について、1752年9月の11日間の欠落に関わるコードを自然言語の質問だけで探させた。エージェントはmain関数内の固定日付を見つけ、未追跡の部分も申告した。著者は、最終判断は人間が行うべきだと述べている。

## チャプター

- [冒頭：REAとは何か](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=1s)
- [MCPの説明と「証拠だけ集める」という制約](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=5s)
- [前提条件：Ghidra、Node、Java、エージェント環境](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=50s)
- [OpenCodeとモデル設定、各バージョンの確認](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=80s)
- [NPXによるセットアップウィザード実行](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=122s)
- [MCP一覧での確認とdoctorチェック](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=157s)
- [デモ題材：calの1752年9月の欠落日](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=213s)
- [解析にはプログラムの実体パスが必要](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=287s)
- [エージェントへの質問と実行開始](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=311s)
- [調査フローの図解](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=407s)
- [エージェントの調査結果の確認](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=439s)
- [国別テーブルの検証と限界、注意点](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=508s)

## 重要な知見

1. REAは「証拠収集」に徹し、解釈の質は使うモデルに依存する。ネイティブ解析にはGhidraが別途必要。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=28s))
2. 対応エージェントはOpenCode、Claude Code、Gemini CLIなど複数挙がっている（自動字幕のため名称の誤変換の可能性あり）。デモはOpenRouter経由のモデルで実施された。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=60s))
3. 導入はNPXのセットアップウィザードで、ハーネスを自動検出して統合する。`MCP list`で登録を確認でき、doctorで到達性を点検できる。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=142s))
4. 解析対象は実体のパスで指定する必要がある。calはncalへのショートカットだった。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=287s))
5. プロンプトでREを明示的に指示すると、エージェントはREAを自発的に呼び出した。範囲を絞る指示（他は解析しない）も効いた。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=355s))
6. 調査の流れは、エージェントが質問し、REAがGhidraでコードと証拠（未解明点を含む）を返し、必要なら追質問する反復である。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=407s))
7. シンボルが除去されていて「1752」の検索は空振りだった。そこで関数一覧、逆コンパイル、参照関係の確認に進み、main内で年・月・日の固定値を発見した。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=454s))
8. 「11日」はコード由来でなくモデルの既存知識だと明示された。所要は約1分、費用は1ドル未満と述べられた。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=454s))
9. 国別テーブルの仮説を、別の暦設定で実行して検証した。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=508s))
10. 万能ではなく、判断の代替にならない。自分が所有するか、調査を許可されたソフトだけを解析すべきと注意している。 ([根拠](https://www.youtube.com/watch?v=xm92KJ7ipqc&t=530s))

## この研究室への応用

- 自分のビルド成果物や許可を得たツールの挙動確認に、MCP＋Ghidraの構成を小規模に試せる。
- 「質問の範囲を絞る」「証拠を必ず出させる」「未追跡部分を報告させる」というプロンプト設計は、他のエージェント調査にも流用できる。
- モデルの既存知識とバイナリ由来の事実を分けて記録する運用は、研究ノートの根拠管理に有用。
- 検証は、仮説を実行結果で裏取りする形で行う（動画の国別テーブル確認が例）。

## 限界・未確認

- 映像は未確認で、字幕テキストのみに基づく。画面上の表示内容、バージョン番号、コマンド、プロンプト全文は未確認。
- 公式資料（リポジトリ、ドキュメント）とは未照合。ツールの正式名称、対応範囲、必須バージョンはUNKNOWN。
- 字幕は自動生成で、固有名詞（Ria/Area/Riya表記の揺れ、Cursive、CodeXなど）に誤変換の可能性がある。
- 所要時間・費用・結果の再現性は著者の申告であり、独自検証していない。
- 外部仕様（Ghidra、Node、Java、各エージェントの要件、1752年の暦史）はUNKNOWNとして扱う。
