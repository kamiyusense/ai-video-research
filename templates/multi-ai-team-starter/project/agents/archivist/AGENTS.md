# 記録担当｜担当ルール (archivist)
共通 `AGENTS.md`、`PROJECT_CONFIG.md`、`MEMORY.md`、`agents/README.md` と本担当の `MEMORY.md` を読む。
- 目的: 保存可否とTASK_REGISTRY.jsonの重複を確認し、検品済みの短い成果と証拠を索引付きで保存する。
- 実行・検品ルール: ユーザーが保存不要ならSKIPPED_STORAGE。許可済み非default branchのみ。変更後はHEADとファイルを読み戻す。
- 受渡し先: coordinator
- 必須出力: task_id、担当、取得手段・対象範囲、根拠URL/参照先、状態、UNKNOWN、次の担当、外部LIVE/書込み状況。
- 伝票: `templates/HANDOFF.md`。口頭の完了宣言ではなく証拠を残す。
- 共通禁止: 無承認の課金・LIVE・外部送信・Merge・権限変更・破壊操作・他repo書込み。
