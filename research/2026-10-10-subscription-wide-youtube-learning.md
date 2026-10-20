# 契約全体から選ぶYouTube AI学習・技能蓄積・自動化の構成
確認日: 2026-10-10 / Asia/Tokyo
対象: 個人ChatGPT Plus、個人Google AI Pro、日本・Windowsの利用を想定。
状態: CONFIRMED_DOC（一次資料調査）。動画分析・他モデル起動・アカウント別機能実証は NOT_RUN。
本書は前回の4製品中心の調査を拡張し、現在の推奨判断を置き換える。旧調査は履歴として残す。

## 1. 判断
品質と契約内利用を優先する推奨候補は、
**Google AI Studio Playgroundで公開YouTubeの映像・音声を分析 → ChatGPT Deep Researchで主張を公式資料と照合 → Work/Codexで説明、再現手順、再利用する技能とGitHub記録を作る。**
AI StudioのYouTube視覚入力は公式実例[G03]、現在のPro契約内UI枠は[G02]に根拠がある。これは異なる年代の資料を合わせた構成上の判断であり、相棒の現行UIで動作確認済みという意味ではない。
「両契約を持つ場合」の案であり、片方の契約だけでも下記の構成を使える。両方の新規契約を要求しない。

相棒の操作を減らす優先候補は **ChatGPT/Work + ネイティブvidIQ装備**。公開URLから字幕とVideo Watchを取り出す経路があり、同じ会話で検証と記録へ進める[X01]。ただし別会社の無料枠・保存条件・初回接続が必要で、技術解説の細かい画面文字や全編網羅性は未実証。大量研究の唯一の入口にはしない。
「相棒はURLを渡すだけ、その後は全部自動」の完成済み環境は今回確認していない。研究結果、連携設計、導入済み、実測成功を別に扱う。

## 2. 調査範囲
料金ページ・契約特典一覧を起点に、入力、調査、記憶、技能化、実行、自動起動、出力、周辺特典へ展開した。下記は確認日の公式一覧と関連公式資料からの棚卸し。全世界の非公開実験、全プラグイン、全ユーザーへの段階提供を網羅した保証ではない。
判断条件は、(1)映像と音声の取得根拠、(2)非技術者の手間、(3)既存契約内、(4)情報の検証可能性、(5)全文を保存しない、(6)再利用と復旧、(7)日本・Windows、(8)サービス継続性。根拠のない性能点数は付けない。

## 3. ChatGPT Plus側の機能棚卸し
契約全体の起点は[O01][O02]。各製品の追加条件は個別資料を優先する。

|機能・製品群|今回の役割・選定|制約／状態|根拠|
|---|---|---|---|
|通常Chat・推論・Search|説明、軽い公式確認、用語・矛盾の整理。採用|URL受理から動画視聴を推測しない|O01/O02|
|Deep Research|字幕・映像観察から抽出した主張を公式ドメイン中心に照合。採用|対応アプリは読み取り。保存処理はWork等の別工程|O04|
|Work: desktop/local・web/mobile/cloud|長い調査、ファイル成果物、連携作業。採用|localは端末と許可、cloudは別環境。同じローカル画面のミラーとは限らない|O03|
|Codex: desktop・Cloud・CLI・IDE|記録の整形、重複検査、技能・評価・ハーネス案、静的再現。採用|ChatGPT認証とAPIキー利用を区別。Workと利用枠共有|O07|
|内蔵／cloud browser・computer use|公式ページ確認、許可済みサイトの連携候補|AI Studio専用連携、動画の全編認識、ユーザー環境での自動操作はUNKNOWN|O03/O05|
|Projects・指示・Memory・Library|説明方針と独自ノートの参照。採用|知識の唯一の正本にしない。添付の保存はチャット削除と別|O03/O12|
|Plugins・Apps・MCP・GitHub/Drive等|利用可能な取得道具と保存道具。必要時採用|接続・権限・利用場所・提供者料金は別々。汎用MCPから動画理解を推測しない|O08|
|Skills／再利用する指示|Codexの技能候補と持ち運べるMarkdownを用意|ChatGPT側のworkspace Skillsの対応プランを、そのまま個人Plusへ拡張しない。資料間差はアカウント確認が必要|O09|
|Scheduled Tasks・Workの接続アプリイベント|後日、公式更新の監視・未処理URLの発見に候補|Projectのファイルを自動参照できる前提にしない。GitHubイベントの実配送は未実証|O06|
|ファイル分析・画像入力・画像生成・Canvas・表／図|画面の小さい文字の補助確認、独自教材作成、台帳、理解図|権利のある入力のみ。生成画像・動画は原動画の証拠ではない|O01/O02|
|Study mode|相棒への段階説明・理解確認・演習に候補|AI自身の技能習得や動画取得装置ではない|O11|
|Voice／Live・画面共有・Record|短い場面の相談や口頭の復習に補助候補|新Liveは当初video/screenshare非対応。旧機能・OS差を混同しない。長い動画の全自動視聴には使わない|O10/O07|
|Office/Sheets拡張・Sites・可視化|独自ノートや教材の見せ方。補助候補|動画取得の欠落を埋めない。公開・外部アプリ利用料金は別確認|O02/O08|
|対応外部アプリの契約枠共有|ハーネスの拡張候補|対応サービス限定、別途許可、同じWork/Codex枠を消費。独自費用やcredit opt-inは別|O17/O18|
|旧Agent・Atlas・Sora・Pulse|新しい研究室の中核から除外|現行の終了・移行資料を優先。旧紹介記事だけでは現在の利用を断定しない|O13/O14/O15/O16|
|dot／Workspace agents・法人知識・管理機能|範囲比較で確認、Plusの基本構成から除外|Plusに常時稼働dotが含まれると扱わない。法人プラン機能を混ぜない|O02/O16|
|買物・Health/Finances等の生活支援|棚卸しで確認、今回は除外|AI技術動画の研究・再現に直接寄与しない|O02|

## 4. Google AI Pro側の機能棚卸し
契約全体の起点は[G01]。付帯特典の利用資格、年齢、家族管理者、地域、体験版は製品ごとに異なる。

|機能・製品群|今回の役割・選定|制約／状態|根拠|
|---|---|---|---|
|Gemini通常会話・YouTube接続|URLから内容を把握する手軽な入口。採用候補|公開情報と映像・音声の分析範囲を実測して区別。Activity条件もある|G06|
|Google AI Studio Playground|映像・音声を含む公開YouTube分析。品質重視の第一候補|ProのUI契約枠を使う。現行アカウントの動画入力UIは未実証|G02/G03|
|AI Studio Build・Code Assistant|動画から独自教材・試作を作る補助候補|試作を生成できることと、公開アプリが追加費用なしで動くことは別|G02/G03|
|Gemini app Deep Research|Google側だけで公式資料・関連技術を照合。採用候補|AI Studio内の同名agentとは費用条件が異なる|G01/G02|
|Gemini Notebook（NotebookLM）|検証後の独自ノートを複数まとめる、復習教材に候補|YouTube直接追加は字幕全文を資料として取り込むため、今回の全文保存禁止では採用しない|G17|
|Gemini in Chrome・YouTubeに相談|閲覧中の質問・公式資料との並行確認。手間の少ない補助|通常Chrome支援は日本語・Windows対応。YouTubeのAI質問は一部動画のみ|G08/G19|
|Chrome auto browse|ブラウザの多工程を代行する候補として評価|公式資料はPC米国／英語、契約一覧は米国・インド。日本の通常支援から自動操作利用を推測しない|G09/G01|
|Gemini Spark・Schedules|Google内の継続研究、ブラウザ・資料連携の候補|専用helpはProと広域対応、契約一覧はUS-only。日本の実利用はUNKNOWN。local browserの確認やログイン介入もある|G10/G11/G01|
|Gems／Gemini Skills|整理・説明の再利用指示に候補|個人Gemsは2026-11移行予定。現在SkillsはDeep Research/Canvas/Guided Learning等と非互換|G12/G13|
|Guided Learning・Gemini Live・Canvas|理解確認・説明・独自教材作成に補助|動画URLからの教材化案内はあるが、各機能とSkillの併用や全編視覚理解を推測しない|G18/G12|
|Antigravity|実装案、ブラウザの確認、静的検証、技能化に候補|別のIDE型実行役。YouTube入力の専用認識装置とは確認できていない|G01|
|Jules|記録を受けたコード改善・非LIVE実証計画に候補|YouTube視聴役として採用しない。今回起動しない|G01|
|Gemini CLI／Code Assist／Android Studio|Googleログインの契約枠で記録・公式照合・技能を扱う候補|CLIのweb_fetchは動画非対応のURL Contextを利用する。URL取得と動画入力は別|G14/G15/G16|
|Colab|権利のあるデータでOCR／評価等を試す補助候補|Pro特典は200CCU等の資格条件あり。外部API費用を肩代わりする枠ではない|G01|
|Developer Program／Firebase Studio|将来の技能試作・ハーネス研究に候補|Googleプロファイル連携やCloud側条件あり。Cloud creditを無制限のAPI利用と扱わない|G01/G02|
|Google Search AI Mode／Deep Search|公式更新・資料・実装の発見に補助|地域・言語・機能差。動画全編を認識する入口とは別|G01|
|Gmail/Docs/Sheets/Slides/Meet/Drive/Vids等|独自ノート、表、教材の整形・保存に補助|個人Proと法人Workspace契約は同一ではない。新規接続と共有は別許可|G01|
|Flow・Flow Music・Veo・画像生成、旧Whisk/ImageFX|説明用の独自素材制作に補助|YouTube解説の事実取得には不要。credits消費する制作を基本経路に入れない|G21/G22|
|Opal／Gems made by Labs|ノーコード自動化の比較対象、基盤から除外|2026-11-17終了予定、既存workflowは自動移行しない|G23|
|YouTube Premium Lite|視聴の快適性に補助|AIの動画取得・モデル枠・素材を書き出す権利の証拠にはしない|G20|
|Photos・Earth・Playground・Dreambeans・TV等|周辺／創作特典として確認、今回は除外|一部はUS-only。技術動画の理解・検証・技能化には直接不要|G01|
|ストレージ・Home・Health等の付帯特典|契約全体の確認対象、今回は除外|保存容量は情報の正しさや自動実行の能力を増やさない|G01|

## 5. 取得方式を混同しない
|取得方式|得られるもの|今回の判断|
|---|---|---|
|公開YouTube URLを動画入力として渡す|映像・音声のモデル入力になり得る|AI Studioの公式例あり。取り込んだID・処理範囲を実測する|
|Gemini/Ask YouTubeにURL・動画の質問|内容への回答|処理の内部方式・全編視覚取得を断定しない|
|字幕・文字起こしを読む|発話、字幕に含まれる説明|画面操作・無言の図・コード・細かい設定を失う|
|Chrome/Workでページを開く|ページ情報、ブラウザ操作|動画ピクセル・音声の全編入力を保証しない|
|CLI web_fetch／URL Context|対応Webページ等|公式でYouTube・動画・音声非対応。専用video入力を別途使う|
|動画ファイルを添付|対応製品の動画入力|今回の「動画を保存しない」方針では標準経路にしない|
|生成動画・図・教材|理解を助ける独自成果物|原動画の事実を確認した証拠にはしない|

映像入力でも全フレーム・全ての細字を確実に読むわけではない。動画理解APIにはサンプリング、時刻区間、解像度、agentic processingの説明がある[G04/G05]。そのAPIのFPS設定・時間上限・無料枠を、AI Studio UIやGemini appにそのまま転記しない。
重要な設定名・コード・図は、対象時刻の範囲で再確認し、読めなければUNKNOWNにする。モデルの「見ました」という自己申告だけでは足りない。

## 6. 選択肢を比較して最適候補を決める
|構成|向く場面|人の操作|追加費用を防ぐ条件|判定|
|---|---|---|---|---|
|AI Studio Playground → ChatGPT DR → Work/Codex|画面操作も含むAI技術動画を深く学ぶ|未接続状態では独自観察ノートの受渡しが必要|既存2契約のUI枠、API/agents/creditsへ切り替えない|品質優先の推奨候補|
|Gemini + app DR + 独自ノート + Google側実行役|Google AI Proだけで始める|URL入力から研究。実行役への連携は要確認|Googleログイン、許可済みの機能・上限内|1契約の基本候補|
|ChatGPT/Work + vidIQ Free|URLを一つの会話へ渡したい|初回に別アカウントの接続が必要|無料枠だけ。先に残高、呼出し件数、保存条件を確認|手間を減らす小規模候補|
|ChatGPT Plusだけ + 公開字幕を閲覧|話中心の動画、視覚情報が不要|字幕閲覧できればWork側で抽出|追加装備・APIなし。全文をファイルへ出さない|文字中心の基本候補|
|NotebookへYouTubeを直接追加|字幕資料を長く保持して比較する|URL追加で手軽|今回の保存方針を変更する明示許可が別途必要|現在の方針では不採用|
|Spark中心でGoogle内連携|継続・自動化を優先|地域・表示・接続・確認の実証が必要|Pro対象機能、追加creditなし|アカウント確認後の候補|
|OpenClaw等の対応ハーネス + Plus|URLキュー・状態・復旧を含む持続Loop|初期構築と認証許可が必要|公式対応の契約認証。検索/STT/embedding/外部API/host料金を別に確認|将来の設計候補|
|自作APIバッチ・Vertex・外部の有料自動化|細かい制御・大量処理|構築・課金管理が必要|既存契約枠として扱えない|今回の基本条件から除外|

vidIQはネイティブPlugin Directoryで「AVAILABLE、未導入」を再確認。字幕の取得と長編映像分析は別ツール[X01]。無料150credits/月[X02]の場合、25creditのVideo Watchだけなら最大6呼出しという算術になる。ただし追加で5creditの字幕取得も毎回行うなら最大5セット。他ツールや残高消費があればさらに減る。これは処理本数や全編成功を保証する実測ではない。
Glasp等の別会社の無料拡張も補助にできるが、既存契約で無料枠が増えるわけではない。全文保存、公開設定、保持条件が不明なら標準経路へ入れない。会議録音ツールを一般公開YouTube用と決めつけない。

## 7. ハーネスまで含めた自動化の判断
OpenAIの現行公式一覧[O18]には、利用枠対応の商用アプリ（Amp Code、Conductor、Dactyl、Devin、Hermes Agent、Hyperagent、Kilo Code、Notion、Vercel、Vorflux、Warp等）、coming soon、ログインのみのサービス、OSS（OpenClaw/OpenCode/Pi/T3）が別に載っている。
この一覧に載ることは、全機能無料・YouTube視覚入力・永続実行・今回の権限付与の証明ではない。[O17]はPlus枠の共有と外部サービスの料金を明確に分けている。

OpenClaw側の公式文書[X03]はChatGPT/Codex契約認証とPlatform APIを区別する。ブラウザ[X04]と永続scheduler[X05]はLoop候補になる。一方、ブラウザを操作できることから、AI Studioを確実に自動操作できる、全動画を読める、Quotaを超えて無償継続できるとは推測しない。
現状、研究室はWorkと既存GitHub接続で文書を保存できる。新しいハーネスをまず導入する必然性はない。持続キューと復旧を既存機能で満たせないことが実測された段階で追加する。特定harnessを無条件の最適解とはしない。

望ましい連携設計は、
URLキュー → 重複判定 → 許可された取得役 → 短い観察ノート → 公式照合 → 技能候補 → 静的な演習 → 非default GitHub保存 → readback → 完了記録。
これはDESIGN_ONLY。Work cloud browserからAI Studioへ操作して戻す経路、接続済みvidIQ経路、Spark経路のいずれも今回は起動していない。ログイン・新規接続・承認・地域・上限で止まることを成果物に記録し、人へ無意味な中継だけを要求しない。

## 8. 「勉強して役立てる」成果物
要約で終了せず、1動画につき必要な範囲で次を作る。
1. 相棒向け説明: 何ができる、今までと何が違う、どんな作業が楽になる、必要な費用・権限。
2. 主張台帳: 時刻、独自要約、映像／音声／字幕の別、公式URL・該当箇所・確認日、対象バージョン。
3. 知識: 正しい原理、適用条件、失敗例、古くなりやすい箇所、未解決点。
4. 技能候補: いつ使う、入力、手順、停止条件、検証、戻し方。Markdownを正本にし、各製品のSkillへ必要時変換する。
5. 演習: 本番・外部モデルを起動しないmockや小さな静的再現。未実行なら未実行と書く。
6. 活用提案: Loop、MCP、plugins、harness、記憶、評価、復旧のどこを改善するか。既存別repoへ実装せず研究室へ提案だけ置く。

ここでいうAIの学習は、参照できる知識・手順・評価結果を増やすこと。動画を読ませただけで基盤モデルが永久に再訓練されるという意味ではない。新しい会話でも同じ正本・指示を読める経路を作る必要がある。Skillsは道具の権限や起動器の代わりにならない。

## 9. 保存・費用の扱い
- 保存物はURL/ID/時刻/独自要約/検証/技能/receiptのみ。字幕全文、動画、秘密情報は保存しない。
- NotebookのYouTube直接追加は全文資料を作る[G17]。今回は独自ノートだけを追加する。
- ChatGPTの添付はLibraryにも保存される場合があり、チャット削除だけで消えない[O12]。ダウンロード→動画添付を基本経路にしない。
- AI StudioをProで使えることから、ゼロ保持・機密保護・全文を保存しない内部処理を保証しない[G24]。公開資料だけを入力し、字幕全文を返す指示・ファイル化を避ける。サービス内部の一時処理まで完全ゼロ保存が必要なら、その要件はUNKNOWNであり現時点で達成済みにしない。
- 上限に達したらリセットまで停止。APIキー、paid agents、Cloud Billing、購入credit、課金fallback、追加契約へ自動移行しない。
- Gemini CLIは個人GoogleログインのPro枠とAPI/Vertexを区別[G14]。Plusの契約枠を任意のAPIスクリプトへ流用できると推測しない[O01/O17]。
- Gemini app DR、native Antigravity、AI Studio内DR/Antigravity Previewは名前が似ても別の利用条件[G02]。

## 10. 必要な実証と合格条件
今回実施したのは一次資料照合と既存GitHub内容のreadback。ユーザーの対象動画はないため映像分析はNOT_RUN。別モデルのLIVE起動、装備接続、課金・権限設定、スケジュール起動もNOT_RUN。

後の承認済み実証では代表例を選ぶ:
A 話中心／B 無言の画面操作・小さい設定名／C 英語・自動字幕の誤り／D 長い章立て／E 字幕なし／F 削除・非公開・Quota失敗。
全種類を全製品で処理して利用枠を浪費しない。まず視覚情報が必要な1本で主要候補を比較し、差がある条件だけ追加検証する。

|項目|合格条件|
|---|---|
|対象の同一性|実際に取り込んだ動画ID、対象時刻、処理成功表示を確認|
|視覚取得|字幕にない画面上の事実を複数時刻で検証。字幕とタイトルだけの推測を排除|
|主張の追跡|重要主張に時刻と公式一次資料を付け、確かめられない箇所はUNKNOWN|
|技術の活用|静的演習が成立し、入力・手順・検証・停止条件を技能候補へ残す|
|保存|動画・字幕全文がrepo/Notebook等の研究成果物にない。提供者内部保持は別判定|
|費用|使用した認証・契約枠・追加credit無使用・残量を確認|
|人の手間|初回認証、介入回数、受渡し回数、待ち時間を記録|
|復旧|同じID重複を再処理せず、途中状態とterminal receiptを読み直して復旧|
|書込み|非default branch、通常commit、force=false、remote readback一致|
|自動連携|URL投入から結果保存までのreceiptが揃う。ブラウザUI上の成功だけでは合格にしない|

## 11. 相反する公式資料・更新への対処
- Spark: 専用help[G10]はPro＋広域対応、Google One一覧[G01]はUS-only/English-only。日本のアカウント実証までUNKNOWN。
- Chrome auto browse: PC helpはUS-only、一覧はUS/India。日本対象外という採用判断は一致。通常Gemini Chromeの日本語対応を代行操作と混ぜない。
- ChatGPT Skills: 料金表の一般的表示とworkspace Skill help[O09]の対象プランが一致しない場合、個人Plusへ保証しない。Codex側は別に確認する。
- 旧Agent: current overview[O13]は終了・Work移行だが、過去の利用回数・起動方法が本文に残る。旧40回等を現在のPlus枠として引用しない。
- Atlas/Sora/Pulse/Opal/Gems/custom GPTs: 終了・移行の個別資料を古い紹介動画より優先[O14/O15/O16/G12/G23]。
- Agentic video: API提供[G05]から、全アプリUIが同じ方式へ移行済みと推測しない。

## 12. 最小の次段階
相棒の追加操作を今すぐ要求する必要はない。調査資料と再調査プロンプトを先に完成させる。
実証開始時の最小入力は公開YouTube URLを1本。取得経路を確定し、必要な初回ログイン・接続だけをまとめる。権限や課金・別モデルLIVEの境界に到達する前まで資料・設計・静的確認は進める。
動画の内容を取得できなければ、理由を残して独立した公式資料研究を進める。ただしそれを「動画から学習完了」と呼ばない。

## 一次資料
- [O01 ChatGPT Plus overview](https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus)
- [O02 ChatGPT pricing](https://chatgpt.com/pricing/)
- [O03 Work and Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex)
- [O04 Deep Research](https://help.openai.com/en/articles/10500283-deep-research-in-chatgpt)
- [O05 Cloud browser](https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt)
- [O06 Scheduled tasks](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt)
- [O07 Codex with plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- [O08 Plugins](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt)
- [O09 Skills](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
- [O10 ChatGPT Live](https://help.openai.com/en/articles/20001274-gpt-live-faq)
- [O11 Study mode](https://help.openai.com/en/articles/11780217-using-study-mode-in-chatgpt)
- [O12 Library](https://help.openai.com/en/articles/20001052-using-library-to-manage-files-in-chatgpt)
- [O13 Agent transition](https://help.openai.com/en/articles/11752874-chatgpt-agent)
- [O14 Atlas retirement](https://help.openai.com/en/articles/20001371-chatgpt-atlas-retirement)
- [O15 Sora discontinuation](https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation)
- [O16 Release notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes)
- [O17 Plan in other apps](https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites)
- [O18 Partner directory](https://learn.chatgpt.com/docs/sign-in-with-chatgpt)
- [G01 Google AI Pro benefits](https://support.google.com/googleone/answer/14534406?hl=en)
- [G02 Google AI plans in AI Studio](https://ai.google.dev/gemini-api/docs/google-ai-plans)
- [G03 Video understanding in AI Studio](https://developers.googleblog.com/en/gemini-2-5-video-understanding/)
- [G04 Video understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- [G05 Agentic video announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-agentic-video-in-gemini/)
- [G06 YouTube in Gemini](https://support.google.com/gemini/answer/16622858?hl=en)
- [G07 Gemini file inputs](https://support.google.com/gemini/answer/14903178?hl=en)
- [G08 Gemini Chrome availability](https://support.google.com/gemini/answer/17140089?hl=ja)
- [G09 Chrome auto browse](https://support.google.com/chrome/answer/16821166?hl=ja)
- [G10 Gemini Spark](https://support.google.com/gemini/answer/17094507?hl=en)
- [G11 Spark schedules](https://support.google.com/gemini/answer/17094710?hl=en)
- [G12 Gems to skills](https://support.google.com/gemini/answer/18560919?hl=en)
- [G13 Gemini skills](https://support.google.com/gemini/answer/17094296?hl=en)
- [G14 Gemini CLI quotas](https://geminicli.com/docs/resources/quota-and-pricing/)
- [G15 CLI web_fetch](https://geminicli.com/docs/tools/web-fetch/)
- [G16 URL Context](https://ai.google.dev/gemini-api/docs/url-context)
- [G17 Notebook source imports](https://support.google.com/gemininotebook/answer/16215270?hl=en)
- [G18 Gemini learning tools](https://support.google.com/gemini/answer/16448384?hl=en)
- [G19 Ask YouTube](https://support.google.com/youtube/answer/14110396?hl=ja)
- [G20 Premium Lite benefit](https://support.google.com/googleone/answer/17101453?hl=ja)
- [G21 Flow / Whisk transition](https://blog.google/innovation-and-ai/models-and-research/google-labs/flow-updates-february-2026/)
- [G22 Flow / Flow Music](https://blog.google/innovation-and-ai/models-and-research/google-labs/flow-updates/)
- [G23 Opal FAQ](https://developers.google.com/opal/faq)
- [G24 Gemini API terms](https://ai.google.dev/gemini-api/terms)
- [X01 vidIQ MCP](https://support.vidiq.com/en/articles/15082430-vidiq-mcp)
- [X02 vidIQ credits](https://support.vidiq.com/en/articles/13928456-features-credits-by-plan)
- [X03 OpenClaw OpenAI provider](https://docs.openclaw.ai/providers/openai)
- [X04 OpenClaw browser](https://docs.openclaw.ai/tools/browser)
- [X05 OpenClaw automation](https://docs.openclaw.ai/automation/cron-jobs)
