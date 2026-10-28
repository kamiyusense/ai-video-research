---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Orca（複数コーディングエージェントを1画面で扱うIDE）"
description: "動画で紹介されたオープンソースのエージェントIDE「Orca」について、字幕から読み取れる機能・使用感・応用可能性と未確認事項を整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "Orca"
  - "エージェントIDE"
video_id: "8QgBcI40VC8"
logical_id: "youtube:8QgBcI40VC8:research"
transcript_logical_id: "youtube:8QgBcI40VC8:transcript"
resource: "https://www.youtube.com/watch?v=8QgBcI40VC8"
canonical_url: "https://www.youtube.com/watch?v=8QgBcI40VC8"
published_at: "2026-10-23"
---

# 研究ノート：Orca

## 独自要約（300字以内）

Orcaは、Claude CodeやCodexなど複数のCLI型コーディングエージェントを、ターミナルのまま1つのウィンドウに並べて動かせるオープンソースのアプリだと紹介されている。進捗表示、ファイル閲覧、Git worktree管理、ブラウザ内の要素注釈、使用量の一覧、複数エージェントへの作業分配、モバイルアプリなどを備えるという。投稿者は従来のターミナル型ツールより進捗把握が優れるとして日常的に使っており、強く推奨している。ただし内容は投稿者の主観的デモに基づく。

## チャプター

- [冒頭：Orcaの概要と推奨](https://www.youtube.com/watch?v=8QgBcI40VC8&t=0s)
- [ターミナル中心の設計と進捗表示・ファイルビューア](https://www.youtube.com/watch?v=8QgBcI40VC8&t=38s)
- [複数エージェントの起動とタブ操作](https://www.youtube.com/watch?v=8QgBcI40VC8&t=83s)
- [Git worktreeの作成と削除、使用量の確認](https://www.youtube.com/watch?v=8QgBcI40VC8&t=99s)
- [内蔵ブラウザでの要素注釈とエージェントへの修正依頼](https://www.youtube.com/watch?v=8QgBcI40VC8&t=156s)
- [Git連携、PR作成、各種プレビュー、自動化](https://www.youtube.com/watch?v=8QgBcI40VC8&t=198s)
- [オーケストレーション（複数エージェントへの分担）](https://www.youtube.com/watch?v=8QgBcI40VC8&t=226s)
- [従来ツールとの比較とモバイルアプリ](https://www.youtube.com/watch?v=8QgBcI40VC8&t=318s)
- [総評とその他機能（差分注釈、CLI、スリープ防止など）](https://www.youtube.com/watch?v=8QgBcI40VC8&t=356s)

## 重要な知見

1. 複数のCLIエージェント（Claude、Codexなど）を同一ウィンドウで横並びに動かせるとされる。各画面は素のターミナルで、CLIをそのまま使える。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=38s)
2. 各エージェントの進捗が左側に表示され、起動したエージェントは対応するロゴ付きで並ぶ。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=50s)
3. ブランチ名を指定してエージェントを選ぶと、Gitのworktreeを作成してその中でエージェントが起動する。削除するとGit側のworktreeも片付けられると説明されている。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=115s)
4. 画面下部で、複数エージェントの週次使用量などを一覧できる。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=131s)
5. 内蔵ブラウザでページ要素を選び、コメントとともにエージェントへ送ると、対象要素を指定した修正依頼になる。デモでは見出し文言が変更された。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=165s)
6. 変更一覧の表示、PR作成、画像・動画・PDF・Markdownのプレビュー、定期実行の自動化が可能とされる。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=198s)
7. 設定でスキルを導入すると、タスクを複数エージェントに分配するオーケストレーションが使えるという。デモでは同一課題をClaudeとCodexに並行で任せ、結果を比較した。ただし投稿者はこの挙動を見せるため明示的に指示したと述べている。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=228s)
8. 投稿者の比較では、従来使っていたターミナル型ツールはサブエージェントやbash実行中の進捗追跡が弱く、完了と誤表示することがあったという。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=318s)
9. モバイルアプリで、プロバイダを問わず複数エージェントを1つのアプリで監視できると説明されている。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=343s)
10. 補助機能として、ファイルのドラッグ投入、差分への注釈、Orca CLI、GitHub・Linear連携、スリープ防止が挙げられている。[根拠](https://www.youtube.com/watch?v=8QgBcI40VC8&t=372s)

## この研究室への応用

- 複数エージェントを並行運用する際の、worktree分離＋進捗一覧という運用パターンの参考になる。
- 同一課題を複数モデルに投げて比較する評価手順（結果の横並び比較）を、自室の検証フローに取り入れる案を検討できる。
- UI上の要素指定による修正依頼は、フロント改修の指示精度を上げる手法として試す価値がある。
- 導入するなら、まず小さなリポジトリで進捗誤表示の有無と使用量表示の正確性を自前で確認する。

## 限界・未確認

- 映像は未確認で、字幕テキストのみに基づく。画面上の表示内容は推測を含む。
- 字幕は自動生成で、誤変換の可能性がある（例：他ツール名や固有名詞の表記）。
- 公式資料（リポジトリ、ドキュメント）とは未照合。GitHubスター数、対応エージェント一覧、料金、ライセンス、対応OS、モバイルアプリの提供形態などの外部仕様は UNKNOWN。
- 「最高」「最大の改善」といった評価は投稿者個人の主観であり、客観的な比較検証は行われていない。
- オーケストレーションの自動分配の品質・コスト・失敗時の挙動は動画からは判断できない（UNKNOWN）。
- 投稿者が他ツールを紹介・推奨する立場である点（提供関係の有無）は字幕からは不明。
