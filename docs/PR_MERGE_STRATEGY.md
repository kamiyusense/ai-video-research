# AI技術研究室｜PRチェーン構造・第1号運用ブランチ・統合戦略ガイド (`PR_MERGE_STRATEGY.md`)

**改訂日**: 2026-10-18  
**対象リポジトリ**: `kamiyusense/ai-video-research`  
**対象作業ブランチ**: `feature/gemini-notebook-research-loop-20261016` (PR #10 head)  

---

## 1. GitHub上の正確なベースチェーン構造（調査結果）

GitHubのREST API / CLI (`gh pr list`) による fresh readback の結果、本リポジトリの全プルリクエストは以下のように連鎖した階層構造（Stacked PR チェーン）となっています。

```text
main (正本)
  └── PR #1: setup/research-lab (初期化・研究契約)
        └── PR #3: research/video05-task-driven-learning-20261010 (動画05・課題ドリブン学習)
              └── PR #4: research/video06-specialist-work-design-20261010 (動画06・5担当制)
                    └── PR #6: feature/reusable-agent-team-starter-20261010 (共通基盤スターター)
                          └── PR #9: docs/staged-video-handoff-20261014 (動画28本段階的受領)
                                └── PR #10: feature/gemini-notebook-research-loop-20261016 (自動化Loop・Q&A基盤)
```

> [!IMPORTANT]
> **マージ順序の重要認識**:
> PR #9 のベースブランチは `main` ではなく **`feature/reusable-agent-team-starter-20261010` (PR #6)** です。
> したがって、「PR #9 を main にマージして PR #10 の base を main に変更する」という短絡的な2段階マージは、チェーン全体の依存関係を無視した誤認でした。

---

## 2. 第1号の運転方針：「現時点でマージを急がない」

ユーザーの最優先指示に従い、**第1号の運転開始のために不要なマージは一切急ぎません**。

### なぜマージ不要で第1号を運転できるのか？
1. **全成果が PR #10 ブランチ（`feature/gemini-notebook-research-loop-20261016`）に累積している**:
   - PR #10 の作業ブランチは、上流の PR #1 → #3 → #4 → #6 → #9 の全コミット履歴を包含しています。
   - 動画28本の研究記録（`research/*.md`）、知識カタログ（`video_knowledge_catalog.json`）、Q&A検索エンジン（`query_research.py`）、GAS中継スクリプト（`cloud_relay_gas.js`）、テストスイート（28件）が、**すべてこのブランチ1本の中に完全に揃っています**。
2. **安全境界の維持**:
   - 本番GASの中継先ブランチ（`TARGET_GITHUB_BRANCH`）をこの隔離ブランチ（`feature/gemini-notebook-research-loop-20261016`）に固定することで、万が一の誤動作や不正データがあっても `main` や他のブランチを汚損・破壊するリスクをゼロに抑えられます。
3. **実機運転とフィードバックの最優先**:
   - コードのマージ作業に時間を浪費せず、実際にGoogle DriveからReceiptを投入してGitHubに届く「動く第1号」の体験を最優先とします。

---

## 3. 将来の `main` 統合戦略（第1号安定後のフェーズ）

第1号の運転が安定し、ユーザーが「正本 `main` へ完全に統合したい」と判断した段階で、以下のいずれかの方法を手動で選択して統合します。

### アプローチA: チェーン順次マージ（履歴完全保持方式）
1. PR #1 を `main` にマージ。
2. PR #3 の base が `main` に繰り上がるため、PR #3 をマージ。
3. 同様に PR #4 → PR #6 → PR #9 → PR #10 と順番にマージしていく。
- **利点**: 各研究フェーズのブランチ履歴がすべて綺麗に `main` に統合される。
- **注意点**: 手動での確認・マージ操作が6回必要。

### アプローチB: PR #10 直接統合（シンプル方式）
第1号の運用検証が完了した後、PR #10 の内容（全累積成果）を直接 `main` に対するPRとして一本化するか、PR #10 の base を `main` に切り替えて一括マージする。
- **利点**: ユーザーの手動操作が1回で済む。

> [!CAUTION]
> **安全境界ルール**:
> いずれの統合操作も、AIエージェントによる自動実行は厳禁です。必ずユーザー自身がGitHubウェブ画面で承認・実行してください。
