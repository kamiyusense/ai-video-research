# AI技術研究室｜PC-OFF無人稼働運用仕様書・安全設計ガイド

**改訂日**: 2026-10-17  
**対象システム**: `automation/gemini-notebook/` (v0.5)  
**運用目標**: ユーザーのローカルPCが電源OFFの状態でも、Geminiによる動画調査とGitHubリポジトリへの成果蓄積を安全・自律的に継続する。

---

## 1. 全体アーキテクチャ概要

ローカルPCに依存せず、Google Cloud（Gemini / Drive / Apps Script）とGitHub Cloud間で完結する完全クラウド中継構成をとります。

```mermaid
flowchart TD
    subgraph Google_Cloud["Google Cloud / Workspace (PC-OFF環境)"]
        G1["Gemini (Scheduled Actions / プロンプト)"] -->|"動画調査・構造化"| G2["Gemini Notebook\n(44ソース・総合索引)"]
        G1 -->|"research_receipt_v1 (JSON)"| D1["Google Drive\nAI技術研究室_受信トレイ/"]
        
        T1["GAS 時間主導型トリガー\n(例: 1時間おき)"] -->|"自動起動"| GAS["Google Apps Script\n(cloud_relay_gas.js v0.5)"]
        D1 -->|"Receipt未処理検知"| GAS
        GAS -->|"処理済みファイルを退避"| D2["Google Drive\n処理済み/"]
        GAS -->|"最新Index同期書き出し"| D3["Google Drive\ngithub_knowledge_index_export.md"]
    end

    subgraph GitHub_Cloud["GitHub Cloud (Private Repository)"]
        GAS -->|"GitHub REST API\n(PAT最小権限)"| GH1["feature/gemini-notebook-research-loop-20261016\n(Draft PR #10)"]
        GH1 -->|"正本コミット&Blob SHA検証"| GH2["research/*.md\nregistry.json\nloop_state.json"]
    end
```

---

## 2. 稼働状況の厳格な区分（Mock / Ready / Live）

本研究室の最重要ルールに従い、稼働状態を明確に区分します。

| 項目 | 現在のステータス | 判定根拠 |
|---|---|---|
| **ローカル検証（単体・結合テスト）** | **PASS（完了）** | 18件の自動テスト全通過、Case A〜Fの実用検索確認、100本バッチ正規化テスト通過 |
| **GAS中継コード実装** | **WIRED_READY（準備完了）** | `cloud_relay_gas.js` v0.5（3348行）実装済み、Contract Spec・セキュリティ検査準拠 |
| **Google Drive 実フォルダ** | **READY_FOR_LINK（未配線）** | フォルダ構造設計済み（実環境でのフォルダID紐付け待ち） |
| **本番クラウド定期稼働 (Live Trigger)** | **NOT_WIRED（未接続・待機）** | **本番GASデプロイ・定期トリガー設定は未実施**。ユーザー明示承認と手動設定が必要 |

> [!IMPORTANT]
> **本番未稼働の明示**:
> 現在は「PC上でコードを完全実装し、モック・結合テストで動作保証した状態」であり、**Google Workspace上でクラウド中継が実際に自動定期稼働しているわけではありません**。本番自動実行を稼働中と報告してはいけません。

---

## 3. PC-OFF無人稼働のための5大安全境界

1. **mainブランチ直接書き込みの絶対拒否**:
   - `CONTRACT_SPEC_V1.forbidden_branches` により、`main` / `master` への直接コミット・プッシュはコードレベルで即座に例外停止します。
   - すべての自律中継は隔離作業ブランチ（`feature/gemini-notebook-research-loop-20261016`）および Draft PR #10 へ向けられます。
2. **秘密情報・認証情報の機械的遮断**:
   - GitHub PAT、Google APIキー、LLMシークレットキー、Bearerトークン等を正規表現パターンで検査し、1文字でも含まれていればリレー処理を中止（STOP）します。
3. **字幕全文・機密著作物の転載ブロック**:
   - SRT/WebVTTタイムコード形式、3行以上の連続字幕文字起こし、長文転載（過剰な改行）を機械的に検知し拒否します。
4. **推測タイムスタンプの排除**:
   - `allowed_timestamp_sources` から推測ハック（`OFFICIAL_TIME_RANGE`）を全廃。
   - `YOUTUBE_CHAPTER_METADATA`、`TIMESTAMPED_CAPTIONS`、`VISUAL_FRAME_CHECK` のいずれかの客観的証拠がない箇所はすべて `UNKNOWN` とし、`&t=` 再生リンクを生成しません。
5. **GAS 9KBプロパティ制限の保護とGitHub正本SSOT化**:
   - GASの `ScriptProperties` に全履歴を溜め込まず、GitHub側の `loop_state.json` を正本（SSOT）として参照・更新します。

---

## 4. ユーザーによる本番LIVE接続手順（要手動承認）

PC-OFF無人運用を実際に開始する際は、ユーザーが以下のステップを手動で実行します（AIによる勝手な外部LIVEデプロイ・トークン発行は禁止されています）。

### Step 1: Google Drive フォルダの準備
Google Drive上に以下のフォルダを作成します：
- `AI技術研究室_受信トレイ` （Geminiの出力先、GASの監視元。必須）
- （任意で保管用フォルダを設ける場合も、GAS側は非破壊インプレース重複判定を行うためファイル消失の危険はありません）

### Step 2: Google Apps Script プロジェクトの作成
1. [Google Apps Script](https://script.google.com/) で新規プロジェクトを作成。
2. `automation/gemini-notebook/cloud_relay_gas.js` の全文を貼り付けて保存。

### Step 3: スクリプトプロパティ（Script Properties）の設定
GASの「プロジェクトの設定」>「スクリプト プロパティ」に以下を登録：
- `GITHUB_FINE_GRAINED_PAT`（または `GITHUB_PAT`）: リポジトリへの書き込み権限（Contents: Read & Write）を持つFine-grained PAT（最小権限）
- `DRIVE_INBOX_FOLDER_ID`: `AI技術研究室_受信トレイ` のフォルダID（必須）
- `DRIVE_EXPORT_DOC_ID`: GitHub正本の知識索引をミラー同期するGoogle DocsのドキュメントID（任意）
- `TARGET_GITHUB_BRANCH`（または `TARGET_BRANCH`）: 対象作業ブランチ（省略時: `feature/gemini-notebook-research-loop-20261016`。main/masterはコードレベルで拒絶）

> [!NOTE]
> **ファイル退避・移動処理について（実装仕様）**:
> `cloud_relay_gas.js` v0.5 は受信トレイ内のファイルを移動・削除せず、**インプレース（非破壊的）に完全重複防止**を行います。
> 処理済みReceiptのダイジェスト（SHA-256）はGitHub正本（`loop_state.json`）および揮発キャッシュに記録されるため、受信トレイに同名ファイルが残っていても二重コミットやファイル破壊は発生しません。
> `DRIVE_PROCESSED_FOLDER_ID` や `DRIVE_ERROR_FOLDER_ID` は現在のコードでは未参照（未使用）であり、ファイル消失リスクを回避する設計となっています。

### Step 4: トリガー（時間主導型）の有効化
GASの「トリガー」設定画面から：
- 実行する関数: `runCloudRelayLoop_`（または `relayDriveReceiptsToGitHub`）
- イベントのソース: `時間主導型`
- 時間の間隔: `1時間おき`（または1日数回）

---

## 5. 異常検知・安全停止と再試行ポリシー

- **Receipt破損・バリデーションエラー**:
  - `status: "REJECTED_VALIDATION_BEFORE_GITHUB_WRITE"` としてレポートに記録され、GitHubコミットは一切実行されません。元ファイルはそのまま保持され、手動調査が可能です。
- **外部書き込み成功不明・ブランチ競合 (422)・Tree Truncated**:
  - **無条件の再試行は行いません**。ネットワーク不達やRef更新の不明なステータス時は `STOPPED_ON_UNKNOWN_REF_UPDATE_NO_RETRY` や `STOPPED_ON_BRANCH_CONFLICT_422_NO_OVERWRITE` として安全停止し、当該Receiptを `haltedReceipts` に記録します。
  - 次回実行時はGitHub側のリモートHEADおよび正本 `loop_state.json` を **remote readback** してコミット済みかを照合し、重複コミットを絶対に防止します。
- **同時実行排他制御**:
  - `LockService.getScriptLock()` による排他ロックを取得。多重起動時は `SKIPPED_CONCURRENT_LOCK_HELD` で安全スキップします。
