# 動画08：YouTube to NotebookLM 拡張機能の一括収集（暫定研究）

- video_id: ZjUJ-35acaU
- 動画: https://www.youtube.com/watch?v=ZjUJ-35acaU
- タイトル（Sparkの字幕解析報告）: 【超便利】Google最強AI「NotebookLM」×「YouTube」の拡張機能が神！徹底解説していきます！
- 投稿者（Spark報告）: mikimiki web スクール
- 公開日（Spark報告）: 2026-03-21
- 長さ（Spark報告）: 21分23秒
- 調査・公式照合日: 2026-10-10
- 取得手段: ユーザーが実行したGemini SparkがYouTube API由来のメタデータ・文字起こしを解析したと報告。ChatGPTは映像・字幕・音声を直接取得していない。**映像の実演確認はUNKNOWN**。
- status: SPARK_REPORT_RECEIVED / OFFICIAL_DOC_CROSSCHECK / VISUAL_UNKNOWN / NOT_INSTALLED / LIVE_NOT_RUN

## 結論
紹介されている第三者製Chrome拡張 `YouTube to NotebookLM - YouTube to Gemini Notebook` は、単一動画・検索結果・プレイリスト・チャンネルの動画URLをNotebookLMへまとめて追加する導線を提供する。大量の**字幕ベース**の学習・横断比較には有望だが、Google公式の仕様上YouTubeから取り込まれるのは**文字起こしだけ**。映像・スライド・細かい画面操作の理解はできない。研究室では③独立調査担当の入力作業削減候補であり、②映像担当の代わりではない。

## Spark報告の要点と時刻（動画原本の独立確認はUNKNOWN）
- [00:17](https://www.youtube.com/watch?v=ZjUJ-35acaU&t=17s): NotebookLMのソース限定回答と複数動画手動登録の負担について。
- [01:40](https://www.youtube.com/watch?v=ZjUJ-35acaU&t=100s): Chrome拡張導入の説明。
- [02:02](https://www.youtube.com/watch?v=ZjUJ-35acaU&t=122s): 動画を新規・既存ノートブックへ登録する操作の説明。
- [03:01](https://www.youtube.com/watch?v=ZjUJ-35acaU&t=181s): 検索結果19本を一括登録する例の説明。
- [04:43](https://www.youtube.com/watch?v=ZjUJ-35acaU&t=283s): チャンネル動画の一括登録、300ソースの例。
- [08:51](https://www.youtube.com/watch?v=ZjUJ-35acaU&t=531s): 動画に基づくFAQ作成と引用の確認。
- [12:07](https://www.youtube.com/watch?v=ZjUJ-35acaU&t=727s): 19本のSEO動画に共通する原則を抽出する例。
- [16:15](https://www.youtube.com/watch?v=ZjUJ-35acaU&t=975s): 複数動画のテーマ別グルーピング。
全てSparkによる字幕報告を元にした時刻。ウチがフレームや元動画を直接確認したわけではない。成功時間や実行結果も独立計測していない。

## ④検品：一次資料と照合済み
1. Google公式ソース追加仕様: https://support.google.com/gemininotebook/answer/16215270?hl=ja
   - 公開動画、字幕が必要。自動字幕も可。取り込まれるのは**テキスト文字起こしのみ**。
   - 72時間未満の新規公開動画、発話なし、字幕なし等は取り込み不可の場合あり。動画長には原則制約なし、ただし字幕500,000語上限。
2. Google公式アクセス・ソース上限: https://support.google.com/gemininotebook/answer/16213268?hl=ja
   - 利用区分で1ノート50/100/300/500/600ソース。300本をどの契約でも入れられるという意味ではない。
3. Google公式のソース参照回答: https://support.google.com/gemininotebook/answer/16179559?hl=ja
   - 引用をたどれるソース基準の回答。引用があっても無誤り保証ではない。
4. Chromeウェブストア実在: https://chromewebstore.google.com/detail/kobncfkmjelbefaoohoblamnbackjggk
   - 提供元 `yt.to.notebooklm` の**第三者製**拡張。動画・検索結果・プレイリスト・チャンネル取り込みを説明。Google純正ではない。
   - 日本語を含む多言語対応の表示があるが、日本語での全機能実地試験はNOT_RUN。
   - ユーザーの活動情報を扱うと申告。詳細な権限・外部通信・現行版の内部API方式は未監査。
5. 第三者セキュリティ分析: https://mantis.sh/audits/youtube-to-notebooklm （潜在的な権限範囲への注意。悪用の事実やセキュリティ事故の証明ではない）。

## 検品結果
- CONFIRMED_DOC: Google NotebookのYouTube文字起こし対応、字幕・公開制限、ソース上限、Chrome拡張の存在と宣伝する一括登録機能。
- VIDEO_REPORT_ONLY: 19本・300ソースの実演、処理時間、FAQ/SEO比較の成功。字幕報告の範囲で説明可だがフレームの独立検証なし。
- UNVERIFIED: 内部の非公開API呼出し方式、無料利用での一括転送上限、現行拡張版のブラウザ権限詳細、日本語操作、安定性。
- NOT_APPLICABLE: NotebookLMで映像フレームの直接解析。Google公式によりYouTubeソースは文字起こしのみ。
- 判定: **PARTIAL_PASS（重要な仕様は照合済み、映像・拡張実機効果はUNKNOWN）**。
- 未実行: 拡張インストール、実機動作、外部モデル実行、追加課金、GitHub以外への外部書込み。

## 研究室への適用案（ChatGPT独自）
- まず標準のNotebookLMで公開動画を単体登録し、字幕ソースと時刻・引用が期待どおり取得されるか検証する。
- 多数の動画を選定・一覧投入する必要が生じたら、第三者製拡張の権限・無償範囲・取り込み件数・重複/取りこぼしを確認した上で導入可否を判断。
- 機密資料やprivate GitHubの情報を未知の拡張へ渡さない。NotebookLMは一時的な字幕調査用で、GitHubの共有記憶の正本を置き換えない。
- 映像の検証には別手段が必要。ユーザーに何度も動画分割・貼り直しを求めない。

## 次の研究課題
- ②映像担当の代替となる**映像フレームを直接取得・理解する**仕組みは別途調査。
- 一括登録の拡張機能の安全性と無料枠を導入前に比較。
- YouTube字幕へのタイムスタンプ引用精度、300本処理の取りこぼし等はUNKNOWN。
