---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Claude Code Desktop・Orca・Herdrの使い分け [W5qwlYBnWa4]"
description: "Claude Code Desktop、Orca、Herdrの特徴と使い分けを整理した動画の研究ノート。Claude専用の統合環境、複数エージェント比較IDE、軽量ターミナル管理の違いと注意点をまとめる。"
tags:
  - "AI技術研究室"
  - "Claude Code Desktop"
  - "Orca"
  - "Herdr"
video_id: "W5qwlYBnWa4"
logical_id: "youtube:W5qwlYBnWa4:research"
transcript_logical_id: "youtube:W5qwlYBnWa4:transcript"
resource: "https://www.youtube.com/watch?v=W5qwlYBnWa4"
canonical_url: "https://www.youtube.com/watch?v=W5qwlYBnWa4"
published_at: "2026-11-02"
---

# 研究ノート：Claude Code Desktop vs Orca vs Herdr

## 独自要約

AIコーディングエージェントを扱う3つのツールの棲み分けを説明する動画。Claude Code DesktopはClaude専用で、並列セッション、レビュー、PR管理まで一通り揃う。Orcaは複数のエージェントに同じ課題を競わせて差分を比較するIDE。Herdrはターミナル内で動く軽量な管理ツールで、状態一覧と常駐が強みだが、レビューやPRの機能は持たない。結論は、Claudeだけなら現状維持、他社エージェントも契約していれば比較用にOrca、キーボード中心の運用ならHerdr、という使い分けである。

## チャプター

- [冒頭：問題提起](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=0s)：乗り換えるべきかという問い。
- [3ツールの位置づけ](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=19s)：いずれもモデルではなく、サインインと課金は別。
- [Claude Code Desktop](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=44s)：セッション設定、並列作業、レビュー、PR追跡。
- [Orca](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=93s)：worktreeで競わせる運用と権限設定。
- [Herdr](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=143s)：ターミナル内の管理、サイドバー、デタッチ。
- [比較と結論](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=191s)：使い分けの基準。
- [締め](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=228s)：説明欄のリンクとコメント依頼。

## 重要な知見

1. OrcaとHerdrは自前のモデルを持たず、既に利用できるエージェントを動かす。サインインと請求は各々別（[33s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=33s)）。
2. Desktopのセッションは、実行場所・フォルダ・権限モード・モデルの4つの選択から始まる（[44s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=44s)）。
3. 並列作業は、セッションごとに専用のGit worktreeを割り当てて衝突を避ける（[57s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=57s)）。
4. レビューは差分行へのコメントや修正適用で行え、組み込みブラウザでの自己確認もできる（[65s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=65s)、[73s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=73s)）。
5. GitHub CLI連携で、CI失敗の自動修正や自動マージの設定ができる（[83s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=83s)）。欠点はClaude専用である点（[90s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=90s)）。
6. Orcaは同じ起点から複数worktreeを作り、複数エージェントに同一プロンプトを与えて比較する（[102s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=102s)）。
7. Orcaは初期設定で承認プロンプトが無効になるとされる。worktreeが隔離するのはファイルであってコマンドではないため、信頼できない作業は手動承認が推奨されている（[109s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=109s)、[116s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=116s)）。
8. worktreeを削除するとブランチも消えるので、負けた側を消す前に必要なものを保存する（[133s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=133s)）。代償は新しいIDEを覚える手間（[140s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=140s)）。
9. Herdrは既存のターミナル上で動く小型プログラムで、サイドバーに各エージェントの状態（作業中・待機・完了など）が出る（[143s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=143s)、[158s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=158s)）。
10. デタッチしてもバックグラウンドで稼働し続け、再接続できる。エージェントが補助エージェントを起動する機能やSSH機の一覧もある（[168s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=168s)、[175s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=175s)）。差分レビューとPRの道具はなく自作になる（[185s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=185s)）。
11. 判断基準：Claudeのみなら現状維持、Codex等も契約済みで比較したいならOrca、軽量なキーボード操作ならHerdr（[195s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=195s)）。併用も可で、Desktopを拠点にする案（[217s](https://www.youtube.com/watch?v=W5qwlYBnWa4&t=217s)）。

## この研究室への応用

- 複数エージェントに同一課題を投げて差分を比べる手法は、研究室のモデル比較の手順に取り入れられる。
- 権限設定を最初に確認する習慣（特にOrcaの初期状態）を、検証環境の運用ルールに入れる。
- 並列作業はworktreeで分離する方針を、自分の作業にも試す価値がある。
- 長時間タスクの状態把握には、Herdrのような状態一覧の考え方が参考になる。

## 限界・未確認

- 映像は未確認で、字幕のみに基づく。画面上の操作や表示は確認していない。
- 公式資料は未照合。機能名、初期設定、挙動の正確さは動画の主張のままである。
- 字幕は取得元で手動扱いだが、転記誤りや固有名詞の誤変換の可能性は残る（transcript_statusはUNVERIFIED）。
- 各ツールの価格、対応OS、最新バージョン、セキュリティ仕様などの外部仕様：UNKNOWN。
- 動画は説明欄のドキュメントを参照するとしているが、そのリンク先は未確認。
