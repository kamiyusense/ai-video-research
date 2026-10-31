# 字幕保存スイッチ設計（GH-22・オフライン受入完了）

## 現在地

2026-10-27：2ボタン試作から1ボタン画面へ改修済み。受け箱読取、弾く／戻す、状態保存、好みメモ、工程制御、サービスアダプターを接続。複数本の通し試験は外部境界をすべて偽物にして実施。指定の全体テストは408件と15サブテストが合格（RESULT: PASS）。設計・実装・オフライン試験・使い方の受入は完了。Windows画面と実サービスはUNKNOWN。

## 設計図

受け箱JSON → 一覧（タイトル、チャンネル、公開日、言語、テーマ、理由）→ 弾く／戻す → 保存開始 → 1本ずつ処理 → 好みメモ。

1本の処理：重複確認 → 字幕だけ取得 → 字幕原文OKF → Claude研究ノート → 既存検品 → 台帳と索引 → GitHub保存と読戻し → Notebookの不足ソース登録と読戻し → 完了。

保存開始を押すことが対象動画の保存許可。確認ボタンは追加しない。候補・弾いた印・工程はPC専用状態に保存しregistry.jsonとは分ける。状態破損時は初期化せず停止。完了済み工程から再開し、結果不明の書込みは再送せず読戻す。

Notebook認証切れはNotebook工程、YouTubeロボット確認は字幕取得工程を残り全部待ちにする。Claudeの枠切れは研究ノート待ち。自動再ログイン、別モデルへの切替はしない。

## 保存先と再利用

Drive受け箱・登録チャンネル・seedは読むだけ。場所は新しい研究室フォルダ優先、旧直下フォールバック、設定で変更可能にする。このローカル版にはlab_folder()がなかったためnotebook_auto_ingest.pyに共通関数を追加し、新画面から再利用する。

好みメモはPCの送信待ちフォルダへ保存後Driveへ渡す。Drive不通でも動画保存は続行。preferences_YYYYMMDD.json、同日2回目は_2とし上書きしない。seedのinterests等は変更せず、saved・rejectedを観測記録として出す。字幕・鍵・個人情報は含めない。

字幕とClaude作業領域はPC保管庫に置く。GitHubへの対象は研究ノート・registry.json・video_knowledge_catalog.jsonに限定。保存先は専用非defaultブランチsubtitle-switch/savesを推奨。main・他repo・force pushは禁止。競合時停止。

既存intake_url.py、検品・台帳処理、notebooklm_py_ingest.pyの不足ソース判定と読戻しを優先して接続する。PowerShell試作は参照として残す。

## AI専用字幕OKF見本

架空の短い見本。Issueの形式はロードマップR3の段落方式をこのアプリについて置き換える。既存別経路の字幕は変更しない。

```yaml
---
okf_version: "0.2"
type: "TRANSCRIPT"
video_id: "abcdefghijk"
logical_id: "youtube:abcdefghijk:transcript"
research_logical_id: "youtube:abcdefghijk:research"
resource: "https://www.youtube.com/watch?v=abcdefghijk"
canonical_url: "https://www.youtube.com/watch?v=abcdefghijk"
published_at: "UNKNOWN"
caption_kind: "automatic"
time_source: "YOUTUBE_CAPTION"
deduplication: "rolling_overlap_v1"
sha256: "<本文のSHA-256>"
cue_count: 2
line_count: 2
transcript_status: "UNVERIFIED"
---
[0] 架空の説明です。
[83] 次の項目を説明します。
```

手動字幕優先、無ければ自動字幕。自動字幕だけローリング重複を除き、それ以外は清書しない。両方無ければTRANSCRIPT_UNAVAILABLE。新規経路ではNotebook経由取得は使わず、時刻と取得元を保つ。研究ノートの根拠は動画URLの&t=83s形式。

## 完成判定

Mock合格：外部通信・モデルなしで一覧、弾く／戻す、複数本完走、字幕なし、再開、GitHub字幕排除、好みメモを検証。偽クライアントの成功を実機成功と呼ばない。

実機合格：GitHubリモート本文とHEAD一致、Notebook字幕と研究ノートの個別読戻し（異なるソースID／要素）、動画ID・URL・相互論理ID・本文一致、台帳と索引、根拠付きQAを確認。本作業では禁止されているためUNKNOWNのままとする。

## オーナー判断（推奨値で実装を進める）

1. Notebook満杯時：月別への切替を推奨。自動作成はせず該当動画のNotebook工程だけ待ちにする。
2. GitHub保存先：subtitle-switch/savesを推奨。main反映は別途レビューと許可による。
3. ソース上限：初期値300、余裕20で警告を推奨。設定可能にし、実際の契約上限はUNKNOWN。


## 実装と受入証拠

- `switch_app.py`：1ボタン画面、手動入力、選別、進捗表示と好みメモ送信。
- `switch_state.py`：JSONのみの受け箱読取、候補状態、上書きしない好みメモ。全行が正常なファイルだけ候補化する。
- `pipeline.py`：OSロック、工程ごとの保存、再開、結果不明書込みの読戻し、原因修正後2回までの再試行。
- `captions.py`：手動優先、json3の開始秒、時間が重なる自動字幕だけローリング重複を除去。離れた繰り返し発言は残す。
- `services.py`：既存intake_url／全ブランチ走査／OKF検品／カタログ構築／Notebookソース判定と本文照合／実画面DOM検査を接続。GitHub公開対象は3種類のパスに限定する。

旧auto_research_pipeline.pyには `--target-branch` を追加し固定枝以外も明示指定できるようにする。main/masterは明示指定しても拒否。QA_WORKFLOW.mdのURL単体登録方針を訂正。registryのRAG動画の旧ソースIDは既知の失効値のためUNKNOWNへ変更し、新しい完全IDは実機readbackまで推測しない。

実画面DOMの2要素とCLIからの両本文照合を両方必要とし、画面に接続できないときはDOM_READBACK_UNKNOWN。ソースIDがあるだけで成功にしない。アプリのcompleteは保存工程の終了を表す。ロードマップの自然言語QAを含む正式なSUCCESS_2_SOURCE_OKFの実機認定は本Issueでは行わない。

好みメモはseedのinterests／want_to_try／using／diversityを上書きせず、saved・rejected・liked_channelsを追加記録として出す。session_idは停止直後の送信重複を防ぐランダム識別子で、個人情報ではない。受け箱とseedは変更しない。

## 2026-10-27の検証結果と残る制約

字幕スイッチ関連43件はオフラインで合格。リポジトリ全体389件はassertion failure 0、Node実行拒否によるerror 20。全件合格の認定は保留。Python compileと差分の空白検査は合格。

.gitが読み取り専用のため、この環境ではローカルcommitを作れない。変更は作業ツリーに保持し、Symphonyの公開とDraft PR検品は未完了。Windows画面、Claude・yt-dlp・notebooklmの実CLI適合、実機保存はUNKNOWN。実機検証は本Issueで禁止されているため行わない。

## 継続ターン3の再点検

- 読戻し中の通信・認証失敗では、以前の結果不明書込みの保留印を消さない。原因を直してもその書込みは再送しない。
- Notebookの各資料は送信前に個別の印をPCへ保存する。既送信が不明なら全て読戻し待ちにする。既送信資料の一致が確認でき、もう片方に送信印が無い場合のみ、その未送信分を続ける。
- 先の動画のPush応答が不明な間に次の動画がPushされた場合も、先のコミットが現在のremote branchの祖先であり本文一致が確認できれば、再送せず当該コミットで保存を立証する。
- 字幕本文を再生成して保存済み指紋と照合し、研究ノートの時刻リンクも実際の字幕開始秒と照合する。Claudeの終了コード0でもJSONの枠切れエラーは待ちとする。
- GitHubへstageする実ノートと検品済みノートの一致を確認する。既存receipt_to_researchの禁止キー・禁止パターン検査をノート・台帳・索引に再利用する。
- APIキーやprovider切替の環境変数は値を読まず存在だけで起動を拒否し、Claude設定の自動読込も無効にする。CLIの実機仕様適合は引き続きUNKNOWN。
- 日付をまたいで台帳工程が再開しても、最初の保存予定パスをPCの意図記録から復元する。
- 注入した偽の外部境界による証拠にはis_mock=trueを付ける。55件の関連試験が合格。既存全体試験のNode環境阻害と.git読取専用は未解消。

## 継続ターン4の再点検（2026-10-27）

開始HEADは `6feddaf`。前ターンの変更はSymphonyのチェックポイントに保存され、main宛てDraft PR #24が存在することをGitHub APIで確認した。現在のrepositoryは公開（public）、default branchはmain。冒頭や古い資料の「非公開」は現状と異なるため、研究ノートは公開される前提で扱う。

Notebook認証切れ・YouTubeロボット確認の工程停止を、PC状態ファイルの `blocked_stages` にも保存する。再起動・新着動画の追加だけでは解除しない。オーナーが原因変更を選択した場合のみ再開し、再度失敗した原因選択を繰り返しても解除しない。Notebook停止中でも新着動画のGitHub工程までは進める。

関連58件のオフライン試験に合格。Windows画面と実サービスは未実行、UNKNOWNのまま。全体試験とコミットの環境制約の最新結果は検品ループ記録に残す。全件合格まではIssueの完了コメント・ラベル削除を行わない。

## 継続ターン5の配送障害確認（2026-10-27）

好みフォルダ内に想定外の形のJSONがある場合と、配送後のPCファイルがロックされ削除できない場合も、配送待ちとして扱い動画保存を続ける。復旧後は送信済み識別子を読み戻して二重配送を防ぐ。関連オフライン試験は60件合格。Node不在と.git読み取り専用の環境阻害は継続し、全体試験・署名付きcommitは未完了。実機はUNKNOWN。

## 送信待ちメモの破損時（2026-10-27）

PCの送信待ちメモに日付がない・型が違う・配送識別子がない場合も、メモを保留して動画保存を続ける。破損メモは勝手に削除・配送しない。復旧後は未配送メモだけ送信し、動画工程は再実行しない。関連オフライン試験61件合格。実機はUNKNOWN。

## 破損メモと正常メモの配送分離（2026-10-27）

PC送信待ちの破損メモはそのファイルだけ保留し、後続の正常メモを配送する。破損ファイルは削除・変更しない。配送先の読戻しが不明な場合は従来どおり配送を止め、結果不明の再送を防ぐ。関連オフライン試験62件合格。全体試験のNode環境阻害、Git書込み制限、実機UNKNOWNは継続。

## 最終オフライン受入（2026-10-27）

開始HEAD `0dd405d83e8b93beeffbaf4b8875ee33468c5442`、作業枝 `symphony/gh-22-design`。指定コマンド `bash .symphony/run_all_tests.sh` は408 passed, 15 subtests passed、RESULT: PASS。以前のNode不在による全体試験保留は今回解消した。上記の過去の環境・件数記録は経緯として残す。

main宛てDraft PR: https://github.com/kamiyusense/ai-video-research/pull/24 。実装は既存の作業を継続して確認した。Git操作によるcommit/pushは行わず、今回の文書差分の公開はSymphonyホストフックが担当する。実Notebook・Drive・YouTube・Claudeは起動していない。実機のSUCCESS_2_SOURCE_OKFはUNKNOWN。起動と設定は `automation/subtitle-switch/README.md` を参照。
