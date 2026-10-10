# P008｜ObsidianをGitHub担当制の「任意の閲覧画面」として試す

- 状態: PROPOSED / DOC_DESIGN_ONLY / INSTALL_NOT_RUN / LIVE_NOT_RUN / VIDEO_CONTENT_PENDING
- 記録日: 2026-10-10
- 動画候補: https://www.youtube.com/watch?v=BStkW1HTfmk （内容・該当時刻はUNKNOWN）
- 調査: [動画07暫定ノート](../research/2026-10-10-BStkW1HTfmk-obsidian-preliminary.md)
- 開発対象: private `kamiyusense/ai-video-research` の **人間向けナビゲーション**
- 絶対に維持する正本: GitHub。ObsidianやWindowsのフォルダを独立した正本にしない。

## 結論
**小さな試験を推奨**。ObsidianはGitHub内の既存Markdown資料を検索・表示・関連表示するUIであって、AIエージェントの頭脳・共有記憶・自動同期・実行ハーネスを置き換えない。既存5担当の役割と保存先を変更する必要はない。最初はObsidianアプリの無料部分だけで、**閲覧中心**に試す。

| 選択肢 | 費用 | 利点 | 限界 | 判定 |
|---|---|---|---|---|
| GitHub Webだけ | 追加0 | privateで履歴・PR・レビューを保持 | ファイル横断の探索や個人向けノートビューが限定 | 現状維持でもOK |
| GitHub + Obsidian（任意） | 本体追加0 | 既存MDを日本語で読む、検索、参照関係を見る | Windowsにローカルコピーが必要。自動同期は別。プラグインのリスク | **小規模試験候補** |
| Obsidianへ正本移行 | 未確認 | ローカル編集中心 | AI側GitHub記録との二重管理と競合 | **不採用** |
| Obsidian Syncを追加購入 | 有料 | 複数端末でVault同期 | 今回はGitHubで代替できる部分が多い | 現時点で不要 |
| コミュニティGit/AIプラグイン導入 | プラグイン次第 | 自動化余地 | ファイル・ネットワーク権限、API課金、事故 | 今は見送り |

## 研究室で採用するときの条件
1. **既存正本を維持**：`AGENTS.md`、root/role別 `MEMORY.md`、`registry.json`、研究ノートの保存先はこれまでどおりGitHub。
2. **人間の閲覧を改善**：ユーザーがWindowsにprivateリポジトリをクローン/コピーした時のみ、Obsidianでその同じフォルダをVaultとして開く。新しい研究ノートをObsidian専用フォルダへ複製しない。
3. **初回は閲覧中心**：Obsidianによる編集・自動リネーム・テンプレート・サードパーティプラグインはOFF/不使用。Obsidianに設定ファイル用の `.obsidian` ディレクトリが作られるため、それを無断でGitHubに追加しない。別端末同期も無効。
4. **Gitの変更管理は別**：Obsidianで表示/編集できることと、GitHubへのコミット・プッシュやPRは別の操作。作業用branch/最新HEAD確認→差分確認→レビュー→GitHub保存で進める。Obsidian自体にはremote push責務を持たせない。
5. **研究資料の発見性**：既存のMarkdown相対リンク・索引をまず利用。必要になってからObsidian内部リンクを試すが、他AIやGitHub Webでも読める標準Markdownリンクを優先。
6. **機密境界**：private repo以外の情報・ユーザー個人情報・鍵を追加保存しない。`Publish`（Web公開）を絶対に試験に含めない。
7. **利用枠**：有料Sync/Publish、新規APIキー、AI接続プラグインを前提にしない。

## 初回の最小受入テスト（まだ NOT_RUN）
A. ユーザーがローカルコピーを準備（private GitHubと現在の未Mergeブランチを混同しない）。無料Obsidianのインストール許可はユーザーが選択。
B. Obsidianの「Open folder as vault」でそのフォルダを開く（https://obsidian.md/help/vault）。
C. 以下の文書が正しく見えるか確認:
   - `README.md` → `docs/SPECIALIST_WORKFLOW.md`
   - `MEMORY.md` → `agents/README.md` → `agents/*/MEMORY.md`
   - `research/2026-10-10-Vr3JkAT9mo8-work-specialists.md`
D. 標準Searchで「映像担当」「課金」を検索し、関係する文書を素早く見つけられるか確認。
E. Obsidian終了後、Git作業ツリーが意図せず変更されていないか確認（`.obsidian/`の新規生成・未追跡ファイルを含む）。ソフトを入れた時の自動変更を無条件GitHubへpushしない。
F. GitHub側の新しい別ブランチの変更が、Obsidianで勝手に同期されないことを理解する。必要なら利用するブランチを明示して取得し直す。

受入基準: 閲覧や検索に価値があり、既存記録を壊さない・二重管理なし・追加課金なし・他repo変更なし。価値が小さければ**不採用**でもOK。

## 次の動画再評価
YouTube本編の字幕・映像未取得。投稿者の「Obsidianで何がどこまで自動化され、どこで限界が出たか」は動画取得後に時刻付きで検証し、P008に差分を追記する。今回は投稿者が実際に上記のGitHub構成を提案したとは扱わない。

## 今回の境界
GitHubの文書保存だけ実行可能。ObsidianをWindowsにインストールしない。Git Clone/Branchの変更、Work/Spark/AI Studio自動起動、外部送信、GitHub main書込、Merge、課金・権限変更、Publishを実行しない。
