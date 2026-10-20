# 【注意】索引の役割分離について (`AI技術研究室_知識索引.md` vs `github_knowledge_index_export.md`)

1. **Gemini Notebook 内の既存総合索引 (`AI技術研究室_知識索引.md`)**:
   - Gemini Notebook（`https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7`）の内部には、先行する16ソース等の知識を統合した**Notebook側の総合索引**が存在します。
   - それを GitHub 側で生成したファイルで丸ごと上書き置換すると、Notebook 固有の蓄積を損なう危険があります。

2. **GitHub 正本側の知識索引・差分エクスポート ([`github_knowledge_index_export.md`](github_knowledge_index_export.md))**:
   - v0.3 以降、`receipt_to_research.py` が GitHub の全ブランチ（`registry.json`・`research/*.md`・`notes/*.md`）から自動生成する台帳・差分エクスポートは、同名の混同を避けるため **[`automation/gemini-notebook/state/github_knowledge_index_export.md`](github_knowledge_index_export.md)** に出力されます。
   - **GitHub への保存成功は、Gemini Notebook への同期完了を意味しません** (`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`)。
   - Gemini 側で GitHub 側の既知 `video_id` や次回調査テーマ (`next_topics`) を参照する際は、[`github_knowledge_index_export.md`](github_knowledge_index_export.md) を参照し、Notebook 内の総合索引へは差分のみを追記してください。
