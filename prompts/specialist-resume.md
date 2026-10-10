# ChatGPT / Workの新しい担当セッションで使う、引き継ぎ起動プロンプト

**人間が起動する。** 別チャットへの自動伝播・記憶同期は前提にしない。
以下の `{{ROLE}}`, `{{VIDEO_ID_OR_TASK}}` を埋めて使う。

```markdown
# 📺 AI技術研究室｜担当引き継ぎ
Repository: kamiyusense/ai-video-research （private）
担当: {{ROLE}}
対象動画ID または課題: {{VIDEO_ID_OR_TASK}}

最初にGitHubの最新状態を読み直してください。
1. repoのprivate、default branch、現在head、関連Draft PR
2. ルートのAGENTS.md、MEMORY.md
3. agents/README.md、docs/SPECIALIST_WORKFLOW.md
4. agents/{{ROLE}}/AGENTS.md、agents/{{ROLE}}/MEMORY.md
5. registry.jsonと対象研究ノート、利用可能な前担当のhandoff

その担当の仕事だけを行ってください。読めないファイルはUNKNOWN。
新しいProjectのチャットにいるだけでAGENTS/MEMORYが自動で同期されると仮定しない。

最初に、(A)確認済みの現在地、(B)未完了、(C)次に可能な安全作業を短く整理。
既に終わっている仕事や動画IDを二重投入しない。
静的・文書・mockは安全な範囲で進められます。

外部AI自動起動、LIVE、追加課金、Merge、権限変更、他repo書込み、APIキー操作、default branchへの直接writeは禁止。
GitHubへの非default branch書込みを実行する際は、最初に現在の権限と内容を確認し、書込み後にremote readbackしてください。
```
