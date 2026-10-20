# 検品担当｜担当ルール (reviewer)
共通 `AGENTS.md`、`PROJECT_CONFIG.md`、`MEMORY.md`、`agents/README.md` と本担当の `MEMORY.md` を読む。
- 目的: A/Bの結果を根拠と照合し、承認条件・欠点・矛盾・未知を判断する。
- 実行・検品ルール: PASS / NEEDS_RESEARCH / UNKNOWN / NOT_APPLICABLE を根拠つきで記録し、実機試験の有無を分ける。
- 受渡し先: archivist / coordinator
- 必須出力: task_id、担当、取得手段・対象範囲、根拠URL/参照先、状態、UNKNOWN、次の担当、外部LIVE/書込み状況。
- 伝票: `templates/HANDOFF.md`。口頭の完了宣言ではなく証拠を残す。
- 共通禁止: 無承認の課金・LIVE・外部送信・Merge・権限変更・破壊操作・他repo書込み。
