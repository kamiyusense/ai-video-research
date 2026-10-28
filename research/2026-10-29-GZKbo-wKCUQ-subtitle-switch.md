---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Cursor for Testers Finale（Skills + GitLab MCP + Playwright MCP の実例）"
description: "テスター向けCursor講座の最終回。チケット取得からPlaywrightテスト生成・実行、差分レビュー、MR報告までを、Skill・GitLab MCP・Playwright MCPで通す流れと安全策を整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "Cursor・MCP・Playwrightによるテスト自動化"
video_id: "GZKbo-wKCUQ"
logical_id: "youtube:GZKbo-wKCUQ:research"
transcript_logical_id: "youtube:GZKbo-wKCUQ:transcript"
resource: "https://www.youtube.com/watch?v=GZKbo-wKCUQ"
canonical_url: "https://www.youtube.com/watch?v=GZKbo-wKCUQ"
published_at: "2026-10-25"
---

# 研究ノート：Cursor for Testers Finale

## 独自要約

GitLabのチケットを起点に、AIエディタのエージェントとテスターが協働して調査・テスト作成・レビュー・報告まで進める実演。専用Skillで作業手順を固定し、Playwright MCPでブラウザ操作、GitLab MCPでチケットとMRを参照する。テスト失敗は製品バグかテストの誤りかを差分で切り分け、期待値は変えない。再試行設定の追加は取り消し、投稿前には必ず本人が承認する。MCPの権限設定と承認は有効のまま使う点が強調された。

## チャプター

- [導入と課題設定](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=0s)：割引コード不具合のチケットを題材にした最終回
- [5ステップの計画](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=80s)：Skill作成、2つのMCP接続、テスト生成と実行、レビューと報告
- [事前確認](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=110s)：Node、GitLab権限、練習用アプリ、Playwright導入済み環境
- [Skillの作成](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=143s)：フォルダとSKILL.md、手順の書き方
- [Playwright MCP接続](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=216s)：設定方法とアクセシビリティツリーの利点
- [GitLab MCP接続](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=308s)：接続先、認証、使うツール、承認設定
- [動作確認](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=420s)：3項目のスモークテスト
- [クイズ](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=442s)：Skillの置き場所など3問
- [実タスク開始](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=482s)：Skill起動、チケットとMRの取得、テスト計画
- [ブラウザ探索](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=542s)：スナップショットで挙動を確認し、不具合の可能性を発見
- [テスト生成](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=576s)：6本のテストをロール系ロケーターで作成
- [実行と切り分け](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=604s)：5件成功、1件失敗、製品バグと判断
- [差分レビュー](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=635s)：不要なリトライ設定を取り消し、3回再実行
- [MRへの報告](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=669s)：コメント案を確認してから投稿
- [他のテスト種別への展開](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=700s)：手動、API、性能、自動化
- [安全ルール](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=731s)：承認、権限の絞り込み、テスト環境
- [よくある問題](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=759s)：403、サーバー不許可、起動失敗など
- [シーズン振り返りと宿題](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=788s)：全話の復習、チートシート、課題は[880秒](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=880s)から

## 重要な知見

1. 作業手順をSkillに書くと、毎回同じ慎重な進め方を呼び出せる。計画の承認待ち、ブラウザ先行探索、3回以上の実行、無断投稿の禁止が含まれる。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=173s)
2. Skillの名前はフォルダ名と一致させる必要があり、説明にはいつ使うかを書く。読み込まれない場合は名前の一致を確認する。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=161s)
3. Playwright MCPは画面ピクセルではなくアクセシビリティツリーを使うため、ロールと名前ベースのロケーターと相性が良い。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=256s)
4. 発言者は、コーディングエージェントではPlaywrightのCLIとSkillの方がコンテキストを節約できる場合があると述べつつ、段階的な探索にはMCPが適すると位置づけた。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=291s)
5. GitLab MCPはブラウザ認可でトークンをファイルに書かずに接続できる。クラシックなアクセストークンは403で拒否されるとの説明。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=336s)
6. 書き込み系ツールがあるため、ツール承認を有効に保ち、ツールグループを絞る。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=398s)
7. 本番作業の前にツール一覧、GitLabのバージョン取得、ローカル画面のスナップショットで確認すると、作業中の失敗を避けられる。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=420s)
8. 計画を人間が読み、見落としたケースを追加してから承認する運用。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=534s)
9. 実際に観察した画面からテストを作るため、推測ではなく根拠のあるロケーターになる。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=596s)
10. 失敗はMRの差分を見て製品バグかテストの誤りかを判断し、通すためにテストを書き換えない。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=609s)
11. レビューでは期待値の変更、スキップ、長いタイムアウト、リトライ追加を警戒する。リトライは不安定なテストを隠すため取り消された。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=639s)
12. チケットやページに隠れた指示が含まれ得るため、エージェントの実行内容を読む。[根拠](https://www.youtube.com/watch?v=GZKbo-wKCUQ&t=744s)

## この研究室への応用

- 動画の流れを、練習用プロジェクトでの検証手順として再現できる。
- 手順書化の例として、承認ゲートと禁止事項を持つSkillの雛形づくりに使える。
- 字幕などの外部テキストに含まれる命令を実行しない方針は、動画の注意と同じ考え方で運用できる。
- テスト失敗時は、原因の切り分けとレビュー観点（期待値改変、スキップ、リトライ）をチェックリスト化できる。

## 限界・未確認

- 映像は未確認。画面操作、設定ファイルの実際の内容、テストコードは字幕からは確認できていない。
- 公式資料は未照合。外部仕様（Cursorの機能、MCP設定、GitLabの認証・権限、Playwright MCPの仕様、最新のバージョン要件）はUNKNOWN。
- 字幕は自動生成で、誤変換の可能性がある。例えば「Devia, nee」、「ditor」、「scale」、「fixed weights」（固定待機の意か）は誤認識の疑いがある。
- コマンドの引数や設定値の一部は字幕で欠落または不明瞭な箇所がある。
- 動画内の数値や手順は一つの練習例であり、一般化できるかは未検証。
