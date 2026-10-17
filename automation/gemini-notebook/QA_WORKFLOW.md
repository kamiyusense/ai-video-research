# AI技術研究室｜質問回答・時刻付き動画箇所検索ワークフロー (`QA_WORKFLOW.md` v0.6)

本書は、蓄積した動画研究・一次資料検証から**ユーザーの自然文の質問に答え、目的に合致する動画の該当チャプター（再生位置リンク `&t=XXs`）まで正確に案内する知識システム**の設計・運用手順・質問窓口比較を定義します。

---

## 1. 役割分担：Gemini Notebook（図書館）と GitHub（構造化正本・索引）

| 項目 | Gemini Notebook（元資料の図書館） | 非公開 GitHub `kamiyusense/ai-video-research`（構造化正本） |
|---|---|---|
| **主な役割** | 元動画の字幕由来情報・長文の一次資料・研究カードを保持し、細部の文脈や具体例を深掘り参照する「図書館」 | 検証済みの技術知識・章立て目次・確認済みタイムライン（`&t=XXs`）・公式資料照合結果・関連研究・更新履歴を厳格に管理する「唯一の研究正本」 |
| **YouTube動画の扱い** | 公開・字幕ありのYouTube動画は可能な限り**動画URLをNotebookソースとして登録**し、あわせて章立て・時刻リンク・検証結果をまとめた**構造化研究カード**を登録する | **字幕全文や動画本体は保存しない**（禁止キー・正規表現で機械的にもブロック）。300文字の概要要約（`summary_ja`）に加え、最大2,500文字の構造化技術ノート（`detailed_findings_ja`）と章立て目次（`chapters`）を保存する |
| **時刻（タイムスタンプ）の保持** | ⚠️ YouTube URLをNotebookソースに追加しただけでは、Notebook内部のテキストチャンク化で秒単位の時刻情報が失われる場合がある | 各章（`chapters`）および各主張（`claims`）に開始秒・終了秒と**時刻の確認根拠（`timestamp_source`）**を構造化して保存し、根拠確認済みの場合のみ `&t=XXs` リンクを生成する |
| **既存資産の保護** | 既存の研究ソース（先行16ソース等）やNotebook内総合索引 `AI技術研究室_知識索引.md` を保護し、削除・重複登録・無断上書きを行わない | `main` への直接書込み・強制プッシュ・削除を禁止し、非defaultブランチ上で履歴とSHA-256ダイジェストを追跡する |

---

## 2. 時刻の信頼性ルール（推測リンクの絶対禁止）

動画の再生位置リンク（`https://www.youtube.com/watch?v=<video_id>&t=<start_seconds>s`）は、**時刻の根拠（`timestamp_source`）が確認できた場合のみ**生成します。

| `timestamp_source` 値 | 意味・確認方法 | `&t=XXs` 再生リンク生成 |
|---|---|---|
| `YOUTUBE_CHAPTER_METADATA` | YouTube動画概要欄・公式チャプターメタデータで開始〜終了時刻を確認 | **生成する（PASS）** |
| `TIMESTAMPED_CAPTIONS` | 時刻付き字幕（Spark / YouTube文字起こし / Gemini YouTube拡張）で発話時刻を確認 | **生成する（PASS）** |
| `VISUAL_FRAME_CHECK` | Google AI Studio または人間による映像フレーム・スライド表示時刻の確認 | **生成する（PASS）** |
| `OFFICIAL_TIME_RANGE` | 投稿者の公式解説記事・公式目次で明示された時刻区間を確認 | **生成する（PASS）** |
| `UNKNOWN` | 時刻未確認（またはNotebook内の時刻なしテキストチャンクのみ） | **生成しない（`UNKNOWN` と明記）** |

- **二重防護の実装**:
  1. **Receipt検証時 (`receipt_to_research.py` / `cloud_relay_gas.js`)**:
     - `timestamp_source == "UNKNOWN"` なのに `start_seconds` や `timestamp_seconds` に数値を入れることをスキーマ違反として拒否（推測秒数の混入を防止）。
     - 逆に `timestamp_source != "UNKNOWN"` なのに `start_seconds` / `timestamp_seconds` が `null` の場合も拒否。
  2. **Markdownレンダリング・質問検索時 (`query_research.py`)**:
     - `start_seconds` が非負整数かつ `timestamp_source != "UNKNOWN"` の場合のみ `[MM:SS〜MM:SS](https://www.youtube.com/watch?v=<ID>&t=<sec>s)` を出力。
     - 時刻未確認（`UNKNOWN`）の場合は推測リンクを作らず、`UNKNOWN (時刻未確認のため&t=リンク非生成 / [通常動画URL](https://www.youtube.com/watch?v=...) + Notebook <source_id> 参照)` と出力して元資料への参照を誘導。

---

## 3. 質問回答と動画箇所検索の6段階パイプライン（①〜⑥）

`automation/gemini-notebook/query_research.py`（およびChatGPT/Geminiの質問応答フロー）は、以下の6段階で質問を処理します。

1. **① 質問の意図を理解する (`analyze_query_intent`)**:
   - 質問文から知りたい目的を分類：
     - `CONCEPT_AND_BASICS`（「〜って何？」「仕組み・役割・違いを知りたい」）
     - `FAILURE_AND_LIMITS`（「失敗例・問題点・注意点・限界を知りたい」）
     - `IMPLEMENTATION_AND_HOWTO`（「具体的な手順・作り方・スクリプト移行方法を知りたい」）
     - `VERIFICATION_AND_OFFICIAL_SPEC`（「公式仕様・一次資料の裏付けを確認したい」）
     - `VIDEO_LOCATOR`（「どの動画のどこを見ればいいか知りたい」）
   - 技術用語の同義語・関連語を展開（例：「ハーネス」⇔ `Harness`, `Hooks`, `状態管理`, `守り・拡張` ／「スキル」⇔ `Skill`, `SKILL.md`, `遅延読み込み`）。
2. **② GitHub上の研究記録・目次・検証済み主張を検索する (`search_github_knowledge`)**:
   - 単純な文字列一致ではなく、**「トピック一致度 × 質問目的との適合度 × 一次資料の検証強度（`CONFIRMED_DOC` / `CONFIRMED_TEST` 優先） × 確認済み時刻の有無」**の複合スコアで該当動画・チャプター・主張を順位付けします。
3. **③ 必要ならGemini Notebookの詳細ソースを参照する (`recommend_notebook_lookup`)**:
   - 該当動画のNotebookソースID・動画URL・総合索引 `AI技術研究室_知識索引.md` を特定し、Notebook（図書館）側で前後の文脈や具体例を深掘りするための質問文を自動生成します。
4. **④ 既存知識で足りない場合は追加調査候補を示す (`detect_gaps_and_suggest_research`)**:
   - 既存記録の未確認事項（`UNKNOWN`）や知識の空白を検出し、次に調べるべきYouTube検索クエリ・公式ドキュメント調査テーマを提案します。
5. **⑤ 根拠付きの回答をまとめる**:
   - 動画内の主張（`VIDEO_REPORTED` / `REPORTED_BY_AUTHOR`）と公式一次資料による確認結果（`CONFIRMED_DOC` / `CONFIRMED_TEST` / `CONTRADICTED`）を明確に区別して回答を構成します。
6. **⑥ 該当する動画のタイトル・章・開始〜終了時刻・YouTube再生リンクを提示する**:
   - 確認済み時刻がある区間について、クリック1回で該当位置から再生できるリンク（`https://www.youtube.com/watch?v=<ID>&t=<sec>s`）と時刻確認根拠（`timestamp_source`）を表形式で提示します。

### コマンド実行例（ローカルCLI / Antigravity）

```powershell
# 1. GitHub内の全研究記録から構造化カタログ (video_knowledge_catalog.json) を更新生成
py -3 automation/gemini-notebook/query_research.py --build-catalog

# 2. 自然文で質問し、根拠付き回答＋動画チャプター再生リンクを取得（Markdown出力）
py -3 automation/gemini-notebook/query_research.py -q "ハーネスって何？どの動画のどこを見ればいい？"

# 3. 特定の目的（失敗例・注意点）に絞った動画箇所検索
py -3 automation/gemini-notebook/query_research.py -q "前に調べたスキル設計の動画で、失敗例を話していた箇所を教えて"

# 4. プログラム連携用の構造化JSON出力
py -3 automation/gemini-notebook/query_research.py -q "担当制AIのAGENTS.mdとMEMORY.mdの役割と実演箇所は？" --json
```

---

## 4. 質問窓口の設計比較（どこで質問するのが最も実用的か）

公式仕様に基づき、ユーザーが日常的に質問する窓口を4つの方式で比較します。

| 評価軸 | 方式A（推奨・日常の第一窓口）：<br>**ChatGPT（Project + GitHub参照）** | 方式B（最も正確・決定論的）：<br>**ローカルCLI / Antigravity (`query_research.py`)** | 方式C（元資料の深掘り専用）：<br>**Gemini Notebook（NotebookLM）単体** | 方式D（補助・新規動画のその場確認）：<br>**Gemini App（YouTube / Workspace拡張）** |
|---|---|---|---|---|
| **参照するデータ源** | 非公開GitHub `kamiyusense/ai-video-research` の `research/*.md`, `video_knowledge_catalog.json`, `github_knowledge_index_export.md` | ローカルまたはGit同期済みの `research/*.md`, `notes/*.md`, `registry.json`, `loop_state.json` | Notebook内に登録されたYouTube URLソース（字幕由来テキスト）＋研究カード＋`AI技術研究室_知識索引.md` | Google Workspace（DriveミラーDoc）＋YouTube拡張 |
| **①〜② 意図理解と構造化検索** | ◎ 自然文の意図理解に優れ、`video_knowledge_catalog.json` や `research/*.md` を読ませることで目的別の章・検証結果を正確に抽出可能 | ◎ 100%決定論的アルゴリズムで全ファイル・全チャプター・検証ステータスをミリ秒単位でスコアリング検索 | ○ 登録ソース内の横断検索・引用は得意だが、GitHub正本の検証ステータス（`CONFIRMED_DOC`等）を厳密に優先する制御はプロンプト依存 | △ 会話ごとに検索範囲が揺れやすく、GitHub正本を直接参照できない |
| **⑥ 時刻付き再生リンク (`&t=XXs`) の正確性** | ◎ GitHub上の確認済みチャプター表・`video_knowledge_catalog.json` に記録された検証済み `&t=XXs` リンクをそのまま正確に提示可能 | ◎ `timestamp_source != "UNKNOWN"` の検証済み時刻のみから100%正確に `&t=XXs` リンクを生成（推測リンク混入ゼロ） | △ **要注意**：YouTube URLをNotebookに追加しただけでは秒単位の時刻が失われることが多く、**構造化研究カード（チャプター表付き）をソースとして併用した場合のみ**時刻リンクを返せる | ○ YouTube拡張経由で字幕タイムスタンプを参照できる場合があるが、未確認時刻を推測で答えるハルシネーションに注意が必要 |
| **③ 元動画の細部・字幕ニュアンスの深掘り** | △ GitHubには字幕全文を保存しないため、記録されていない細部の発言内容は「Notebookの該当ソースを参照」と案内する | △ 同左（参照すべきNotebookソースIDと深掘り用プロンプトを自動出力する） | ◎ **最も得意**：Notebook自身が保持するYouTube字幕由来ソースから具体的な発言の文脈を引用付きで回答できる | ○ 単一動画のYouTube拡張照会には使えるが、研究室全体の蓄積との統合は弱い |
| **④ 不足知識の検出と追加調査提案** | ◎ GitHubの `open_unknowns`・`P006` 未解決課題・`RESEARCH_ROADMAP.md` と照合して次の調査を提案可能 | ◎ カバレッジ判定（`SUFFICIENT_VERIFIED` / `PARTIAL` / `INSUFFICIENT`）と未確認事項を自動抽出 | △ 外部Webの最新公式ドキュメントをその場で検索・検証する機能は限定的 | ○ Google検索併用で新しい動画・公式記事を探す入口に向く |
| **追加費用・権限** | 既存ChatGPT Plus契約内（追加費用なし） | 完全ローカル実行（API課金ゼロ・通信不要） | 既存Google AI Pro契約内（追加費用なし） | 既存Google AI Pro契約内（追加費用なし） |

### 結論：明確な切り分けと推奨運用（二段構え方式）

1. **Notebook単体でできること・限界**:
   - Notebook単体では、登録済みYouTubeソース（字幕由来情報）と研究ノートを横断して「動画の中でどんな具体例を話していたか」を引用付きで調べる**「図書館としての深掘り」**ができます。
   - しかし、Notebookは非公開GitHubを直接読めず、またYouTube URLソース単体では秒単位の正確な再生リンク（`&t=XXs`）を安定して生成できません。これを補うため、Gemini Task実行時に**「確認済みチャプター時刻・`&t=XXs` リンク・検証結果を含む構造化研究カード」**もあわせてNotebookに登録します。
2. **ChatGPT（GitHub参照）または `query_research.py` でできること（推奨の第一窓口）**:
   - 日常の質問（「ハーネスって何？どの動画のどこを見ればいい？」「スキル設計の失敗例を話していた箇所は？」）は、**ChatGPT（GitHubの `automation/gemini-notebook/state/video_knowledge_catalog.json` と `research/*.md` を参照）** または **ローカル/Antigravityの `query_research.py`** を第一窓口にします。
   - これにより、一次資料で裏付けられた回答（`CONFIRMED_DOC` と `VIDEO_REPORTED` の区別）と、時刻根拠が確認済みのYouTube再生リンク（`&t=XXs`）を推測なしで即座に取得できます。
   - さらに詳しい発言のニュアンスを知りたい場合のみ、出力された「③ Gemini Notebook参照ガイド」のプロンプトを使ってNotebook（図書館）を開くのが最も確実で手戻りがありません。
3. **追加開発や公式仕様上の境界**:
   - ChatGPTやローカルCLIからGemini Notebook内部の非公開ソースを直接API検索する公式機能は提供されていません（`NOT_SUPPORTED_BY_OFFICIAL_SPEC`）。
   - そのため、GitHub側に**「章立て目次・確認済みタイムライン・2,500文字までの詳細技術知識（`detailed_findings_ja`）・検索カタログ（`video_knowledge_catalog.json`）」**を持たせる本v0.6設計により、9割以上の質問はGitHub正本だけで即答＋再生リンク案内まで完結し、残りの細部照会だけをNotebookへ正確に誘導できます。
