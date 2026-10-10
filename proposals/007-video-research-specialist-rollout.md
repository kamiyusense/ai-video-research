# P007｜AI動画研究室の担当制を段階導入

- proposal_id: P007
- 記録日: 2026-10-10
- 親研究: `research/2026-10-10-Vr3JkAT9mo8-work-specialists.md`
- 状態: **PHASE_A_STATIC_IMPLEMENTED / PHASE_B_C_NOT_RUN**
- 許可範囲: 研究室リポジトリへの非default branchのドキュメント作成・静的検証
- ユーザーが望む最終状態: 動画URLだけで必要な専門担当が研究、検品、保存と改善案をつなぎ、前回の続きを説明なしで再開できる。ユーザーの視聴・調査・コピペ時間を減らす。
- 本番自動Loop/外部モデル実行の承認: NOT_AUTHORIZED

## Phase A：今回実装した土台（STATIC）
- [x] `MEMORY.md`：研究室共通の索引、個人プロフィールではなく知識・未解決・進捗の道案内。
- [x] `agents/README.md`：5役割と受渡し契約。
- [x] `agents/{coordinator,visual,research,reviewer,archivist}/AGENTS.md`：担当別ルール。
- [x] `agents/<role>/MEMORY.md`：各担当の短い引き継ぎ。
- [x] `docs/SPECIALIST_WORKFLOW.md`：受付→独立映像/調査→検品→独自要約保存。
- [x] `templates/handoff-envelope.md`：取得範囲、video_id、結果、根拠、次の作業。
- [x] `prompts/specialist-{visual,research,resume}.md`：コピペ式依頼文。
- [x] `tests/SPECIALIST_HANDOFF_MOCK.md`：失敗条件を含めた静的mock。
- [ ] 外部AIを別セッションで動かした実地試験：NOT_RUN。
- [ ] GitHubのmainへの統合：未承認。

## Phase B：現行のPlus/Google AI Proで小規模運用（次段階）
1. ユーザーから動画1件を受け取る。既存台帳を照合。
2. ユーザーがAI StudioまたはSparkを起動し、異なる調査指示を送る。
3. 入手した短い結果をChatGPTへ渡し、reviewerが根拠・時刻・動画公開時点の仕様を検品。
4. 判断して必要な知識だけarchivistがGitHubの非default branchへ保存、remote readback。
5. 新しいChatで `prompts/specialist-resume.md` を使い、過去チャット無しで最新の状態を復元できるか確認。
6. 効果測定：相棒によるコピペ回数、重複調査、受渡し失敗、修復に要した操作。

**合格条件**: 1本を重複なしに最後まで扱える、担当交代後に必要情報を再読込できる、動画/公式/提案を区別できる、追加課金0、無断LIVE0、main直接書込み0。

## Phase C：Work・自動収集・継続Loop（別途検証・承認）
- Workを使った受付・検品・記録のバッチ化。プランの枠とローカル/クラウドの違いを先に確認。
- WorkのクラウドブラウザでGoogle AI Studio/Gemini Sparkを実際に操作して回収できるか、権限と規約を守った小さな試験で判断。できると決めつけない。
- 連続したタスクの状態・優先順位・停止条件、二重実行防止、エラー復旧、費用上限を設計。
- ユーザーが「API課金なし」を望む限り、APIキーが必須の自動連携は採用しない。既存の契約認証とUIワークフローを比較。
- 自動起動・Merge・権限設定・追加課金・外部サービスへの一括情報送信は別承認。

## 既存PRとの関係
初期化PR #1がbase。動画05のPR #3がこの担当制実装の祖先。プロジェクト立上げ時の目的/ボトルネック管理PR #2は別派生で、同じREADME・AGENTS.md・RESEARCH_ROADMAP.mdを更新している。今後統合する場合には**順番と競合をfresh readbackして解消**。この提案は勝手にMergeしない。

## なぜ専用のローカル記憶を作らないか
投稿者の方式ではローカルフォルダのAGENTS/MEMORY/Resourcesを利用。研究室はprivate GitHubに既存研究・台帳があり、二重保存すると不一致になる。GitHub唯一正本で、必要なファイルだけ担当へ渡す方式から始める。**GitHubに書くだけでは他サービスへ自動同期しない。**
