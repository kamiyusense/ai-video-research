# AI技術研究室_知識索引 (GitHub正本 同期用インデックス)

- 対象リポジトリ: `kamiyusense/ai-video-research` (private)
- 補助知識庫 (Gemini Notebook): https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7
- 最終索引更新日: 2026-10-17
- 用途: Gemini Task の Step 1 (READ) / Step 3 (SELECT) / Step 6 (DIFF) / Step 8 (INDEX) で参照し、既知動画の重複調査を防ぎ、差分抽出と次テーマ選定の基準とする。

## 1. 既知の動画ID台帳（全ブランチ統合・重複登録禁止リスト）

| video_id | 状態 | 保存場所 ( 現在ブランチ / 並行PRブランチ ) | 研究ファイル |
|---|---|---|---|
| `3bLrrkA1nlQ` | PRELIMINARY_RESEARCH_RECORDED; ORIGINAL_VIDEO_UNKNOWN; LIVE_NOT_RUN | origin/research/cognitive-drift-series-20261010, origin/research/video08-notebooklm-youtube-extension-20261010 | `research/2026-10-10-3bLrrkA1nlQ-html-plan-preliminary.md` |
| `BStkW1HTfmk` | VIDEO_CONTENT_PENDING; OFFICIAL_ONLY_RESEARCH; OBSIDIAN_INSTALL_NOT_RUN | origin/research/video07-obsidian-github-overlay-20261010 | `research/2026-10-10-BStkW1HTfmk-obsidian-preliminary.md` |
| `Vr3JkAT9mo8` | RESEARCH_RECORDED; STATIC_SPECIALIST_IMPLEMENTED; LIVE_NOT_RUN | current_branch | `research/2026-10-10-Vr3JkAT9mo8-work-specialists.md` |
| `ZjUJ-35acaU` | REVIEWED_PARTIAL; OFFICIAL_CROSSCHECK; VIDEO_VISUAL_UNKNOWN; EXTENSION_NOT_TESTED | origin/research/video08-notebooklm-youtube-extension-20261010 | `research/2026-10-10-ZjUJ-35acaU-notebooklm-youtube-extension.md` |
| `lC5jxpYmatE` | RESEARCH_RECORDED; LIVE_NOT_RUN | current_branch | `research/2026-10-10-lC5jxpYmatE-ai-techniques.md` |
| `MVVpR2Bb0Rk` | SKIPPED (メンバー限定報告・対象外) | `origin/research/cognitive-drift-series-20261010` | 調査対象外 |

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
