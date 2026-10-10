# 手動担当制ワークフロー v1
運用状態: STATIC_TEMPLATE / NO_AUTO_HANDOFF / NO_EXTERNAL_LIVE

## 1. 受付
coordinatorは `PROJECT_CONFIG.md`、`MEMORY.md`、`TASKS.md`、`TASK_REGISTRY.json` を確認。
新規/既存task_idを確定し、既存なら重複起票を避けて差分作業を選ぶ。
依頼目的、完了条件、資料、必要な独立検証、承認と費用境界を整理する。

## 2. 専門担当へ
`templates/HANDOFF.md`に短く、同じタスクIDと基準時点を記す。
必要ならspecialist-aとspecialist-bに**独立して**調査・実行を依頼。外部AIへ渡す操作は人間が行い、実行済みと偽らない。
各専門担当は確認手段、証拠、未取得、結果、不一致を報告する。

## 3. 検品と記録
reviewerは報告と一次資料を照合し、PASS/NEEDS_RESEARCH/UNKNOWN/NOT_APPLICABLEを判定。
archivistは保存意図と権限、台帳の重複を確認。書く場合だけ指定repoの承認済非default branchに変更し、リモート読み戻し。Mergeはしない。
`TASKS.md`は人が読む索引、`TASK_REGISTRY.json`は同じIDの二重登録防止。両者の不一致はUNKNOWNとして修正案を提示し、根拠なく上書きしない。

## 4. 新チャットで再開
`prompts/RESUME.md`を使い、role・task_id・repoを明示。
毎回現在repo、default branch、HEAD、関連PR、全体・担当ルール、対象handoffと成果物を読み直す。
「確認できた最新状態」「未完了」「今できる安全な作業」を述べ、未完了から開始する。
静的文書だけで実際の外部担当連携や自動化が実装されたとは言わない。

## 5. 状態と停止
RECEIVED → SCOPED → SPECIALIST_REPORTED / SPECIALIST_UNKNOWN → REVIEWED → RECORD_CANDIDATE → RECORDED → READBACK_VERIFIED。
SKIPPED_STORAGE=保存しない、BLOCKED=承認・費用・認証等で停止。
保存に使った外部writeの結果UNKNOWNでは無条件再送しない。まずGitHubのHEAD・ファイルを読み戻す。
同時編集・同一ファイルの競合では更新を止める。
