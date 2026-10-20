# 初期運用ガイド

## 新しい担当制（人間の受渡し）
新しい動画URLを受け取ったら `docs/SPECIALIST_WORKFLOW.md` と `MEMORY.md` を参照する。担当の実装は `agents/README.md`、外部AI用の依頼文は `prompts/specialist-visual.md`・`prompts/specialist-research.md` に置く。新しいチャットは `prompts/specialist-resume.md` で最新状態を読み直す。

**現時点で担当間の自動送受信、GitHubへの自動保存、Workの自動起動は存在しない。** ユーザーの都度の操作に従い、実行・検品・記録の成否を別々に確認する。複数ブランチにある同一ファイルはMerge前に競合確認。

## 研究を選ぶ
AI関連全般を対象に、RESEARCH_ROADMAP.mdで優先順位と未調査事項を管理する。
動画の研究、公式資料だけの研究、論文や公開実装の研究を区別する。
動画を使わない研究はresearch/docs/<固有名>.md等に置き、動画URL・時刻はNOT_APPLICABLEとする。
資料URLと対象版で既存記録を確認する。動画の台帳に架空の動画IDを追加しない。
役立つ成果は技術ノート、比較、改善提案へ育て、自動化との関係と次の安全作業を残す。
各社の新情報は公式発表と公開日を確認し、関連テーマへ取り込む。

## 動画の研究を始める
動画URLを受け取ったら、最初に動画IDと既存記録を確認する。
URLだけで内容を見られるとは限らない。タイトル・概要しか見られなければその範囲を明記し、
本文や出典時刻の主張をUNKNOWNにする。動画・字幕全文を取得・保存しない。
内容を確認できた部分を自分の言葉でまとめ、対象版を合わせた公式資料と照合する。
記録には確認日を残す。仕様や料金に関係する主張は利用する時点で再確認する。

## 重複対策（運用ルール。自動検知装置は未実装）
通常watch URLのv、youtu.beのパス、shorts/<ID>、live/<ID>は同一の動画IDで照合する。
IDは大文字小文字を保持する。時刻・追跡用パラメータは動画IDに含めない。
IDを確定できないリンクはUNKNOWN。外部へ開く前に行き先を確認する。
registry.json の video_id と record_id=youtube:<ID> はそれぞれ一意にする。
既存IDならresearch/の既存記録へ追記し、新しい研究記録を作らない。
同じ主張と公式資料の版の組合せは統合する。新版の再確認は日付付き履歴として追加する。
同時更新のhead競合は再読込して整理する。無条件上書きしない。

## GitHub初期化（作成機能がない場合）
ユーザーがGitHub公式画面でowner=kamiyusense、name=ai-video-research、
visibility=privateを確認し、READMEを付けて作成する。Copilotへの作業依頼は入力しない。
READMEはbranchの起点を作るためのもの。既存資料を移植しない。
AIはその後、対象repoの実在・private・default branch・headを新しく読み戻す。
privateが確認できなければ書き込みを停止する。接続に見えなければ権限を勝手に変更しない。
現在headを起点にsetup/research-lab等の非default branchへ初期資料を置き、
レビュー用PRを作成してreadbackする。main等へ直接書かず、Mergeしない。
表示名や過去のSHAを正本にしない。書き込みが不明なら同じ操作を再送しない。

## ChatGPT初期化
サイドバーから「新しいプロジェクト」で「📺 AI技術研究室」を作成する。
共有・招待は追加しない。アカウント全体の設定やモデル設定は変更しない。
プロジェクトの「…」→「プロジェクト設定」の指示欄へ
CHATGPT_PROJECT_INSTRUCTIONS.md の内容を入れ、PROJECT_SOURCE.md を資料に追加する。
GitHubリンクを追加しても自動同期・自動保存の完了とは解釈しない。

## 記録の完了条件
対象とprivateの確認、branch/head、独自要約と出典、主張の確認状態、
変更差分とremote readbackを残す。未確認はUNKNOWN。
提案を保存したことと、実装・LIVE・Mergeが承認されたことを分ける。

## 復旧
外部書き込みの結果が不明ならまずrepo、branch head、ファイル、PRをreadbackする。
保存済みならNO-OP。分からなければUNKNOWNを維持し、自動再送しない。
台帳と研究ファイルが不一致なら、証拠を確認してから整合を修正する。
削除やリセットで整合させない。独立した調査・文書作業を先に進める。

## 承認境界
課金、LIVE、Merge/auto-merge、外部モデル/Jules/provider起動、権限・APIキー操作、
default branch直接write、force push、削除は初期運用に含めない。
禁止方針を記しただけでGitHub側のbranch保護等が有効になるわけではない。
