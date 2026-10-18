# AI技術研究室｜第1号 本番接続・運転開始プレーブック (`V1_PRODUCTION_PLAYBOOK.md`)

**作成日**: 2026-10-18  
**対象システム**: `automation/gemini-notebook/` (v0.6)  
**対象作業ブランチ**: `feature/gemini-notebook-research-loop-20261016` (PR #10 head)  
**運用方式**: **半自動方式（人間によるJSON配置 ＋ GASによる完全クラウド自動中継）**

---

## 1. 第1号の基本構成と受入基準（条件A〜E）

第1号では、無理な完全無人化や過剰な外部API課金を避け、人間とクラウドの得意分野を分担した**最も堅牢で持続可能な半自動アーキテクチャ**を採用します。

```text
【日常の運用フロー】
ユーザー (PCまたはスマホ)
   │ ① Geminiで動画を調査・JSON出力 (1〜2分)
   ▼
Google Drive (AI技術研究室_受信トレイ/) にJSONを配置 (数秒)
   │ 
   │ ※ここからPCをシャットダウンして就寝・外出可能 (PC-OFF)
   ▼
Google Apps Script (cloud_relay_gas.js) [時間主導型トリガー: 1時間おき]
   │ ② 検証・秘密情報遮断・非破壊的重複排除
   ▼
GitHub (feature/gemini-notebook-research-loop-20261016)
   │ ③ 単一アトミックコミット & Remote Readback
   ▼
GitHub正本の知識カタログ更新・保存確認
   │ ④ 必要に応じてNotebookへ最小手動反映
   ▼
Gemini Notebook で深掘り質問・知識を日常再利用
```

### 第1号の受入基準（条件A〜E）達成状況
- **条件A（研究結果の作成）**: `GEMINI_TASK.md` に準拠した `research_receipt_v1` 形式の出力プロンプト整備済み。
- **条件B（Google Drive受渡し）**: 受信フォルダ `AI技術研究室_受信トレイ` を選定。インプレース重複排除によりファイル消失ゼロ。
- **条件C（GASによるGitHub保存）**: `cloud_relay_gas.js` v0.6 実装済み。トークン漏洩スキャン、アトミックコミット、409/422競合時の安全停止対応。
- **条件D（本番E2E検証）**: 以下のTEST 1〜7の手順を策定。本番初回テスト用Fixture（非破壊スモークテストデータ）を用意。
- **条件E（研究の再利用）**: ローカルCLI対話モード（`run_qa.ps1`）およびGemini Notebookへの最小手動反映フローを整備。

---

## 2. ユーザー事前準備（初回のみ・所要時間 約10分）

本番接続を開始する際、ユーザーが手動で行う初期設定手順です。

### Step 1: Google Drive 受信フォルダの作成
1. Google Drive（ブラウザまたはアプリ）を開きます。
2. 新規フォルダを作成し、名前を **`AI技術研究室_受信トレイ`** とします。
3. フォルダを開き、ブラウザのアドレスバーのURLを確認します：
   `https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i...`
4. `/folders/` の後ろにある英数字文字列（これが **`DRIVE_INBOX_FOLDER_ID`** です）をメモします。

### Step 2: GitHub Fine-grained PAT の発行（最小権限）
1. GitHubの [Personal Access Tokens (Fine-grained)](https://github.com/settings/tokens?type=beta) を開きます。
2. **「Generate new token」** をクリックします。
3. 以下のように最小権限で設定します：
   - **Token name**: `ai-video-research-gas-relay`
   - **Expiration**: 30日〜90日（推奨）
   - **Resource owner**: `kamiyusense`
   - **Repository access**: **Only select repositories** を選び、**`kamiyusense/ai-video-research`** を選択。
   - **Permissions** > **Repository permissions**:
     - **Contents**: **Access: Read and write** （※これ以外の権限はすべて No access にする）
4. **「Generate token」** をクリックし、生成されたトークン（`github_pat_...`）をコピーします（画面を閉じると二度と表示されません）。

### Step 3: Google Apps Script（GAS）プロジェクトの作成とコード配置
1. [Google Apps Script ホーム](https://script.google.com/) を開きます。
2. 左上の **「新しいプロジェクト」** をクリックします。
3. プロジェクト名を `ai-video-research-cloud-relay` に変更します。
4. エディタ内の `Code.gs` に最初からあるコードを全消去します。
5. 本リポジトリの **[`automation/gemini-notebook/cloud_relay_gas.js`](file:///c:/Users/yuuki/Documents/ai-video-research/automation/gemini-notebook/cloud_relay_gas.js)** の全文をコピーし、エディタに貼り付けて **保存（Ctrl+S）** します。
   - ※外部ライブラリの追加は一切不要です（単一スタンドアロンで動作します）。

### Step 4: スクリプトプロパティ（Script Properties）の設定
1. GASエディタの左メニューにある **「プロジェクトの設定」**（歯車アイコン）をクリックします。
2. ページ下部の **「スクリプト プロパティ」** セクションで **「スクリプト プロパティを追加」** をクリックし、以下を登録します：

| プロパティ名 | 設定値 | 必須/任意 | 説明 |
| :--- | :--- | :--- | :--- |
| **`GITHUB_FINE_GRAINED_PAT`** | `github_pat_...` (Step 2でコピーしたトークン) | **必須** | GitHubへのコミット認証用 |
| **`DRIVE_INBOX_FOLDER_ID`** | Step 1でメモしたフォルダID | **必須** | 受信フォルダのID |
| **`TARGET_GITHUB_BRANCH`** | `feature/gemini-notebook-research-loop-20261016` | **必須** | 保存先作業ブランチ（※main/masterはコードレベルで拒絶） |
| **`DRIVE_EXPORT_DOC_ID`** | （空白のままでOK） | 任意 | 知識索引をGoogle Docsにミラー同期する場合のみ指定 |
| **`DRY_RUN`** | `true` または `false`（デフォルトは未設定/false） | 任意 | `"true"` に設定すると `runCloudRelayLoop` でも書き込みを抑止してプレビューのみ実行 |

3. **「スクリプト プロパティを保存」** をクリックします。

---

## 3. 本番運転テスト計画（TEST 1〜TEST 7）

設定完了後、以下の順序で動作を確認します。

### TEST 1: 構成・認証確認（空フォルダでの初回 Dry-Run 手動実行）
1. GASエディタに戻り、画面上部の実行関数ドロップダウンで **`runCloudRelayDryRun`** を選択します。
2. **「実行」** ボタンをクリックします。
3. 初回実行時、「承認が必要です」というダイアログが表示されるので、ご自身のGoogleアカウントを選択し、アクセスを許可します（Google Driveおよび外部API GitHubへの通信）。
4. 実行ログ（Execution log）を確認します。JSON形式で以下のように出力され、エラーなく `Execution completed` となれば接続・認証成功です：
   ```json
   {
     "status": "COMPLETED",
     "mode": "DRY_RUN",
     "targetBranch": "feature/gemini-notebook-research-loop-20261016",
     "applicationBranchGuard": "ENFORCED_NON_DEFAULT_ONLY",
     "relayReport": [],
     "driveReconciliation": null,
     "notebookSyncStatus": "NOT_SYNCED_FROM_GITHUB"
   }
   ```
   > [!NOTE]
   > `runCloudRelayDryRun` はGitHubリポジトリのブランチ・ファイル構造の読み取り（GET）のみを行い、コミット・プッシュ（POST/PATCH）は一切行いません。

### TEST 2: 受信・検証テスト（Dry-Run プレビュー → 承認後単発LIVE保存）
台帳へ架空の動画・主張を保存せず、かつ「新規保存」の成功を客観的に証明するため、2種類の検証データを用意しています：
- **予行演習用**: `test_sample_receipt_v1.json`（既存動画 `sodTFSuV4zY`。台帳を増やさずにGAS接続と更新系動作を確認）
- **本番新規保存実証用**: `live_sample_receipt_v1.json`（実在する未登録動画 `kCc8FmEb1nY`。新規1件の確実な保存を証明）

#### Step 2A: Dry-Run プレビュー検証（GitHub書き込みなし・非破壊）
1. まずは予行演習または本番新規実証用のいずれかを選択します：
   - **本番新規保存を実証する場合**: リポジトリ内の **[`automation/gemini-notebook/fixtures/live_sample_receipt_v1.json`](file:///c:/Users/yuuki/Documents/ai-video-research/automation/gemini-notebook/fixtures/live_sample_receipt_v1.json)** をダウンロード。
   - ※未登録の実在動画 `kCc8FmEb1nY`（Andrej Karpathy氏 nanoGPT講義）の実データであり、未検証時刻は誠実に `UNKNOWN` と記録されています。
2. Google Driveの `AI技術研究室_受信トレイ` フォルダにアップロードします。
3. GASエディタで **`runCloudRelayDryRun`** を再度 **「実行」** します。
4. 実行ログを確認します。GitHubへのコミットは発生せず、安全に検証・新規差分プレビューが行われたことを確認します：
   ```json
   {
     "status": "COMPLETED",
     "mode": "DRY_RUN",
     "relayReport": [
       {
         "file": "live_sample_receipt_v1.json",
         "status": "DRY_RUN_PREVIEW_ONLY_NO_GITHUB_WRITE",
         "githubWriteStatus": "PREVIEW_ONLY",
         "wouldCommit": true,
         "newRecordsCount": 1,
         "updatedRecordsCount": 0,
         "newIds": ["kCc8FmEb1nY"]
       }
     ]
   }
   ```

#### Step 2B: ユーザー承認後の単発LIVE保存テスト（初回本番書き込み）
Dry-Runで `newRecordsCount: 1` と差分プレビューが正常であることを確認した後、ユーザー承認のもとで実際にブランチへ1度だけ書き込みます。
1. GASエディタで実行関数を **`runCloudRelayLoop`** に切り替えます。
2. **「実行」** ボタンをクリックします。
3. 実行ログを確認します：
   ```json
   {
     "status": "COMPLETED",
     "mode": "APPLY",
     "relayReport": [
       {
         "file": "live_sample_receipt_v1.json",
         "status": "COMMITTED_AND_READBACK_VERIFIED",
         "githubWriteStatus": "COMMITTED_AND_READBACK_VERIFIED",
         "headSha": "...",
         "videoIds": ["kCc8FmEb1nY"]
       }
     ]
   }
   ```

### TEST 3: GitHub側の保存確認（Remote Readback確認）
1. GitHubの [PR #10 ページ](https://github.com/kamiyusense/ai-video-research/pull/10) を開きます。
2. Commits タブを確認し、GASから新しいコミット（`auto(gemini-loop): relay 1 research updates from Google Drive receipt`）が追加されていることを確認します。
3. Files changed タブで、`research/2023-01-17-kCc8FmEb1nY-lets-build-gpt.md` が新規作成され、`registry.json` に1件追加され、`automation/gemini-notebook/state/loop_state.json` にダイジェストが記録されていることを確認します。

### TEST 4: 重複排除テスト（非破壊性の確認）
1. Drive受信トレイにファイルが残った状態のまま、GASエディタで **`runCloudRelayLoop`** をもう一度 **「実行」** します。
2. 実行ログを確認します：
   ```json
   {
     "status": "COMPLETED",
     "relayReport": [
       {
         "file": "test_sample_receipt_v1.json",
         "status": "SKIP_DUPLICATE_ALREADY_COMMITTED_ON_GITHUB"
       }
     ]
   }
   ```
   新たなGitHubコミットが発生せず、同一内容の重複保存が防止されたことを確認します。

### TEST 5: 異常系・安全停止テスト
1. 不正なテキストファイル（例: メモ帳で `これは壊れたJSONです` とだけ書いたファイル `broken.json`）を受信トレイに置きます。
2. GASエディタで **`runCloudRelayDryRun`** または **`runCloudRelayLoop`** を実行します。
3. ログで `status: "SKIPPED_NO_RECEIPT"` または `"REJECTED_VALIDATION_BEFORE_GITHUB_WRITE"` となり、プロセス全体がクラッシュせず安全にスキップされることを確認します。

### TEST 6: PC-OFF時間主導型トリガーの有効化
1. GASエディタの左メニューにある **「トリガー」**（時計アイコン）をクリックします。
2. 右下の **「トリガーを追加」** をクリックします。
   - **実行する関数を選択**: `runCloudRelayLoop`
   - **実行するデプロイを選択**: `Head`
   - **イベントのソースを選択**: `時間主導型`
   - **時間ベースのトリガーのタイプを選択**: `時間ベースのタイマー`
   - **時間の間隔を選択（時間）**: `1時間おき`（またはお好みの間隔）
3. **「保存」** をクリックします。
4. これで、**PCの電源を落としても、クラウド上で1時間おきに自動巡回・中継が行われる状態**になります。

### TEST 7: 保存した研究成果をGemini Notebookで利用する手順
> [!NOTE]
> **Notebook直接同期の現状ステータス: 手動反映（外部API自動同期は UNKNOWN / NOT_WIRED）**  
> Google公式による外部システムからのNotebookLM自動ソース登録APIは一般提供されていないため、第1号では「GitHub正本のエクスポート文書を手動でNotebookへコピーする方式」を安全な基本運用として採用しています。

1. GitHub正本に保存された研究サマリーは、`automation/gemini-notebook/state/github_knowledge_index_export.md` に集約されます。
2. ユーザーは必要に応じてこのMarkdownの内容をコピーし、[Gemini Notebook](https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7) のメモ（ノート）に追加するか、新しいソースとして登録します。
3. Notebook上で「最近追加されたハーネスの知見について教えて」とチャットで質問し、回答を得られることを確認します。

---

## 4. 異常時の停止・復旧方法

- **GASの実行エラーが発生した場合**:
  - GASの「実行数」画面でエラーログを確認します。
  - GitHubトークンの期限切れ、ブランチ名の間違い、DriveフォルダIDの間違いが主な原因です。
- **緊急停止したい場合**:
  - GASの「トリガー」画面を開き、作成したトリガーを「削除」するだけで、クラウド上の自動実行は即座に完全停止します。
- **GitHub正本の保護**:
  - すべての処理は隔離作業ブランチ（`feature/gemini-notebook-research-loop-20261016`）に限定されており、`main` に影響を与えることは構造上不可能です。
