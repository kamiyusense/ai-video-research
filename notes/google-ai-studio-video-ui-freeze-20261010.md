# Google AI Studio：YouTube全編調査時のブラウザ停止 調査記録（暫定）

- 調査日: 2026-10-10 JST
- テーマ: 動画の全編一括調査中にChromeの「ページが応答しません」が出る
- 判定: RELATED_REPORTS_CONFIRMED / ROOT_CAUSE_UNKNOWN / PERMANENT_FIX_UNKNOWN
- 状態: STATIC_RESEARCH_ONLY / NO_INSTALL / NO_LIVE / NO_BILLING
- 対象: 動画研究チームの映像担当（Google AI Studio）
- 連続研究: [認識ズレ対策シリーズ](cognitive-drift-video-series-20261010.md)

## ユーザー提供の観測（ブラウザスクショと本人の報告）
1. AI StudioでGemini 3.8 Flashを使用し、短い「冒頭60秒、3件」調査は回答完了（画面上7.4秒）。
2. 同じ約8分半のYouTube動画について、全編詳細報告では複数回フリーズ。思考レベル「低」、短くした報告、別ブラウザなどを試しても成功しないとの報告。
3. Chromeの応答停止ダイアログにAI StudioとGemini Sparkが同時表示。YouTube、X、U-NEXTは動作していたとの報告。
4. WindowsタスクマネージャーではCPU約9%、メモリ約53%、ディスク約1%（当該画面の瞬間値）。本人申告ではフリーズ中も大きな急上昇を見なかった。GPU使用率、個別ChromeプロセスPID、DevToolsエラー、処理段階の確定値はUNKNOWN。
5. AI Studioに報告文が出力され始めた画面もあったが、最終全文回収は失敗。一時チャットは履歴に残らなかった。ブラウザ停止原因とモデルの動画解析成功/失敗を同一視しない。

## 一次資料からの確認
- Google公式動画入力: https://ai.google.dev/gemini-api/docs/video-understanding （YouTube動画は映像入力としてサポート。入力上限から約8分半という尺自体を原因とは断定しない。Agentic動画処理はAPI仕様。AI Studio UIで選択可能かはUNKNOWN）
- Chromium設計: https://chromium.googlesource.com/chromium/src/+/main/docs/process_model_and_site_isolation.md （Chromeは複数のレンダラで隔離。条件によって同一サイトの処理を共有。AI StudioとSparkが同じプロセスを実際に共有していたかは**UNKNOWN**）
- Chrome公式障害対処: https://support.google.com/chrome/answer/142063?hl=ja （拡張機能、サイトデータ、描画支援などの一般的な切り分け）
- Gemini SparkのChrome連携: https://support.google.com/chrome/answer/16821166?hl=ja （Chromeローカルブラウザとの接続機能がある。ただしユーザーがこの機能を実行していたかはUNKNOWN）

## Google開発者フォーラム（利用者報告、同一原因の証明ではない）
- 2026-01-06: https://discuss.ai.google.dev/t/ai-studio-is-getting-slow/114187 （64GB RAMでもAI Studio表示が鈍化したという報告。低いOS全体メモリ使用量でもAI Studio UIに問題が起き得る）
- 2026-05-23: https://discuss.ai.google.dev/t/google-ai-studio-freezes-during-conversation-and-requires-clearing-chat-to-continue/58535 （キャッシュ無関係の画面遅延をCSSの改変で回避した利用者報告）
- 公開非公式回避プログラム: https://github.com/xgloom/fix-aistudio-lag （ソースを直接確認。変更内容はbackdrop-filterとscroll-behaviorを全要素に対して無効化。Tampermonkey等のインストールを現時点で推奨しない。実機効果UNKNOWN）
- 2026-04-30: https://discuss.ai.google.dev/t/bug-ai-studio-web-ui-video-upload-stuck-on-extracting-500-internal-server-error/142958 （Chrome/Edgeで動画処理が失敗し、APIでは成功という利用者報告。Google関係者は小動画で再現せず、サーバー容量による一時障害の可能性を指摘。**ユーザーのYouTube応答表示停止とは症状が異なる**）
- 2026-10-01: https://discuss.ai.google.dev/t/ai-studio-video-processing-fails-with-http-500-using-a-paid-api-key-text-only-requests-succeed/186360 （Gemini 3.8 Flash動画抽出エラー HTTP500。有料APIキー使用ケース。今回のページ無応答と混同しない）
- 2026-09-24: https://discuss.ai.google.dev/t/ai-studio-agent-execution-terminated-fixed-by-clearing-aistudio-google-com-site-data-in-chrome/184597 （Windows11/Chrome/3.8 Flashで対象サイトのローカルデータ削除後に復旧した事例。障害メッセージが異なり成功保証なし。削除前に一時チャットの消失リスク説明が必要）
- 2026-05-27: https://discuss.ai.google.dev/t/google-ai-studion-being-slow-and-not-productive-for-daily-productions/167020 （複数一般設定を試しても改善しない報告）
- 参考：https://statusgator.com/services/google-ai-studio-and-gemini-api （第三者の障害集約には2026-10-09/10の問題報告があるが、今回のUIフリーズと同じ事象かはUNKNOWN）

## 因果関係の優先順位（推測を明示）
1. PRIORITY_HIGH: AI Studio Web UI内のレンダリング・イベントループ・スクリプト問題。理由: Chrome上で長い回答が表示途中の停止、別サイト正常、利用者に類似報告。ただしログなしで確定できない。
2. PRIORITY_MEDIUM: Google側の動画入力処理や一時障害。理由: 同時期の動画処理エラー報告。今回は短い動画内容照会に成功、途中までの回答を表示しているため同一とは限らない。
3. PRIORITY_MEDIUM: 同一ブラウザのプロセスやGoogleサイト側共通要因によるSpark巻き込み。**Sparkの同時表示は証拠だが、PID未取得のため同一rendererとは証明できない。**
4. PRIORITY_LOW: PC全体のCPU・RAM不足。瞬間値は高負荷を支持しないが、GPUや個別rendererの一時停止・瞬間スパイクはまだUNKNOWN。

## 現実的な運用と未解決
- 既に同じ試行が3回以上失敗したため再投入を繰り返さない。報告未回収はVISUAL_UNKNOWN。Gemini Sparkから届いた独立字幕報告は別証拠として保存し、映像確認済みにすり替えない。
- Drive保存は**チャットの損失軽減策**であり、Chromeフリーズの修正ではない。URLコンテキストは動画理解用の動画入力とは別。
- より低負担の代替: Geminiアプリで公開YouTubeの内容を尋ねられる（https://support.google.com/gemini/answer/16622858?hl=ja）が、特定の画面実演をフレーム単位で直接解析したと自動判定しない。NotebookLMもYouTubeは文字起こしのみ（https://support.google.com/gemininotebook/answer/16215270?hl=ja）。
- APIでYouTube動画入力を使う選択肢はあるが、APIキー/課金/追加認証/モデル起動の承認が必要なため**現段階では実施しない**。
- 後日再調査の検討候補: ユーザー希望があればChrome専用タスクマネージャーでrenderer PID、Chromeの当該サイトだけの保存データ、GPU描画、開発者ツールのエラーを非破壊で調べる。今は再現操作を依頼しない。
- 根本原因・恒久的な公式修正: UNKNOWN。別の無保証なプロンプト書き換えや動画分割を「解決策」と断定しない。

## 調査の境界
このファイルは公開一次資料・利用者報告・ユーザーからのスクショに基づく独自メモ。ユーザーPCの内部プロセスやネットワークログは未取得。ファイル作成以外のLIVE実行、外部AI起動、モデル設定/課金/権限変更、他repository変更、Mergeなし。
