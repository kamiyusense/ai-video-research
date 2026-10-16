# Gemini Notebook AI技術研究室: 継続研究Loop v0.1

**目的**: 動画を読む回数を増やすことではなく、Geminiが既存Notebookの知識を使って、自分で新情報を発見し、検証して、差分だけを蓄積する**一連の自動研究ワークフロー**を作る。

## このブランチで具体的に用意したもの

| 部品 | 場所 | 段階 |
|---|---|---|
| GeminiネイティブTaskの単一運用指示 | [GEMINI_TASK.md](GEMINI_TASK.md) | READY_TO_PASTE（Gemini側実行未確認） |
| 知識差分からGitHub正式研究記録を作るローカル変換器 | [receipt_to_research.py](receipt_to_research.py) | STATIC_IMPLEMENTED（既存GitHub自動pushなし） |
| 既存担当制と研究台帳 | ルート `AGENTS.md`, `MEMORY.md`, `registry.json`, `docs/SPECIALIST_WORKFLOW.md` | REUSED |

**すでにGeminiの利用者報告**: 6動画を一度に調査できる、Notebookへ計16ソースの登録・readbackができる。これらを今さら1本→2本という粒度で再検証しない。

**今回はこの環境からGemini本人を起動していない**。Google Notebookへの直接アクセス、Gemini側のスケジュール設定、GitHubへのGemini自身の認証接続、常時巡回は NOT_WIRED / UNKNOWN。

## 対象・構成

- 補助知識庫: [Gemini Notebook「AI技術研究室」](https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7)
- 正式な研究記録: private GitHub `kamiyusense/ai-video-research`、非default branchでPR審査。別repoへの書込みは禁止。
- 自動実行の第一候補: Geminiの公式TaskによるNotebookネイティブ検索・取得・更新。新しいAPI契約・非公式Cookie/MCP・有料外部モデルを前提にしない。
- Geminiからprivate GitHubへの**直接pushは未確認**。この溝を「完全自動」と呼ばず、JSONの研究結果を中継する。

```text
Gemini Task（1回の実行で研究Loop全体）
  ├─ Notebook索引と過去の研究を読む
  ├─ YouTube・公式資料から候補発見
  ├─ 重複を除外し、重要な動画だけ調査
  ├─ 公式照合・NEW / UPDATED / CONFLICT / UNKNOWN
  ├─ Notebookへ差分ソース追記・索引保全・readback
  ├─ 次回調査テーマを選ぶ
  └─ research_receipt_v1 を出力
        ↓
GitHub受渡し（現段階は未接続、出力JSONの手動受領可能）
        ↓
receipt_to_research.py（ローカルで重複判定、研究Markdown・registry生成）
        ↓
非default branchで内容確認 → 必要ならcommit/PR（自動化は未接続）
```

## 今すぐ使う手順（毎動画ではなく最初の設定だけ）

1. `GEMINI_TASK.md` 全文を、Geminiの新規Taskへ**1回だけ**貼り付ける。タスク単位で発見・照合・Notebook更新・索引更新・結果出力まで連続実施させる。研究対象動画のURLをユーザーが毎回探す必要はない。
2. Gemini側のNotebook操作許可を確認。定期実行の設定は**まだ行わない**（継続的な無人更新の実機動作が不明なため）。Notebookとの連携が一度通った後にスケジュール検討。
3. Geminiの返した `research_receipt_v1` JSONを機械読み込みに渡せば、GitHub形式への変換・重複判定ができる。以下は**ローカルでの実行例**。コードはGithubへ自動通信しない。

```bash
python automation/gemini-notebook/receipt_to_research.py receipt.json
# 内容確認・非default branch checkout後、明示的に必要なときだけ:
python automation/gemini-notebook/receipt_to_research.py receipt.json --apply
git diff -- registry.json research/
```

このスクリプトはプレビューが初期値。 `--apply` はローカル作業ツリーを変更するだけで、GitHubへcommit・pushはしない。main/master、予期しないoriginでは書込み拒否。字幕全文や動画は保存しない。Notebook readback PASSで、かつ新規のvideo_idだけを作成する。

## 先駆者から移植した設計

- **Ingest / Query / Lint**: 発見した情報をそのまま追加せず、過去の知識を検索し、既知・新規・矛盾・古さを整理。
- **Write-time dedupe**: 動画ID・既存記録・公式URLを照合し、毎回同じものを量産しない。
- **Evidence-first**: 字幕から分かったこと、映像で確認したこと、公式仕様、開発者自身の主張、実モデル検証を区別。
- **GitHub正本 / Notebook補助**: GitHubの非公開素材を許可なく外部ストレージに移さない。Notebookには独自要約とリンクのみ。
- **Stop-on-unknown-write**: 反映したか不明なら再送より読み戻しを優先。

## 正直な未完成部分と次の優先順位

1. **Gemini Taskの単一run**で、候補発見からNotebookへの差分保存までを実運用する（既存の複数動画読込テストは繰り返さない）。
2. **Gemini結果→非公開GitHub**を、ユーザーの追加入力なしで送る安全な公式連携経路の確認。現段階ではJSON受渡しとローカル変換器までで、*無人同期は未実装*。
3. **定期起動**は、Gemini側の実行権限・通知・クォータ・失敗時の挙動が確認できてから設定する。定期化前でも、単一Taskの再実行だけで研究Loopを繰り返せる設計。
4. 未Mergeの研究Draft PR群に情報が分散しているため、統合後のGitHub台帳とNotebook側video_idの差分を必ず確認する。現段階の `registry.json` がNotebook全件を網羅しているとは扱わない。

## 今回やらないこと

「動画を2本同時に読めるか」の再テスト、任意の外部モデル追加起動、従量API、Cookie抽出、非公式Notebook API、実スケジュール登録、個人情報の転送、Github mainへの直接書込み、PR Merge、他repo変更。静的コード/運用手順の準備と、接続可能箇所を使った最短ルートを優先する。
