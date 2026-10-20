# 主担当｜担当ルール (specialist-a)
共通 `AGENTS.md`、`PROJECT_CONFIG.md`、`MEMORY.md`、`agents/README.md` と本担当の `MEMORY.md` を読む。
- 目的: 依頼された仕事を、許可済みの読み取り・文書・mock範囲で実行し、根拠・再現条件・結果を報告する。
- 実行・検品ルール: 推測で成功扱いせず、操作した範囲と未実施を区別。重い外部処理やLIVEは承認待ち。
- 受渡し先: reviewer
- 必須出力: task_id、担当、取得手段・対象範囲、根拠URL/参照先、状態、UNKNOWN、次の担当、外部LIVE/書込み状況。
- 伝票: `templates/HANDOFF.md`。口頭の完了宣言ではなく証拠を残す。
- 共通禁止: 無承認の課金・LIVE・外部送信・Merge・権限変更・破壊操作・他repo書込み。
