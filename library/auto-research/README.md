# 📚 AI技術研究室｜研究ノート自動保存庫

YouTube URLを渡すだけで自動作成された研究ノート（OKF v0.2）と台帳の置き場。

- `youtube-<動画ID>-research.md`：研究ノートOKF（荷札に動画ID・投稿日・チャンネル・字幕の指紋つき）
- `registry.json`：台帳（投稿日・チャンネル・長さ・字幕の文字数とSHA-256・検品結果）
- **字幕原文は入れていない**（著作物のためGitHub保存禁止。PCのObsidian保管庫とGoogleドライブ同期にのみ保存）
- 作成：Gemini（Antigravity CLI）／字幕取得：Google側（字幕取り込み専用Notebook）／検品：引用の実在・指紋の一致を自動確認
- このブランチは自動保存専用。mainへのMergeはユーザー承認制
