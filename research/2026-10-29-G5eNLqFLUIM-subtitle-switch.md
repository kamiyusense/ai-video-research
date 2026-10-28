---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Orca ADE レビュー（無料・100K Stars・既定で全権限）[G5eNLqFLUIM]"
description: "複数のコーディングエージェントをgit worktreeで並列実行するOSS「Orca」を紹介する動画の研究ノート。機能、開発元、急成長、既定で権限確認を省略する点への注意、課税・競合の論点を整理する。"
tags:
  - "AI技術研究室"
  - "Orca ADE"
  - "並列コーディングエージェント"
video_id: "G5eNLqFLUIM"
resource: "https://www.youtube.com/watch?v=G5eNLqFLUIM"
canonical_url: "https://www.youtube.com/watch?v=G5eNLqFLUIM"
published_at: "2026-10-24"
logical_id: "youtube:G5eNLqFLUIM:research"
transcript_logical_id: "youtube:G5eNLqFLUIM:transcript"
---

# 独自要約

OrcaはClaude CodeやCodexなど複数のコーディングエージェントを、git worktreeで分離した作業コピー上で同時に動かすMIT系OSSの「ADE」。開発元はY Combinator出身のStably。約7か月で10万Starに到達した。一方、既定ではエージェントに全権限を与え、承認なしでコマンドを実行させる。動画はManual/Autoへの切替を勧め、利用枠の消費、性能不満、競合の多さも指摘する。

# チャプター

- 導入：7か月で10万Star、複数エージェント同時実行 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=0s>
- 動画の構成予告（機能・開発元・変更すべき設定） — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=24s>
- ADEの考え方とworktree分離 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=36s>
- 機能群（内蔵ブラウザ、行単位レビュー、SSH、約35種対応、スマホ版β） — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=65s>
- 無料・OSS・自前契約持ち込み — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=87s>
- 開発元Stablyと成長の経緯 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=95s>
- 注意点：既定で全権限、権限モード切替 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=125s>
- テレメトリと過去のトークン漏えい修正 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=155s>
- 利用枠の消費と規約上の論点 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=169s>
- 否定的な声と競合・名称の先行例 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=185s>
- CEOの個人運用例と締め — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=208s>

# 重要な知見

1. 並列化の中核はgit worktree。各エージェントが別ブランチ・別作業コピーを持ち、同一ファイルの衝突を避ける。 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=46s>
2. 1つのプロンプトを複数エージェントに展開し、結果を比較して採用案をマージする運用が想定されている。 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=56s>
3. 費用は無料だが、各エージェントの契約・利用枠は利用者負担。並列数が増えるほど枠を早く消費する。 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=169s>
4. 既定で権限確認を省略する起動フラグが使われ、コマンドが無確認で実行され得る。worktreeは隔離チェックアウトであってセキュリティ上のサンドボックスではない、と公式文書が述べていると紹介される。 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=125s>
5. Manual/Auto/Yoloの切替は直近追加されたばかりで、実コードに使う前にManualかAutoにすることが推奨される。 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=147s>
6. テレメトリは新規インストールで既定オン（匿名、設定で無効化可）。過去にCopilotログイントークンが同一PCの他ユーザーに読める不具合があり、修正済みと説明される。 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=155s>
7. 成長は急だが、CPU使用率や遅延への不満が報告され、Cursor・Conductor・Herdrなど競合も存在する。 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=185s>
8. 開発は高頻度で、3月以降369の安定版が出たと述べられる。 — <https://www.youtube.com/watch?v=G5eNLqFLUIM&t=119s>

# この研究室への応用

- 同一課題を複数エージェントに投げて比較する評価手順の試験に使える（worktree分離で成果物を比較しやすい）。
- 試用する場合は隔離環境・Manualモードから始め、機密リポジトリや認証情報を置かない。
- 利用枠消費を記録し、並列数と費用・成果の関係を測る検証項目を作る。
- 競合（Cursor等）との比較表を作る際の観点として、権限既定値・分離方式・テレメトリ・モバイル対応を使う。

# 限界・未確認

- 映像は未確認で、画面上の設定項目や操作は確認していない。字幕のみに基づく。
- 公式資料（README、ドキュメント、規約、リポジトリ、Star数、リリース数）は未照合。動画内の数値・引用は動画の主張として扱う。
- 字幕は取得元で手動扱いだが、転記・聞き取り由来の誤変換の可能性は残る（人名・製品名・数値は特に要確認）。
- ライセンス詳細、価格、対応エージェント数、権限モードの正確な挙動、脆弱性修正の範囲などの外部仕様は UNKNOWN。
- 他レビューやReddit投稿の内容は動画経由の伝聞で、原典未確認。
