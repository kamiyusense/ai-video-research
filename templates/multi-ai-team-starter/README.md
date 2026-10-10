# 共通AI担当制スターター v1
状態: TEMPLATE_STATIC_ONLY / NOT_DEPLOYED / NO_AUTOMATION
作成日: 2026-10-10

## 何ができるか
AI製品が違っても、同じGitHubリポジトリのルール・短い記憶索引・仕事の状態を**明示的に読み直し**、前任担当の続きを再開するための共通ひな形。
研究、開発、制作、副業等に横展開できる。専用のAI契約を5つ必要とせず、役割と実行AIは自由に割り当てる。

**ひな形を保存するだけでは、Claude/ChatGPT/Geminiが自動で読み込む・同期する・起動することはない。**
これはAI実行ハーネス、イベント監視、スケジューラ、外部サービス連携の実装ではない。

## 使い始める（人間の承認後）
1. 対象プロジェクトのリポジトリを決め、private/default branchと現在の状態を確認する。勝手に新規リポジトリを作成しない。
2. このフォルダの `project/` **内のファイルだけ**を、対象プロジェクトのルートへ配置する案を作る。既存の `AGENTS.md`・`CLAUDE.md`・`MEMORY.md`・設定ファイルを**上書きせず差分統合案を提示**する。既存repoに既に担当制があるなら最小差分に留める。
3. `PROJECT_CONFIG.md` の未記入項目を埋め、`agents/README.md`の担当名・目的・入出力を合わせて調整する。
4. `AGENTS.md`の対象リポジトリ・許可範囲・停止条件を確認。自動起動、課金、Merge、権限変更、default branch直書きは承認なしで行わない。
5. 文書の整合性を `tests/STATIC_ACCEPTANCE.md` で検品後、ユーザーが許可した非default branchへ保存し、GitHubの内容を読み戻す。
6. 新しいチャットから `prompts/RESUME.md` を利用し、前のチャット無しで最新情報・残作業・次の一手を説明できるか実地試験する。

**このスターター自身を保存したことは、手順2〜6の実行承認や完了を意味しない。**

## 同梱ファイルの読み順
- `project/PROJECT_CONFIG.md`：目的・リポジトリ・制限
- `project/AGENTS.md`：共通ルール
- `project/MEMORY.md`：短い記憶索引
- `project/agents/README.md`：5つの役割と受渡し先
- `project/docs/WORKFLOW.md`：手動運用と安全な作業順
- `project/TASKS.md`・`project/TASK_REGISTRY.json`：タスクの正本・重複検査
- `project/templates/HANDOFF.md`：担当間の伝票
- `project/prompts/RESUME.md`：新チャット復帰
- `project/tests/STATIC_ACCEPTANCE.md`：模擬検証

## 汎用5役割
coordinator=受付／specialist-a=実作業担当A／specialist-b=独立担当B／reviewer=検品／archivist=記録。
役割は入れ替え・省略・増減可能。**5つの外部AIが自動的に動くわけではない**。
研究例: A=映像、B=字幕/一次資料。
開発例: A=実装、B=テスト/調査。
事務例: A=資料整理、B=独立照合。
独立比較が必要ならA/Bは相手の結果を読まずに調べる。

## 守るべき境界
- GitHubの指定リポジトリを唯一の共有正本とする。ローカルコピーは作業用であり、push前の変更は共有済みではない。
- privateであっても秘密情報、認証情報、外部AI報告の全文や大量転載を入れない。
- 書込み先はユーザーが明示的に許可した対象repoの非default branch。衝突・実行結果不明は読み戻し優先。force push、削除、Merge、権限変更を勝手にしない。
- 識別子が同じ成果物は更新候補とし、重複作成しない。後任は必ずfresh readback。
- 他プロジェクトへ展開するまではこの研究室の外を変更しない。

## 出自と依存
`kamiyusense/ai-video-research` の担当制（coordinator / visual / research / reviewer / archivist）を**汎用化した独自テンプレート**。
このテンプレートの保存ブランチは研究室のPR #4に由来する。PR #5のObsidian案を必要条件としない。
