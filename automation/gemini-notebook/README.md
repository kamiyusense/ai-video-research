# Gemini Notebook AI技術研究室: 継続研究Loop v0.2

**目的**: 動画を読む回数を増やすことではなく、Geminiが既存Notebookの知識を使って、自分で新情報を発見し、検証して、差分だけを蓄積し、非公開GitHub正本および次回調査テーマへ循環させる**一連の自動研究ワークフロー**を作る。

## このブランチで実装・接続したもの

| 部品 | 場所 | 段階 |
|---|---|---|
| GeminiネイティブTaskの単一運用指示（全11工程統合） | [GEMINI_TASK.md](GEMINI_TASK.md) | READY_TO_PASTE（Gemini側スケジュール無人実行は未実証） |
| 知識差分からGitHub正式研究記録・知識索引を作る自動ブリッジ | [receipt_to_research.py](receipt_to_research.py) | AUTOMATED_LOCAL_AND_GIT_BRIDGE（テスト実証済み） |
| GitHub正本×全ブランチ統合のNotebook同期用知識索引 | [state/AI技術研究室_知識索引.md](state/AI技術研究室_知識索引.md) | GENERATED_AND_SYNCED |
| 継続研究ステート（Receipt冪等性台帳・次回テーマ・P006課題） | [state/loop_state.json](state/loop_state.json) | GENERATED_AND_SYNCED |
| 自動テストスイート（重複防止・全ブランチ照合・障害停止・Readback） | [tests/test_gemini_notebook_loop.py](../../tests/test_gemini_notebook_loop.py) | CONFIRMED_TEST（7スイート全PASS） |
| 既存担当制と研究台帳 | ルート `AGENTS.md`, `MEMORY.md`, `registry.json`, `docs/SPECIALIST_WORKFLOW.md` | REUSED |

## Google・GitHub 公式連携の調査結果と方式選定（追加従量課金なし）

「Geminiによる研究成果を、非公開GitHubへ人間の手動コピーなしで安全に受け渡す仕組み」について、GoogleおよびGitHubの公式機能を比較した結果は以下の通り（確認日: 2026-10-17）：

| 連携方式 | 公式提供状況 | 追加課金 | 非公開GitHubへの書込み | 評価・採用判断 |
|---|---|---|---|---|
| 1. Gemini WebアプリのGitHub拡張機能 (`Import code`) | 公式あり | 無料（Pro枠内） | **不可（読取専用スナップショットのみ）** | Geminiチャット/Taskから直接 `git push` する機能は存在しない。 |
| 2. Vertex AI / Gemini Enterprise GitHub Connector / NotebookLM Enterprise API | 公式あり（Cloud） | **従量課金・Enterprise契約必須** | 可能（OAuth Action） | 個人サブスク外・追加従量課金禁止の安全条件に抵触するため**不採用**。 |
| 3. 非公式ブラウザ自動化 / Cookie抽出MCP (`notebooklm-py` 等) | 非公式 | 無料 | ローカル経由 | GoogleアカウントのCookie流用・規約/セキュリティリスクがあるため**禁止**。 |
| 4. **公式出力（Google Drive同期 / Docsエクスポート / 1クリック回答コピー）＋ ローカルGit/gh認証ブリッジ (`receipt_to_research.py`)** | **公式機能のみ組合せ** | **追加課金ゼロ** | **可能（非default branchへのcommit/push/readback自動検証）** | **【採用】最も安全で保守しやすく、手作業のJSON切り出し・Git操作をゼロにする方式。** |

### 採用した受け渡し・循環アーキテクチャ

```text
[1〜10] Gemini Task（1回の実行で発見→Notebook参照→重複確認→調査→公式検証→差分抽出→Notebook更新→次テーマ選定）
  │  └─ 最終回答に `research_receipt_v1` の ```json コードブロックを含めて出力
  ▼
[受渡し経路（以下のいずれもJSONの手動切り出し不要）]
  ├─ 経路A（ファイル/Google Drive Inbox）: Google Drive (`G:\マイドライブ\...`) またはローカル `inbox/` に回答ファイル（.md / .txt / .json）を保存 → `--inbox` で自動検出
  ├─ 経路B（1クリック回答コピー）: Gemini回答の「コピー」ボタンを押すだけ → `--from-clipboard` で回答全文からJSONブロックを自動抽出
  └─ 経路C（単一ファイル指定）: `receipt.json` または `response.md` を直接指定
  ▼
[7〜11] `receipt_to_research.py`（ローカル決定論的パイプライン）
  ├─ ① 入力抽出 & バリデーション（HTTPS URL検証、YouTube URL正規化、300字要約上限、字幕全文混入防止）
  ├─ ② 多重の重複防止（Receipt SHA-256冪等性台帳 ＋ 現ブランチ `registry.json` ＋ 全 `origin/*` 並行PRブランチ横断照合）
  ├─ ③ 新規作成（`NEW` → `research/` & `registry.json`）および 既存研究への安全な差分追記（`UPDATED` / `CONFLICT`）
  ├─ ④ 次回研究テーマ（`next_topics`）・未確認事項（`unknowns`）・P006未解決課題を `state/loop_state.json` へ統合
  ├─ ⑤ Notebook還元用の知識索引 `state/AI技術研究室_知識索引.md` を自動再生成（オプションでGoogle Driveフォルダへ自動エクスポート）
  └─ ⑥ 非default branch境界検査・リモート競合チェック・Git Commit・Push・Remote Blob SHA Readback検証・証拠JSON出力
```

## 使い方（ワンコマンドで全工程を反映・検証）

### 1. プレビュー（デフォルト：変更を加えず重複判定・検証のみ実行）
```bash
# JSONファイルまたはGemini回答全文（Markdown）から自動抽出してプレビュー
py automation/gemini-notebook/receipt_to_research.py receipt_or_markdown.md

# クリップボード（Geminiの回答コピー）から直接プレビュー
py automation/gemini-notebook/receipt_to_research.py --from-clipboard

# Inboxフォルダ（ローカルまたは G:\マイドライブ\...）内の未処理ファイルを一括プレビュー
py automation/gemini-notebook/receipt_to_research.py --inbox automation/gemini-notebook/inbox
```

### 2. ローカル反映＋知識索引更新＋Git Commit & Push＋Remote Readback検証
```bash
# ファイルまたはInboxから取り込み、知識索引更新・非default branchへのcommit/push・リモート読み戻し検証まで一括実行
py automation/gemini-notebook/receipt_to_research.py receipt_or_markdown.md --apply --sync-index --commit --push --evidence-out evidence/latest-receipt-import.json

# クリップボードからワンコマンドで取り込み・知識索引更新・GitHub反映・読み戻し検証
py automation/gemini-notebook/receipt_to_research.py --from-clipboard --apply --sync-index --commit --push
```

### 3. 全リモートブランチの最新状態から知識索引だけを再生成する
```bash
py automation/gemini-notebook/receipt_to_research.py --refresh-index-only
```

### 4. 自動テストスイートの実行
```bash
py tests/test_gemini_notebook_loop.py
```

## 正直な未完成部分（未接続・未実証）と次の優先順位

1. **Gemini Web UI / Scheduled Actions 側の実機無人スケジュール実行（未実証）**:
   - `GEMINI_TASK.md` は単一タスクとして完成しているが、Gemini 側で定期実行（Scheduled Actions）を設定した際に Notebook へのソース追加・索引更新が人間の承認クリックなしで完走するかは実機未確認。
2. **Gemini Notebook への `AI技術研究室_知識索引.md` のGoogle Drive自動同期設定（手動紐付け1回が必要）**:
   - スクリプトは `--export-drive-dir` でローカルの `G:\マイドライブ` 配下へ `AI技術研究室_知識索引.md` を自動書き出しできるが、Gemini Notebook 側でその Google Drive ドキュメントをソースとして登録する初回操作はユーザー側で行う必要がある（無断でGoogle Driveの既存ファイルを書き換えない安全設計）。
3. **並行Draft PR群（PR #1〜#9）の統合**:
   - 現在 `3bLrrkA1nlQ`（PR #7/#8）、`ZjUJ-35acaU`（PR #8）、`BStkW1HTfmk`（PR #5）は別ブランチに存在する。本ブランチの `receipt_to_research.py` は `origin/*` 全リモートブランチを自動走査して重複登録をブロックする機能を実装済みだが、将来PRを統合する際は `registry.json` のレコード統合が必要になる。
