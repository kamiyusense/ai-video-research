# AI技術研究室｜独立コードレビュー＆データ品質監査レポート

**実施日時**: 2026-10-17  
**対象ブランチ**: `feature/gemini-notebook-research-loop-20261016` (PR #10)  
**検査対象**: 全28動画（研究ノート28本、カタログ31件、チャプター241区間）  
**検証スクリプト**: `automation/gemini-notebook/verify_timestamps.py`, `query_research.py`, `receipt_to_research.py`  

---

## 1-A. 研究データの正確性

### 1. 28動画のメタデータ整合性
- **動画IDとURLの一致**: 全28動画（`2-8cXaRHlqI` 〜 `y2xCGyURl7Q`）について、11文字のYouTube動画IDと正規化URL（`https://www.youtube.com/watch?v=...`）が100%一致していることを確認。
- **タイトル・投稿者・公開日・動画長の整合性**:
  - YouTube一次実測長とGemini自己申告長に2秒以上の差異が存在した11本については、動画全編のチャプターを無条件に信憑せず **全章 `UNKNOWN`** に厳格降格済み。
  - タイトルと概要欄の説明に矛盾が確認された2本（`sodTFSuV4zY`, `ZY7YuYHLlIQ`）についても、チャプター時刻を **全章 `UNKNOWN`** に設定。
  - 公開日・投稿者の差異は研究ノートのヘッダーおよび `timestamp_evidence.json` 内に一次取得値とGemini記載値の両方を併記して記録。

### 2. Geminiの自己申告と一次資料・事実の区別
- Geminiが「公式仕様と一致」と自己申告した記述のうち、一次資料URLが提示されていないものはすべて `REPORTED_BY_AUTHOR`（投稿者の主張・AIの要約報告扱い）とし、`CONFIRMED_DOC` としての確定を排除。
- 実機での動作確認（`CONFIRMED_TEST`）が未実施の主張について、勝手に動作済みとマークしない。

---

## 1-B. タイムスタンプ証拠判定の監査

全241チャプターの証拠分類内訳：
- **検証済み (Verified): 計 139 章 (57.7%)**
  1. `YOUTUBE_CHAPTER_METADATA`: 48章（YouTube公式概要欄のチャプター定義と秒数が完全一致）
  2. `TIMESTAMPED_CAPTIONS`: 82章（公式字幕・自動生成字幕内のタイムスタンプ語彙と完全一致）
  3. `VISUAL_FRAME_CHECK`: 9章（`lC5jxpYmatE` 4章、`Vr3JkAT9mo8` 5章。専門担当が映像フレームを実見して照合した区間）
  4. `OFFICIAL_TIME_RANGE`: 0章（推測ハックは全廃）
- **未確認 (UNKNOWN): 計 102 章 (42.3%)**
  - 13動画が全章UNKNOWN（動画長不一致11本、概要欄矛盾2本）。
  - 8動画が一部UNKNOWN（概要欄・字幕で確認できなかった章）。

### 重点検証項目
1. **概要欄開始時刻の一致と内容一致**:
   - 単に `00:00` が存在するだけでなく、章タイトルと字幕語彙の一致を確認。
2. **AI映像分析報告とAGY直接映像確認の分離**:
   - `VISUAL_FRAME_CHECK` は手動専門担当（visual担当）が映像を精査して付与された証拠のみに限定。GeminiなどのAIによる映像要約申告をAGY自身の直接映像確認と混同しないよう `timestamp_basis` に由来を明記。
3. **時刻未確認箇所における推測リンクの禁止**:
   - `timestamp_source == "UNKNOWN"` の区間には YouTube 再生位置リンク（`&t=XXs`）を絶対に生成しない。通常動画URLおよびNotebookソースIDへの案内のみを出力。

---

## 1-C. 公式資料の検証 (`CONFIRMED_DOC`)

- **URL存在確認と対応付け**:
  - `CONFIRMED_DOC` が付与されている主張は、Anthropic公式ドキュメント（`https://docs.anthropic.com/...`）やGitHub公式リファレンス等の一次URLが1対1で対応付けられている `lC5jxpYmatE` の 3 claims のみ。
  - 一次URLが添付されていない主張はすべて `REPORTED_BY_AUTHOR` に分類。
  - `receipt_to_research.py` のバリデーションにおいて、`status == "CONFIRMED_DOC"` で `official_url` が None の場合は `ValueError` で拒否する防御を実装。

---

## 1-D. 既存研究（lC5jxpYmatE, Vr3JkAT9mo8, P006）との接続

- **lC5jxpYmatE**:
  - 本研究室の基盤となる重要動画（Skill, ハーネス設計, DevContainer分離, トークン節約）。
  - 4章の `TIMESTAMPED_CAPTIONS` と 4章の `VISUAL_FRAME_CHECK` により全8章が確認済み。
  - 新規動画の多くが `COMPLEMENTS` または `EXTENDS` で `lC5jxpYmatE` を参照するようカタログ化。
- **Vr3JkAT9mo8**:
  - ChatGPT WorkのUI/実務連携動画。5章の `VISUAL_FRAME_CHECK` と 2章の `TIMESTAMPED_CAPTIONS` で全7章が確認済み。
- **P006 (未解決課題バックログ)**:
  - `proposals/006-unresolved-task-backlog-revisit.md` の課題群（非同期実行の監視、自動復旧、長期記憶の重複解消）に対し、新規動画（Eval改善スキル `X9Zk68AII4A` や Addness連携 `cneFa24EFEk`）が関連付けられていることを確認。
