# 研究担当間の受け渡し（1件1ブロック）

> 下記はテンプレート。埋まらない項目は `UNKNOWN`。動画本体・字幕全文・AI回答全文・認証情報・機密情報を貼らない。

- handoff_id: <video_id>/<stage>/<generation>
- video_id: <11文字の大文字小文字区別ID / UNKNOWN>
- canonical_url: https://www.youtube.com/watch?v=<video_id>
- user_question: <今回知りたいことを短く>
- source_role: coordinator | visual | research | reviewer | archivist
- destination_role: coordinator | visual | research | reviewer | archivist
- stage: RECEIVED | SCOPED | VISUAL_REPORTED | VISUAL_UNKNOWN | RESEARCH_REPORTED | RESEARCH_UNKNOWN | REVIEWED | RECORD_CANDIDATE | RECORDED | READBACK_VERIFIED | SKIPPED_STORAGE | BLOCKED
- result: PASS | NEEDS_RESEARCH | UNKNOWN | NOT_APPLICABLE
- acquisition: video+audio | selected_video_segments | transcript_only | metadata_only | official_web | user_supplied_report | mock
- acquisition_scope: <確認できた範囲・時刻・取得できなかった範囲>
- claims_and_times: <独自要約／時刻／どの資料で確かめたか。最大5〜8件>
- verified_sources: <URL・公表日・確認日・何を裏付けるか>
- contradictions: <食い違いの内容。なければNONE / 不明はUNKNOWN>
- unknowns: <残る疑問>
- next_action: <誰が何をするか／何が届くまで待つか>
- storage_intent: YES | NO | UNDECIDED
- authorization: STATIC_RESEARCH_ONLY | EXPLICIT_APPROVAL_NEEDED
- evidence_ref: <GitHubの研究ノート/手元のユーザー提供報告など。未取得ならUNKNOWN>
- repo_ref: <branch, HEAD, PR。未確認ならUNKNOWN>
- write_status: NOT_RUN | READBACK_VERIFIED | UNKNOWN
- external_live_status: NOT_RUN | USER_MANUALLY_EXECUTED | UNKNOWN

## 引き継ぎのルール
- `source_role`担当が未確認の内容を`destination_role`へ「確認済み」として渡さない。
- 相手のレポートを全文GitHubに置かない。必要な結論と根拠を独自要約。
- 動画を元に要約したことと、実機で作業を成功させたことを別欄で記す。
- 同じ`video_id`の再調査は`registry.json`に新レコードを増やすのではなく履歴追記の候補として扱う。
- `write_status=UNKNOWN`の再送はしない。まずGitHub remote readback。
