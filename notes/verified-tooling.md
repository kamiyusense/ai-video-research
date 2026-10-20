# 初期技術ノート: 研究室の接続と指示ファイル

確認日: 2026-10-10（Asia/Tokyo）。
確認方法: 公式資料の読み取り。動画由来ではない。動画URL・出典時刻: NOT_APPLICABLE。
LIVE試験・接続設定変更: NOT_RUN。以下はCONFIRMED_DOCであり実機の成功証拠ではない。

## N001: ChatGPTプロジェクト
関連チャット・ファイル・プロジェクト指示をまとめる機能。作成はサイドバーのNew project、
指示の追加はプロジェクトのメニューからProject settingsで行う。
今回の操作一覧には作成・指示変更ツールがない。GitHubへの自動保存や自動同期は確認していない。
出典: https://help.openai.com/en/articles/10169521-projects-in-chatgpt
対応箇所: Create a project / Add project instructions。

## N002: Julesの準備
公式導入資料はGitHubへの接続、対象repositoryとbranchの選択、作業内容の入力を説明している。
repositoryルートのAGENTS.mdを作業文脈に使うことも説明している。
この研究室の改善提案を保存してもJulesの起動やGitHub接続は行われない。
出典: https://jules.google/docs/
対応箇所: Connect GitHub / Starting your first task / Include AGENTS.md file。
本アカウントの接続可否・料金枠・実行権限: UNKNOWN。

## N003: Claude Codeの指示と設定
継続的な指示にはCLAUDE.mdを使う。設定ファイルにはユーザー用・共有プロジェクト用・
ローカル用等の範囲がある。研究室はCLAUDE.mdで方針を渡し、権限設定は変更しない。
出典: https://code.claude.com/docs/en/settings
対応箇所: Settings files and who they affect / Change a setting。
Claude Codeが本研究室で実際に読んだか: UNKNOWN。

## N004: GitHubの作成画面
公式資料は作成画面のowner、name、visibilityの事前入力リンクを説明している。
利用可能なGitHubコネクタにはrepository作成操作がない。privateの確認は作成後に別途行う。
出典: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
対応箇所: Creating a new repository from a URL query。
作成前の対象取得は404だった。その時点では実在・privateはUNKNOWN。
ユーザーの作成後にGitHub metadataを読み戻し、対象の実在・visibility=privateを確認した。
詳細は SETUP_STATUS.md を参照する。

## 研究上の判断
Claudeが根拠を整理しJules向けの仕様を準備する分担は、上の資料を参考にした独自提案。
ChatGPT→Claude→Julesが自動でつながることを示す資料・実行証拠は取得していない。
