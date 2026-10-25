# 字幕保存スイッチ（Windows用の操作画面）

相棒のPCの自動研究（`C:\Users\yuuki\Documents\Codex\tools\`）に、ボタンで動かす画面を足したもの。
処理の中身は今までの `research_from_url.ps1` をほぼそのまま使い、研究ノートの書き手だけを替えた。

| ボタン | すること |
|---|---|
| ① Claudeで最後まで | 字幕取得 → 字幕原文OKF → Claudeが研究ノートOKF → 検品 → 台帳・目次 → GitHub保存（研究ノートと台帳だけ） |
| ② 字幕OKFまでで止める | 字幕取得 → 字幕原文OKF まで。研究ノートは手動で他のAIに頼む |
| 手動用の指示文をコピー | ChatGPT / Antigravity に貼る指示文をクリップボードへ。画面には出さないので書き換えられない |

- 手動で書いた研究ノートは、次にどちらかのボタンを押したとき（URL欄が空でもよい）に、検品・台帳・目次・GitHub保存まで自動で仕上げる。
- ②で止めた動画を後からClaudeに書かせたいときは、同じURLを①に貼る。字幕は取り直さない。
- 1回10本まで、1本ごとに20秒待つ。Notebookのログイン切れ・登録失敗が出たら残りを止める（`research_batch.ps1` と同じ）。

## 変更点（PCの元のスクリプトから）

- `agy -p`（Antigravity CLIを外のプログラムから呼ぶ）をやめた。Googleは個人プランでCLIを包んで自動で動かすことを認めていないため。
- 研究ノートの書き手は `-Writer claude`（既定）か `-Writer manual`。Claudeは公式CLIを1回だけ実行し、使える道具はファイルの読み書きだけ（`--tools Read Write Glob Grep`、`--permission-mode acceptEdits`、保管庫の中で起動）。
- `-Writer manual` は字幕原文OKFを保存して `exit 9`（研究ノート待ち）で止まる。
- 字幕原文OKFが保存済みなら字幕は取り直さず、荷札と指紋を読み戻して続きから進む（指紋が合わなければ `exit 6` で止める）。
- 研究ノートのテンプレートは `research_note_prompt_template.md`（元の `agy_research_prompt_template.md` の `created_by` を差し込み式にしたもの）。

## まだのこと

- 字幕の時刻: 取り込み経路（字幕取り込み専用Notebook）に時刻が無いため、今も `time_source: "NONE"`。約1分ごとの時刻目印（確定仕様R3）は未対応。
- 研究室Notebookへの2ソース登録はこの画面ではしない（元のスクリプトと同じ）。

## PCへの置き方

`subtitle_switch.pyw`・`research_from_url.ps1`・`research_note_prompt_template.md` を `Documents\Codex\tools\` に置く（元の `research_from_url.ps1` は `.bak-20261025` として残す）。起動は `pythonw subtitle_switch.pyw`（デスクトップのショートカットから）。
