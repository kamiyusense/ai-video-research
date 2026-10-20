# 新しいChatGPT／Claude／Workセッションでの復帰指示（人間が貼る）

以下のコードブロックは利用者が対象プロジェクトへ合わせて記入してから貼る。貼っただけでは外部AIは自動で起動しない。

```markdown
# プロジェクト担当の引き継ぎ
対象GitHubリポジトリ: {{REPO_FULL_NAME}}
役割: {{ROLE_ID}}
対象task_id: {{TASK_ID}}

前チャットの説明を正本とせず、今のGitHubを読み直してください。
最初にrepoの実在、公開範囲、default branch、現在HEAD、関連PRを確認してください。
順番に PROJECT_CONFIG.md / AGENTS.md / MEMORY.md / agents/README.md /
docs/WORKFLOW.md / agents/{{ROLE_ID}}/AGENTS.md / agents/{{ROLE_ID}}/MEMORY.md /
TASKS.md / TASK_REGISTRY.json / 対象成果物とhandoff を読み直してください。
実際に読めなければファイルごとにUNKNOWNを報告してください。

確認できた現在地・未完了・次の安全な作業を短く整理し、
前任と重複しない作業だけ続けてください。
必要な独立検品と担当間の受渡しを区別してください。

外部AI起動、課金、権限変更、Merge、強制push、削除、他repoへの変更、
default branchへの直接書込みは別承認がない限り行わないでください。
GitHubへの保存を行う場合は、承認済の非default branchで行い、
成功不明のwriteを再送せず読み戻してください。
```
