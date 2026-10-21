---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "【研究ノート】デスクツアーならぬソフトウェアツアー！AIエンジニアが仕事で使ってるアプリ・サービスを一式紹介 [sodTFSuV4zY]"
description: "AIエンジニアが個人開発や業務、クリエイティブ、環境構築で実際に使用しているアプリやサービスを紹介するソフトウェアツアー。Claude CodeやOrcaを中心としたエージェント環境運用、Playwrightによるブラウザ自動化、1Passwordでの機密管理、Macの操作効率化アプリなど、個人で活用しているツール構成や具体的な利用方法を解説している。"
resource: "https://www.youtube.com/watch?v=sodTFSuV4zY"
tags:
  - "AI技術研究室"
  - "動画研究"
logical_id: "youtube:sodTFSuV4zY:research"
record_id: "youtube:sodTFSuV4zY"
video_id: "sodTFSuV4zY"
published_date: "2026-10-14"
published_at: "2026-10-14T20:59:23+09:00"
channel: "クロノITチャンネル"
duration_seconds: "1381"
created_at: "2026-10-21"
created_by: "Antigravity CLI (Gemini)"
source_transcript: "youtube:sodTFSuV4zY:transcript"
source_transcript_sha256: "805be0695292e0cf84a08f82482b8d7a5515ca7c9ee4318999d600484b4d0ce0"
time_source: "NONE"
related_records:
  - target_id: "youtube:sodTFSuV4zY:transcript"
    relation: "DERIVED_FROM"
    note: "本ノートの元になった字幕原文"
---

# 【研究ノート】デスクツアーならぬソフトウェアツアー！AIエンジニアが仕事で使ってるアプリ・サービスを一式紹介 [sodTFSuV4zY]

本ノートは字幕原文 [[youtube-sodTFSuV4zY-transcript]] を元にした二次分析です。

## 独自要約
動画では、AIエンジニアが個人で仕事に利用しているソフトウェア環境を紹介している。開発言語はPythonとTypeScriptを採用し、Claude Codeを主軸にしつつCodexをサブエージェントとして併用。ターミナルやエディタはOrcaに集約し、gitのworktreeやDockerを用いてエージェント同士の競合回避や安全性確保を行っている。さらにPlaywrightによるブラウザ自動操作や1Password連携によるAPIキー保護、動画編集ツールのOpenCut、Macの操作性を高める各種ユーティリティなど、AIを組み込んだ実践的な作業環境の全体像が示されている。

## 内容の流れ
- 導入と作業前提（MacBook Proとサブ機Mac miniの構成、個人ツールの紹介趣旨）
- 開発言語とフレームワーク（Python、TypeScript、React、Storybookによる部品管理）
- 日常的に使うAIサービス（Claude Code、Codex、ChatGPT、dots、Gemini Notebook、Aqua Voice）
- エディタとターミナル環境（Orcaへの統合、git worktreeの活用、セッション・ワークスペース運用）
- 開発・インフラ関連ツール（GitHub、GitKraken、Docker、Playwright、ngrok、Cloudflare、Terraform、Tailscale等）
- クリエイティブ制作ツール（OpenCut、Gemini作曲機能、Canva、FigmaからAIによるHTML直接生成への移行、PhotoCraft）
- 業務管理とセキュリティ（Google Workspace、bookrun、1Passwordによる環境変数・MCP保護）
- Macの操作性・環境設定アプリ（Clibor、AutoRaise、Rectangle、Hazel、Ice、Karabiner-Elements）
- まとめとツールの見直し（AIを活用した設定作業の効率化と定期的な環境刷新の推奨）

## 重要な知見
- Claude Codeを開発の主軸とし、ナレッジベースからの起動や自作Webアプリからの単発実行で日常業務を効率化している。「開発はこれを主軸にしてて」
- Codexをサブエージェントとして併用し、不要なコンテキストを渡さずに画像生成やコード・設計の客観的レビューを担当させている。「第三者の意見として使いやすい」
- エディタやターミナルをOrcaに統一し、タスクごとにgitのworktreeを分離してエージェント並列稼働時のファイル競合を防いでいる。「ファイルを踏み合わないように」
- AIエージェントをDockerコンテナ内で実行することで、作業による手元ファイルの破損リスクを隔離している。「壊れるのはコンテナの中だけ」
- PlaywrightのMCPやCLIを利用し、AIに作成ページの表示確認やフォーム入力テストなどのブラウザ操作を代行させている。「ブラウザを操作させるのに使ってる」
- 1PasswordのEnvironmentsとMCPを活用し、AIにAPIキーの実値を渡さずに環境変数名のみを参照させて安全性を確保している。「秘密の値は返さない」
- AIに直接HTMLやCSSを生成させる運用が中心となり、モック作成におけるFigmaの利用が減少しStorybookへの依存度が高まっている。「直接AIにHTMLを起こさせる」
- AIにツールの設定やルール記述を任せられるようになったことで、新しいツールや環境構築を試すハードルが大幅に下がっている。「設定をAIに任せられるようになって」

## この研究室への応用
- rcloneとクラウドストレージの連携による、研究対象の大容量動画ファイルや画像素材の効率的な同期・管理
- Gemini Notebook（旧NotebookLM）を活用した、長尺動画の字幕や関連資料の迅速な検索・要約・論点整理
- Hazel等のファイル監視自動化による、ダウンロードした研究用資料やスクリーンショットの自動分類・整理運用の構築

## 限界・未確認
- 字幕データにタイムスタンプ（時刻情報）が存在しないため、各発言の具体的な再生位置は確認できない。
- 音声自動認識等による字幕取り込みのため、誤変換や固有名詞の表記揺れが含まれている可能性がある。
- 本分析は字幕テキストのみに基づいており、実際の動画内で提示された画面操作、スライド、実演映像等は未確認である。
- 紹介されているツール構成や運用方法はMac環境を中心とした投稿者個人の実践例であり、他OSや他用途での汎用性は検証されていない。
