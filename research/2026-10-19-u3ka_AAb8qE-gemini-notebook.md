---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "【研究カード】 【OKF実践】AI時代の知識管理とオープンナレッジフォーマット v0.2"
description: "オープンナレッジフォーマット（OKF v0.2）に基づく文書構造化手法を解説。資料先頭の標準荷札、1件1ファイルの資料分割、意味付けされた双方向リンクによる知識ネットワーク構築。"
resource: "https://www.youtube.com/watch?v=u3ka_AAb8qE"
tags:
  - "AI技術研究室"
  - "動画研究"
logical_id: "youtube:u3ka_AAb8qE:research"
record_id: "youtube:u3ka_AAb8qE"
video_id: "u3ka_AAb8qE"
canonical_url: "https://www.youtube.com/watch?v=u3ka_AAb8qE"
original_url: "https://www.youtube.com/watch?v=u3ka_AAb8qE"
publication_date: "2026-08-20"
checked_at: "2026-10-19"
source_scope: "ユーザー提供字幕（主要タイムスタンプ付き区間 08:16〜16:33）およびYouTube動画情報を分析"
transcript_logical_id: "youtube:u3ka_AAb8qE:transcript"
related_transcript_id: "youtube:u3ka_AAb8qE:transcript"
transcript_status: "UNVERIFIED"
primary_source_notebook_id: "UNKNOWN"
document_type: "AI技術研究室 構造化研究カード（二次分析資料）"
notebook_readback: "UNKNOWN"
github_verification: "NOT_RUN"
github_to_notebook_sync: "NOT_SYNCED_FROM_GITHUB"
changes:
  - "NEW"
related_records:
  - target_id: "youtube:pRfC1DILDEM:research"
    relation: "COMPLEMENTS"
    note: "RAG探索設計（pRfC1DILDEM）とOKF知識体系が相互補完関係にある"
    status: "CONFIRMED"
    evidence: "08:16荷札とpRfC1DILDEMの13:16言及"
---

# 【研究カード】 【OKF実践】AI時代の知識管理とオープンナレッジフォーマット v0.2

> [!IMPORTANT]
> **文書区分**: 本ドキュメントは一次資料（YouTube字幕）を基に構造化分析した「AI技術研究室 研究カード」です。Notebook内の一次資料YouTube動画そのものではありません。回答引用時は「一次資料（動画）」と「本研究カード（構造化分析）」を明確に区別してください。

> [!NOTE]
> **資料識別・Notebook UI参照案内**:
> - **動画ID**: `u3ka_AAb8qE`
> - **資料論理ID**: `youtube:u3ka_AAb8qE:research`
> - **対応字幕原文論理ID**: `youtube:u3ka_AAb8qE:transcript`
> - **UI制限事項**: NotebookLM UI上ではソース間直接リンクのクリックジャンプができない仕様です。対応する字幕原文を参照する場合は、上記『対応字幕原文論理ID (`youtube:u3ka_AAb8qE:transcript`)』または『動画ID (`u3ka_AAb8qE`)』をもとに、Notebookのソース一覧から検索・特定してください。

## 独自要約
オープンナレッジフォーマット（OKF v0.2）に基づく文書構造化手法を解説。資料先頭の標準荷札、1件1ファイルの資料分割、意味付けされた双方向リンクによる知識ネットワーク構築。

## 動画目次・確認済みタイムライン（チャプター）
- [08:16〜09:08](https://www.youtube.com/watch?v=u3ka_AAb8qE&t=496s) | **荷札（メタデータによる資料識別）** | 資料冒頭のYAMLフロントマターによるメタデータ識別原則を解説。 | time_source: TIMESTAMPED_CAPTIONS | topics: OKF, YAMLフロントマター, メタデータ
- [09:35〜10:11](https://www.youtube.com/watch?v=u3ka_AAb8qE&t=575s) | **リンク（関係の意味付けと双方向参照）** | 資料間を意味付きリンク（COMPLEMENTS等）で結び、双方向参照を可能にする設計。 | time_source: TIMESTAMPED_CAPTIONS | topics: Links, 関係種別, Graph

## 詳細技術知識・再利用ノート
【OKF v0.2の中核概念】
1. 荷札（YAMLフロントマター）: 資料の冒頭に type, title, description, resource, tags 等の統一メタデータを付与し、人間とAIの両方が即座に資料の性質を把握できる。
2. 1件1ファイル原則: 巨大なドキュメントを分割し、1つの概念や研究を1ファイルに収めることで、AIの検索精度と再利用性を最大化する。
3. 意味付けされたリンク（typed relations）: 単なるURL参照ではなく、COMPLEMENTS, EXTENDS, UPDATES 等の関係種別を明記して相互接続する。

【RAGとの役割分担】
OKFは「書類の置き方改革（地図作り）」であり、RAG（質問振り分け表・歩行設計）と組み合わせることで真価を発揮する。

## 主張・一次資料・時刻
- OKF v0.2では資料先頭にYAMLフロントマター（荷札）を配置し、必須メタデータを標準化する | CONFIRMED_DOC | time: [08:16](https://www.youtube.com/watch?v=u3ka_AAb8qE&t=496s) | official: https://github.com/GoogleCloudPlatform/open-knowledge-format | time_source: TIMESTAMPED_CAPTIONS
- OKFとRAGは対立するものではなく、書類整理と検索エンジンの関係として相互補完する | REPORTED_BY_AUTHOR | time: [09:35](https://www.youtube.com/watch?v=u3ka_AAb8qE&t=575s) | official: UNKNOWN | time_source: TIMESTAMPED_CAPTIONS

## 関連する既存研究・課題との接続
- [youtube:pRfC1DILDEM:research](2026-10-18-pRfC1DILDEM-gemini-notebook.md) (COMPLEMENTS): RAG探索設計（pRfC1DILDEM）とOKF知識体系が相互補完関係にある | status: CONFIRMED | evidence: 08:16荷札とpRfC1DILDEMの13:16言及

## 限界
Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。
