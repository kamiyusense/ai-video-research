# GitHub正本 知識索引・差分エクスポート (`github_knowledge_index_export.md`)

> **【重要：索引の区別と上書き禁止】**
> - このファイルは **GitHub 正本（`kamiyusense/ai-video-research`）側の既知動画台帳・未解決課題・次回テーマの差分エクスポート** です。
> - Gemini Notebook 内に既存の総合索引ソース **`AI技術研究室_知識索引.md`**（先行16ソース等の蓄積を含む総合索引）とは**別物**です。
> - Notebook 内の `AI技術研究室_知識索引.md` をこのファイルで丸ごと上書き置換しないでください。Notebook 側では既存内容を維持したまま差分追記（または別ソースとして参照）してください。
> - **GitHub への保存成功は、Gemini Notebook への同期完了を意味しません** (`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`)。

- 対象リポジトリ: `kamiyusense/ai-video-research` (private)
- 補助知識庫 (Gemini Notebook): https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7
- GitHub側エクスポート更新日: 2026-10-17
- リモートブランチ照合鮮度: `FRESH_FETCHED`
- Notebook側への逆同期状態: `NOT_SYNCED_FROM_GITHUB`

## 1. GitHub全ブランチ横断・既知の動画ID台帳（重複登録禁止リスト）

`registry.json` だけでなく、`research/*.md` および `notes/*.md` のファイル名・本文から検出された動画IDを含みます。

| video_id | 状態 | 検出元 (現在ブランチ / 並行PRブランチ) | 参照パス |
|---|---|---|---|
| `3bLrrkA1nlQ` | PRELIMINARY_RESEARCH_RECORDED; ORIGINAL_VIDEO_UNKNOWN; LIVE_NOT_RUN | origin/research/cognitive-drift-series-20261010, origin/research/video08-notebooklm-youtube-extension-20261010 (registry.json) | `research/2026-10-10-3bLrrkA1nlQ-html-plan-preliminary.md` |
| `BStkW1HTfmk` | VIDEO_CONTENT_PENDING; OFFICIAL_ONLY_RESEARCH; OBSIDIAN_INSTALL_NOT_RUN | origin/research/video07-obsidian-github-overlay-20261010 (registry.json) | `research/2026-10-10-BStkW1HTfmk-obsidian-preliminary.md` |
| `MVVpR2Bb0Rk` | REMOTE_MARKDOWN_REFERENCE | origin/research/cognitive-drift-series-20261010, origin/research/video08-notebooklm-youtube-extension-20261010 (body:notes/cognitive-drift-video-series-20261010.md) | `notes/cognitive-drift-video-series-20261010.md` |
| `Vr3JkAT9mo8` | RESEARCH_RECORDED; STATIC_SPECIALIST_IMPLEMENTED; LIVE_NOT_RUN | current_branch (registry.json) | `research/2026-10-10-Vr3JkAT9mo8-work-specialists.md` |
| `ZjUJ-35acaU` | REVIEWED_PARTIAL; OFFICIAL_CROSSCHECK; VIDEO_VISUAL_UNKNOWN; EXTENSION_NOT_TESTED | origin/research/video08-notebooklm-youtube-extension-20261010 (registry.json) | `research/2026-10-10-ZjUJ-35acaU-notebooklm-youtube-extension.md` |
| `lC5jxpYmatE` | RESEARCH_RECORDED; LIVE_NOT_RUN | current_branch (registry.json) | `research/2026-10-10-lC5jxpYmatE-ai-techniques.md` |

## 2. 優先研究テーマ・次回調査キュー (`next_topics`)

1. R001/R002: 自律研究Loopの完了条件・停止条件と、重複イベントや結果不明書込みの安全な復旧パターン
2. R004/R005: ハーネス・MCP・プラグイン・公式コネクタの権限境界とモデル非依存の状態管理
3. P006連携: 新しいAI機能・ツール発表時に「過去の未解決課題」と自動照合して再挑戦を提案する仕組み

## 3. 未確認・要検証事項 (`unknowns`)

- Gemini Taskの定期スケジュール実行時におけるNotebookソース追加・索引更新の無人完走可否
- YouTubeソース（文字起こしのみ）では確認できない画面実演・UI操作の軽量な検証手段

## 4. 未解決課題ストック（P006 再評価対象）

新技術・新機能を発見した際は、以下の未解決課題を解決できる一次資料の根拠があるか照合すること：

- **P006-U01**: Google AI Studioの長尺YouTube動画入力でのブラウザUIフリーズ回避・映像フレーム直接検証の省力化 (状態: `OPEN`, 参照: `proposals/006-unresolved-task-backlog-revisit.md`)
- **P006-U02**: Gemini Notebookと非公開GitHub間の手動コピーを最小化する安全な公式連携・差分同期 (状態: `IN_PROGRESS`, 参照: `automation/gemini-notebook/README.md`)
- **P006-U03**: 反復的な画面操作（Computer Use）から公式API・決定的スクリプトへの安全な移行判断 (状態: `OPEN`, 参照: `research/2026-10-10-lC5jxpYmatE-ai-techniques.md`)
