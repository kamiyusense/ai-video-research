# 担当受渡し伝票（1仕事1件）
以下は入力用書式。未確認はUNKNOWN。受渡しを作っただけでAIを自動起動したとは扱わない。

- handoff_id: <task_id>/<stage>/<generation>
- task_id: <TASK_REGISTRY.jsonで一意>
- project_repo: <PROJECT_CONFIG.md の repository>
- from_role: coordinator | specialist-a | specialist-b | reviewer | archivist
- to_role: coordinator | specialist-a | specialist-b | reviewer | archivist
- goal: <短い目的>
- acceptance: <確認可能な完了条件>
- status: RECEIVED | SCOPED | SPECIALIST_REPORTED | SPECIALIST_UNKNOWN | REVIEWED | RECORD_CANDIDATE | RECORDED | READBACK_VERIFIED | SKIPPED_STORAGE | BLOCKED
- result: PASS | NEEDS_RESEARCH | UNKNOWN | NOT_APPLICABLE
- acquisition: <実際に確認した情報と取得方法>
- scope: <確認範囲、未取得範囲、作業の範囲>
- evidence: <根拠URL / file path / 日付 / 実験条件>
- confirmed_facts: <確かめた内容の短い要約>
- disagreements: NONE | UNKNOWN | <相違点>
- unknowns: <未確定>
- next_action: <誰が何をするか>
- data_storage: YES | NO | UNDECIDED
- authorization: STATIC_ONLY | EXPLICIT_APPROVAL_NEEDED
- repo_ref: <branch/HEAD/PRまたはUNKNOWN>
- write_status: NOT_RUN | READBACK_VERIFIED | UNKNOWN
- external_live_status: NOT_RUN | USER_MANUALLY_EXECUTED | UNKNOWN

## 禁止
担当の報告全文を漫然と共有正本に保存しない。秘密・鍵・個人情報を入れない。
同じtask_idの新規登録を重複させない。根拠不明の成功や具体時刻を創作しない。
