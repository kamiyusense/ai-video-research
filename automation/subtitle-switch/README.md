# 字幕保存スイッチ（Windows）

受け箱の動画から不要なものを弾き、「保存開始」1回で残りを順に保存する画面です。手動URLも使えます。
設計は [日本語設計文書](../../docs/SUBTITLE_SWITCH_DESIGN.md) を参照してください。

**実装はオフラインの偽サービスで検証しています。本作業では本番実行をしていません。Windows画面・Claude・YouTube・GitHub保存・Notebook／Drive同期の実機結果はUNKNOWNです。**

## 最初の準備

1. WindowsにPython（tkinter付き）、Git、yt-dlp、ログイン済みClaude CLI、既存のnotebooklm-py CLIが必要です。APIキーは使いません。インストールや課金、ログイン操作はこのアプリでは行いません。
2. GitHub研究室のPC作業フォルダで、保存専用の非defaultブランチ `subtitle-switch/saves` を用意してください。普段の開発用フォルダと分け、未保存の変更が無い作業フォルダを推奨します。アプリはブランチの切替や作成を勝手に行いません。mainにいる場合は停止します。
3. `config.example.json` を `config.local.json` にコピーし、`repository` を上の作業フォルダ、`vault` をPCの保管庫に変更してください。OWNERは自分のWindowsユーザー名に置き換えます。保管庫はGitHub作業フォルダの外に置いてください。
4. Driveデスクトップ同期を使い、`drive_root` をマイドライブの場所にします。受け箱・好み・登録チャンネルは `AI動画研究室/` の中を優先し、旧直下にしか無ければそちらを使います。個別の場所は設定の `inbox`・`preferences`・`channels` で指定できます。
5. `notebook_id` は保存先NotebookのID、`source_limit` は実際のソース上限に合わせます（初期値300、契約上限はUNKNOWN）。NotebookをChromeのCDP接続で開いておいてください。アプリはChromeの起動やGoogleの再ログインを行いません。`cdp_port` の初期値は9222です。

本Issueでは実サービスへの実行は禁止です。上記はオーナーが後日、実機実行を許可した際の手順です。

## 起動

このフォルダをエクスプローラーで開き、ターミナルから次を実行します。

```powershell
pythonw subtitle_switch.pyw config.local.json
```

起動時のエラーを確認するときは `pythonw` を `python` に替えます。設定ファイル・保管庫・状態ファイルはGitHubへ追加しないでください。

## 毎回の操作

1. 「一覧を更新」で受け箱を読みます。`.gdoc`は無視し、壊れたJSONはそのファイルだけ「要確認」にします。
2. 不要な動画を選んで「弾く」。理由は任意です。印は再起動しても残ります。「弾いた動画も表示」→ 選択 →「戻す」で解除できます。
3. 必要なら手動URLを1行に1本貼ります。短縮URL・時刻付きURLも受け付けます。
4. 「保存開始」を押します。**押すことが、残った対象動画へのGitHub・Notebook保存の許可です。** 追加の確認画面はありません。
5. 工程・待ち理由・Notebook使用数を確認します。1本の失敗でも別の動画の処理は進みます。処理中は画面を閉じず、終了を待ってください。

## 待ちになったら

- `NOTEBOOK_LOGIN_EXPIRED`：オーナーが手動でNotebookへログインし直します。字幕・研究ノートの作り直しは不要です。
- `YOUTUBE_ROBOT_CHECK`：YouTube側の確認をオーナーが解決します。自動再ログインやロボット確認の回避は行いません。
- `CLAUDE_QUOTA`：Claudeの枠が戻るまで研究ノート待ちです。別モデルへ切り替えません。
- `NOTEBOOK_CAPACITY`：Notebook工程だけ待ちです。GitHub保存までは済んでいます。保存先Notebookや上限設定を確認してください。
- `WRITE_RESULT_UNKNOWN`：結果不明の書き込みです。再起動後も再送せず読み戻します。確認できなければ待ちを維持します。状態ファイルを削除してやり直さないでください。
- `SAVE_BRANCH_REQUIRED`：GitHub作業フォルダが設定した専用ブランチか確認してください。

原因を直した場合だけ、画面の「直した原因」を選んで「保存開始」を押します。原因を変えた再試行は2回まで。同じ原因を直さずに押しても再実行しません。結果不明の書込みはこの操作でも再送しません。

Notebookログイン切れとYouTubeロボット確認の待ちは、アプリを再起動しても残ります。新しく受け箱に届いた動画も該当工程で待ちます。原因を直してから「直した原因」を選ぶと再開できます。Notebook待ちの間も、新しい動画の字幕・研究ノート・GitHub保存までは進みます。

## 好みメモとPC上の資料

好みメモは `preferences_YYYYMMDD.json`、同日2回目は `_2`、以後連番です。seedは変更しません。字幕本文・キーは含めません。Driveへ書けない場合は保管庫内の `subtitle-switch-state/preference_outbox/` に残り、次回まとめて送ります。送信待ち件数を画面に表示します。

字幕と研究ノートの作業資料は保管庫内 `jobs/<動画ID>/`、進行状態は `subtitle-switch-state/inventory.json` に保存します。GitHubへは検品した短い研究ノートと台帳・索引だけを送ります。Notebookには字幕原文OKFと研究ノートOKFの独立2ソースを登録し、URL単体ソースは登録しません。

`research_from_url.ps1` と旧画面の互換用関数は試作の参照として残しています。新しい画面はそのPowerShell経路を起動しません。

## オフライン試験

リポジトリのルートで実行します。モデル・ネット接続・Windows画面は使用しません。

```powershell
python -m unittest discover -s tests -p "test_subtitle_switch*.py"
```

「完了・登録済みも表示」で処理結果を見返せます。通常の一覧には未処理・待ち・要確認だけを出します。

`CLAUDE_API_CONFIGURATION_BLOCKED` は、ClaudeをAPIキーや他providerへ接続する環境変数が設定されている場合です。アプリは値を読み取らずモデル起動前に停止します。通常のClaude CLIログインを使う環境をオーナーが確認してください。

保存済み字幕の指紋不一致や、字幕に存在しない開始秒へのリンクは検品で停止します。保管庫の字幕を手で書き換えないでください。GitHubへ送るノートの実ファイルも、検品済みノートとの一致を再確認します。
