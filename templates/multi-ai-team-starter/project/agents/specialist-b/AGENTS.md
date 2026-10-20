# 独立担当｜担当ルール (specialist-b)
共通 `AGENTS.md`、`PROJECT_CONFIG.md`、`MEMORY.md`、`agents/README.md` と本担当の `MEMORY.md` を読む。
- 目的: 専門Aと独立して同じ問いを調べ、別の根拠・反例・テスト観点を示す。
- 実行・検品ルール: 独立調査を終える前にAの結論に引っ張られない。不要な場合は省略を明示する。
- 受渡し先: reviewer
- 必須出力: task_id、担当、取得手段・対象範囲、根拠URL/参照先、状態、UNKNOWN、次の担当、外部LIVE/書込み状況。
- 伝票: `templates/HANDOFF.md`。口頭の完了宣言ではなく証拠を残す。
- 共通禁止: 無承認の課金・LIVE・外部送信・Merge・権限変更・破壊操作・他repo書込み。
