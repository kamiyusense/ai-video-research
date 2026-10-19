---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "【研究カード】 【AI中級】RAGのその先。巨大な資料をAIで精度高く取り扱いたい。"
description: "RAG（検索拡張生成）が抱える構造的限界（数・時系列・全体サマリーに答えられない欠陥）を整理し、質問を「①探し物」「②数える」「③並べる・いつの時点か」「④全体」の4つに仕分け、RAGは探し物のみに限定して専用の道具（セマンティックレイヤー付きSQL、バイテンポラル履歴管理、階層型要約）へ振り分ける設計を提示。さらに500ページ未満のプロンプト丸ごと渡しや、Claude CodeのようにベクトルDBを捨ててオンデマンド探索（grep/glob）に倒す『仕組みを作らない選択』を解説。"
resource: "https://www.youtube.com/watch?v=pRfC1DILDEM"
tags:
  - "AI技術研究室"
  - "動画研究"
logical_id: "youtube:pRfC1DILDEM:research"
record_id: "youtube:pRfC1DILDEM"
video_id: "pRfC1DILDEM"
canonical_url: "https://www.youtube.com/watch?v=pRfC1DILDEM"
original_url: "https://www.youtube.com/watch?v=pRfC1DILDEM"
publication_date: "2026-09-02"
checked_at: "2026-10-18"
source_scope: "Gemini報告: YouTube字幕 00:00〜14:23 を取得して分析。映像・画面未確認。ChatGPT独立確認なし。Notebook登録・読戻しはGemini自己申告。"
transcript_logical_id: "youtube:pRfC1DILDEM:transcript"
transcript_status: "UNVERIFIED"
primary_source_notebook_id: "25c0f62e-99aa-48bc-9486-357a350c76f5"
document_type: "AI技術研究室 構造化研究カード（二次分析資料）"
notebook_readback: "PASS"
github_verification: "NOT_RUN"
github_to_notebook_sync: "NOT_SYNCED_FROM_GITHUB"
changes:
  - "NEW"
related_records:
  - target_id: "youtube:u3ka_AAb8qE:research"
    relation: "COMPLEMENTS"
    note: "OKF（書類の置き方改革＝地図作り）とRAG（質問振り分け表＝歩行設計）が相互補完関係にある"
    status: "CANDIDATE"
    evidence: "13:16過去回OKFとの接続言及およびu3ka_AAb8qEの08:16荷札・09:35リンク構造"
---

# 【研究カード】 【AI中級】RAGのその先。巨大な資料をAIで精度高く取り扱いたい。

> [!IMPORTANT]
> **文書区分**: 本ドキュメントは一次資料（YouTube字幕）を基に構造化分析した「AI技術研究室 研究カード」です。Notebook内の一次資料YouTube動画そのものではありません。回答引用時は「一次資料（動画）」と「本研究カード（構造化分析）」を明確に区別してください。

## 独自要約
RAG（検索拡張生成）が抱える構造的限界（数・時系列・全体サマリーに答えられない欠陥）を整理し、質問を「①探し物」「②数える」「③並べる・いつの時点か」「④全体」の4つに仕分け、RAGは探し物のみに限定して専用の道具（セマンティックレイヤー付きSQL、バイテンポラル履歴管理、階層型要約）へ振り分ける設計を提示。さらに500ページ未満のプロンプト丸ごと渡しや、Claude CodeのようにベクトルDBを捨ててオンデマンド探索（grep/glob）に倒す『仕組みを作らない選択』を解説。

## 動画目次・確認済みタイムライン（チャプター）
- UNKNOWN | **オープニング（RAGの基本概念と3年分議事録での方針変更日検索失敗談）** | Gemini報告区間 00:00〜00:46：オープニング（RAGの基本概念と3年分議事録での方針変更日検索失敗談）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **チャンネル紹介（海外Yパパラジオ・シンガポール発信）** | Gemini報告区間 00:46〜01:04：チャンネル紹介（海外Yパパラジオ・シンガポール発信）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **実務経験と問題意識（ハイブリッド検索の限界と似たもの抽出の構造的欠陥）** | Gemini報告区間 01:04〜01:46：実務経験と問題意識（ハイブリッド検索の限界と似たもの抽出の構造的欠陥）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **本日のアジェンダ3点（構造的限界、質問の振替先、作らない選択）** | Gemini報告区間 01:46〜02:02：本日のアジェンダ3点（構造的限界、質問の振替先、作らない選択）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **第1章：RAGが構造的に答えられない質問の本質（図書館の司書メタファー）** | Gemini報告区間 02:02〜03:11：第1章：RAGが構造的に答えられない質問の本質（図書館の司書メタファー）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **限界①「数（カウント・集計）」：上位件数抽出による不正確性と自信満々の誤答** | Gemini報告区間 03:11〜03:35：限界①「数（カウント・集計）」：上位件数抽出による不正確性と自信満々の誤答。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **限界②「時間（時系列・順序）」：意味の近さでの混同と日付絞り込みによる暗黙脱落** | Gemini報告区間 03:35〜04:23：限界②「時間（時系列・順序）」：意味の近さでの混同と日付絞り込みによる暗黙脱落。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **限界③「全体（サマリー・傾向）」：点（検索）を集めても面（全体像）にはならない** | Gemini報告区間 04:23〜05:04：限界③「全体（サマリー・傾向）」：点（検索）を集めても面（全体像）にはならない。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **第2章：質問の仕分け（4つの型：探し物、数える、並べる/いつの時点か、全体）** | Gemini報告区間 05:04〜05:33：第2章：質問の仕分け（4つの型：探し物、数える、並べる/いつの時点か、全体）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **仕分け①「探し物」の強化：Anthropic Contextual Retrieval** | Gemini報告区間 05:33〜06:27：仕分け①「探し物」の強化：Anthropic Contextual Retrieval。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **仕分け②「数える・並べる」：DBへのSQL問い合わせとメトリクス定義シート** | Gemini報告区間 06:27〜07:31：仕分け②「数える・並べる」：DBへのSQL問い合わせとメトリクス定義シート。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **仕分け③「いつの時点か」：バイテンポラル（有効時間と記録時間の2軸管理）** | Gemini報告区間 07:31〜08:15：仕分け③「いつの時点か」：バイテンポラル（有効時間と記録時間の2軸管理）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **仕分け④「全体」：階層型要約（要約ピラミッド）と長コンテキスト丸ごと渡し** | Gemini報告区間 08:15〜08:53：仕分け④「全体」：階層型要約（要約ピラミッド）と長コンテキスト丸ごと渡し。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **第3章：そもそも仕組み（RAG）を作らないという選択肢** | Gemini報告区間 08:53〜08:58：第3章：そもそも仕組み（RAG）を作らないという選択肢。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **作らない選択①：資料が小さい（約500ページ未満）ならプロンプトに丸ごと渡す** | Gemini報告区間 08:58〜09:51：作らない選択①：資料が小さい（約500ページ未満）ならプロンプトに丸ごと渡す。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **作らない選択②：資料更新が速いなら作らない（Claude CodeのRAG廃止とAgentic Search）** | Gemini報告区間 09:51〜10:51：作らない選択②：資料更新が速いなら作らない（Claude CodeのRAG廃止とAgentic Search）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **業界の二極化（Cursor/Copilotのインデックス vs Claude Codeのオンデマンド探索）** | Gemini報告区間 10:51〜11:25：業界の二極化（Cursor/Copilotのインデックス vs Claude Codeのオンデマンド探索）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **まとめ：RAGのその先とは新技術ではなく「1枚の質問振り分け表」** | Gemini報告区間 11:25〜12:05：まとめ：RAGのその先とは新技術ではなく「1枚の質問振り分け表」。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **判断基準の3要素（質問の型、資料の量、更新の速さ）** | Gemini報告区間 12:05〜12:36：判断基準の3要素（質問の型、資料の量、更新の速さ）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **実践ステップ：社内質問20問の4分類とAIルーターによる自動化** | Gemini報告区間 12:36〜13:16：実践ステップ：社内質問20問の4分類とAIルーターによる自動化。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **過去回「OKF（書類の置き方改革）」との接続（地図作りから地図の歩かせ方へ）** | Gemini報告区間 13:16〜14:01：過去回「OKF（書類の置き方改革）」との接続（地図作りから地図の歩かせ方へ）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE
- UNKNOWN | **エンディング（高評価・チャンネル登録の案内）** | Gemini報告区間 14:01〜14:23：エンディング（高評価・チャンネル登録の案内）。字幕の時刻付き原資料はこの保存工程では独立確認していないため、正式時刻はUNKNOWN。 | time_source: UNKNOWN | topics: NONE

## 詳細技術知識・再利用ノート
情報源：Geminiの字幕中心の研究報告。映像・画面は未確認。ChatGPTは動画とNotebookを独立検証していない。
① RAGが構造的に答えられない3つの質問パターン ／ 数（カウント・合計） :
破綻理由 : ベクトル検索・キーワード検索は「類似スコア上位N件」を取得する仕組みであり、全件網羅を保証しない。拾った断片だけから数えるため、抜け漏れが生じて正確な件数・合計金額を算出できない。 ／ 時間（時系列・順序・いつの時点か） :
破綻理由 : 時間軸の前後関係は「意味の類似度」では計測できない。3年前の議事録と先週の議事録に似た方針が書かれていれば、両方とも同等のスコアで抽出される。日付メタデータで絞り込むと、適合件数が裏で黙って減少し、根拠の薄い回答を警告なしで出力する。 ／ 全体（サマリー・全体の傾向） :
破綻理由 : 検索は「点」を拾う仕組みであり、「面（全体像）」を問う質問には対応できない。「案件全体を代表する1枚の断片」はどこにも存在しないため、たまたま拾えた数枚の断片から全体を語る危険なハルシネーションが発生する。 ／ ② 質問の4分類と最適なアーキテクチャの振り分け
1. 「探し物」型 : ／ 推奨手段 : 強化型RAG（[Anthropic Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)）。
技術仕様 : チャンク分割時に各断片の冒頭へ「何の資料の一部か」を1文補記（文脈付与）。これにBM25単語検索とリランキング（再順位付け）を組み合わせることで、検索失敗率を大幅に低減（コストはプロンプトキャッシュ併用で100万トークンあたり約1ドル）。 ／ 2. 「数える・並べる」型 :
推奨手段 : リレーショナルデータベース＋セマンティックレイヤー（事前定義シート）。 ／ 技術仕様 : 検索させずにSQLで集計。ただしDBスキーマをAIにそのまま見せると、AIが毎回独自の計算定義（キャンセルの控除、売上の計上基準など）を発明して数値がブレる。事前に「売上とはこのカラムの合算である」という指標定義シートを1枚用意し、AIには定義を選択させる。
3. 「いつの時点か」型 : ／ 推奨手段 : バイテンポラル（2軸時間）履歴管理。
技術仕様 : 事実レコードごとに有効期間を持たせ、更新時も古い事実を消さずに残す。「現実に起きた時間（Valid Time）」と「システムがそれを記録・認知した時間（Transaction Time）」の2本を保持することで、「過去の特定日時点で組織が認識していた状況」を正確に再現可能にする。 ／ 4. 「全体」型 :
推奨手段 : 階層型要約（RAPTOR / Map-Reduce）または長コンテキスト直接読み込み。 ／ 技術仕様 : あらかじめ詳細要約・中間要約・全体要約のピラミッド構造を事前生成しておくか、大容量コンテキストモデルに丸ごと全件を投入して後から集約する。
③ そもそも仕組み（RAG）を作らないという選択基準 ／ 資料の量が小さい場合（約500ページ / 20万トークン未満） :
[Anthropic公式指針](https://www.anthropic.com/engineering/contextual-retrieval)の通り、RAGを組まずにプロンプトキャッシュを利用して全資料をそのままコンテキストに渡す方が、高速・安価で精度も高い。インデックス更新・保守の永続的運用コストを回避できる。 ／ 資料の更新頻度が高い場合（コードベース等） :
Claude Codeの実例 : 初期はTypeScript製ローカルベクトルDBでRAGを試作していたが、コード変更との同期遅延やインデックス権限管理の課題から早々に廃止。人間のエンジニアと同様に、その場で `glob` や `grep` を用いて自律探索する「Agentic Search」を採用。 ／ 業界の対比 : CursorやGitHub Copilotがインデックス作成を維持しているのに対し、資料の性質（表記揺れが多い自然言語資料＝インデックス/ベクトル推奨 vs 型番・関数名が明確なコード＝オンデマンドgrep推奨）に応じて作り分ける必要がある。
④ 業務導入の具体的実践法 ／ 社内から実際に寄せられる想定質問を20問リストアップし、上記4つの型にマッピングする。
自社の業務がどの型に偏っているかを可視化した上で、仕分け自体を軽量AI（ルーター）に判定させ、各専門ツールへ自動ディスパッチする。 ／ 過去回（OKF：散らかった書類を整える「置き方改革」＝地図作り）と組み合わせ、整えた地図の上をどう歩かせるかという「歩行設計」として運用する。

## 主張・一次資料・時刻
- Gemini動画要約：類似検索の上位チャンクだけでは全件集計・時系列整合・全体傾向に必要な情報を網羅できない場合がある。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- Gemini動画要約：質問を探し物、集計、特定時点、全体傾向に分類し、RAG・指標定義付きSQL・2軸の履歴管理・階層要約を使い分ける。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- Gemini公式資料照合報告：Contextual Retrievalは文脈付与、BM25、再順位付けを組み合わせる。ベンチマーク・費用の数値は本保存工程で独立確認していない。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: https://www.anthropic.com/engineering/contextual-retrieval | time_source: UNKNOWN
- Gemini動画要約：履歴の有効時間と記録時間を分離するバイテンポラルの考え方を紹介。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN
- Gemini動画要約：資料量・更新頻度によっては丸ごと読み込みやgrep/globによる必要時の検索を選び、RAGの構築自体を避ける選択肢がある。 | REPORTED_BY_AUTHOR | time: UNKNOWN | official: UNKNOWN | time_source: UNKNOWN

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。

## 関連研究・資料リンク
- `youtube:u3ka_AAb8qE:research` (COMPLEMENTS): OKF（書類の置き方改革＝地図作り）とRAG（質問振り分け表＝歩行設計）が相互補完関係にある | status: CANDIDATE | evidence: 13:16過去回OKFとの接続言及およびu3ka_AAb8qEの08:16荷札・09:35リンク構造
