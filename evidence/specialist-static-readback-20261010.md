# Evidence｜AI技術研究室・担当制の静的保存検査 2026-10-10

- repo: `kamiyusense/ai-video-research` (private、GitHub metadataで確認)
- branch: `research/video06-specialist-work-design-20261010` (nondefault)
- 起点: 動画05研究PR #3のhead `16ef53f53ed29b7bb780b27ec9162e5ba942f77c`
- 変更: 文書・担当定義・記憶インデックス・研究台帳・模擬試験用仕様のみ
- 検証方式: GitHubから指定branchの実ファイルを再取得し、取得成功と重要なマーカー・一意性・整合性を**コードで静的チェック**（ファイル全面の同一性ハッシュ比較ではない）
- 外部AIモデルを使うLIVEの端末動作: NOT_RUN
- GitHub以外への書込み、課金、APIキー、権限変更、Merge: NOT_RUN

## リモート確認（証拠の内容）
1. **共有文書9件 READBACK_PASS**: `AGENTS.md`, `README.md`, `RESEARCH_ROADMAP.md`, `OPERATIONS.md`, `CHATGPT_PROJECT_INSTRUCTIONS.md`, `MEMORY.md`, `registry.json`, `agents/README.md`, `docs/SPECIALIST_WORKFLOW.md`。
   - 5つの入口が`SPECIALIST_WORKFLOW.md`を参照。
   - `registry.json` は `lC5jxpYmatE`と`Vr3JkAT9mo8`の2件。各1件で重複なし。
   - `MEMORY.md` では自動起動や自動同期が未接続と明記。
2. **担当ファイル10件 READBACK_PASS**: 5つの `agents/<role>/AGENTS.md` と 5つの `agents/<role>/MEMORY.md`。全件存在、role ID が一致、ルートの制約を参照。
3. **研究・プロンプト・mock 7件 READBACK_PASS**: 動画06研究ノート、P007、hand-offテンプレート、映像/独立調査/復帰の3プロンプト、6ケースの静的mock。video_id、取得範囲、UNKNOWN等の必要欄、プレースホルダー、資料の取得限界を確認。

**最終静的チェック結果: PASS（26既存ファイルのremote readback）**。

## mockの意味
`tests/SPECIALIST_HANDOFF_MOCK.md`でM01〜M06の期待される入出力と停止条件を定義した。外部AIやWorkを動かすE2Eテストを実行したわけではない。モデルを用いた実際の担当交代が有効かは未実証。

## 今後の検証と注意
- ChatGPT Web/Work/CodexでAGENTS.mdとMEMORY.mdを**自動で**読む仕様が全環境で成立するとは仮定していない。
- 保存先はGitHubの現在のDraft PRで、mainへの反映は未実施。
- PR #2は別ブランチにあり、`README.md`・`AGENTS.md`・`RESEARCH_ROADMAP.md`の競合可能性がある。後日Mergeする前にfresh比較する。
- 最初の実機E2Eは、相棒が動画1本を選び2つの外部AIを手動起動した後で行う。費用・権限・LIVEは別承認。
