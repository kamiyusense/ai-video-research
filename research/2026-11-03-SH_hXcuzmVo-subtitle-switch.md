---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Orcaで複数のClaude Codeを並行実行する（worktreeで衝突回避）"
description: "動画の字幕を資料に、Orca（エージェント並列実行デスクトップアプリ）の仕組み・使い方・注意点を整理した研究ノート。gitのworktreeで作業を分離する点が中心。映像と公式資料は未確認。"
tags:
  - "AI技術研究室"
  - "Orca"
  - "git worktree"
  - "Claude Code"
video_id: "SH_hXcuzmVo"
logical_id: "youtube:SH_hXcuzmVo:research"
transcript_logical_id: "youtube:SH_hXcuzmVo:transcript"
resource: "https://www.youtube.com/watch?v=SH_hXcuzmVo"
canonical_url: "https://www.youtube.com/watch?v=SH_hXcuzmVo"
published_at: "2026-10-25"
---

# 研究ノート：Orcaで複数のClaude Codeを並行実行する

## 独自要約

OrcaはCLI型AIエージェントを並べて動かすデスクトップアプリで、作業ごとにgit worktreeとブランチを作るため、同じファイルを触っても衝突しにくい。動画は複数Issueの同時処理、モデル比較、差分への行メモ、ブラウザ要素の受け渡し、使用量確認を示す。一方で権限は分離されず、統合は人が担う点を注意として挙げる。

## チャプター

- [導入：待ち時間と衝突の問題](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=0s)
- [Orcaの概要（無料・MIT・対応OS）](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=28s)
- [worktreeの仕組みとOrcaでの作成](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=71s)
- [3Issueを3体で同時実行](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=136s)
- [別モデルで比較する](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=183s)
- [差分への行メモと一括送信](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=246s)
- [Design Modeで見た目を修正](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=292s)
- [使用量パネル](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=359s)
- [スマホアプリ（ベータ）](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=386s)
- [その他の機能](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=414s)
- [CLIと動画制作での利用例](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=459s)
- [注意点3つ](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=507s)
- [まとめ](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=583s)

## 重要な知見

1. 衝突回避の中心はgit worktree。フォルダが別なので片方の変更が他方に及ばない（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=71s)）。
2. 新しいworktreeにはgit管理外のファイル（node_modulesや.env等）がなく、設定で用意させられると説明（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=116s)）。
3. 実演では3体が同じstyle.cssを変更しても衝突しなかった（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=162s)）。
4. 同じIssueをHaikuとSonnetに出して比較でき、実装の書き方の差が見える（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=220s)）。
5. 差分の行に付けた複数のメモを、まとめて1つの指示として送れる（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=268s)）。
6. Design Modeで選んだ要素のHTML/CSS情報をエージェントに渡して修正を依頼できる（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=311s)）。
7. Claudeの5時間・週の枠の使用量を、重い作業の前に確認できる（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=368s)）。
8. 動画制作ではシリーズごとにworktreeを作り、CLIで作成と起動を行う運用が紹介された（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=464s)）。
9. worktreeが分けるのはファイルのみで権限は分けない。初期設定は確認なし寄りで、YoloとManualを切替可能（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=511s)、[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=531s)）。
10. 同じ箇所の変更はマージ時に衝突し、解決は人の仕事。レビュー可能な数に絞るべきと述べる（[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=561s)、[根拠](https://www.youtube.com/watch?v=SH_hXcuzmVo&t=574s)）。

## この研究室への応用

- 小さなIssueを2件、別worktreeで同時に試し、待ち時間の短縮効果を測る。
- 同一タスクを複数モデルで比較する手順を、評価ノートの型にする。
- 権限が共有される前提で、重要データを扱う作業はManual運用にする方針を検討する。
- 並行数はレビュー可能な量に合わせる（動画の主張）。

## 限界・未確認

- 映像は未確認。字幕のみを資料としたため、画面内容は字幕の記述に依存する。
- 公式資料は未照合。動画の主張（公式の推奨、ライセンス等）は未検証。
- 字幕は取得上UNVERIFIED。自動字幕ではないとされるが、誤変換の可能性は残る。
- 動画内のバージョン（1.4.239）以降の仕様変更は UNKNOWN。
- 外部仕様（Orcaの設定項目・CLIの詳細・スマホアプリの現状・各サービスの使用量枠）は UNKNOWN。
- 実演は小規模な例であり、大規模リポジトリでの効果は未確認。
