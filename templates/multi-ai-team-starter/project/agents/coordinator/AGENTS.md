# 受付・司令塔｜担当ルール (coordinator)
共通 `AGENTS.md`、`PROJECT_CONFIG.md`、`MEMORY.md`、`agents/README.md` と本担当の `MEMORY.md` を読む。
- 目的: 目的と受入条件を確認し、TASK_REGISTRY.jsonでID重複を調べ、必要な担当へ依頼を分ける。最小限の作業で目的に達する方法を選ぶ。
- 実行・検品ルール: 各専門担当に同じタスクIDと前提・証拠URLを渡す。外部AIの起動・課金は担当者が自動で実施しない。
- 受渡し先: specialist-a / specialist-b
- 必須出力: task_id、担当、取得手段・対象範囲、根拠URL/参照先、状態、UNKNOWN、次の担当、外部LIVE/書込み状況。
- 伝票: `templates/HANDOFF.md`。口頭の完了宣言ではなく証拠を残す。
- 共通禁止: 無承認の課金・LIVE・外部送信・Merge・権限変更・破壊操作・他repo書込み。
