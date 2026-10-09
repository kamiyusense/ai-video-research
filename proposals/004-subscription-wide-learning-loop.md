# 004 契約内の動画研究から再利用技能へ
状態: DESIGN_ONLY / runtime NOT_RUN。判断資料は research/2026-10-10-subscription-wide-youtube-learning.md。

## 推奨案
品質優先: AI Studio Playground → 公式一次資料のDeep Research → Work/Codex → 非default GitHub記録。
手間優先の比較候補: ネイティブvidIQ装備を取得役にする。別サービス無料枠、権限、保持条件、技術動画の精度を実測するまでは中核に固定しない。
持続処理は既存Workの利用可能な起動機構を先に検証し、不足した場合だけ公式契約認証に対応するハーネスを検討する。
初期資料は課金、LIVE、装備接続、イベント設定、外部model起動を実施しない。

## 状態
QUEUED → ACQUISITION_PREPARED → OBSERVED → VERIFIED_DOC → PRACTICE_PREPARED → RECORDED → READBACK → COMPLETE。
取得不能・認識不明は UNKNOWN。安全な公式資料研究は別に続けられるが、動画研究COMPLETEへは進めない。
時刻・動画ID・取得方法・主張・対象版・出典が揃わなければ「視聴済み」を作らない。

## 正本と重複
研究室GitHubのURLキュー、独自観察、主張台帳、技能候補、実証、receiptを正本にする。
同じvideo_id・claim・source_versionは統合する。要約だけで重複判定しない。
request/claim/result/receiptはappend-only、stateのみmutable。
correlation_id、generation、期限、expected_target_head、quota状態を記録。
terminal COMPLETE/FAILED/UNKNOWNを勝手に再起動しない。retry=0 / fallback=disabled。
Cloudの定期タスクがProjectの添付を読めるとは仮定せず、許可済みの接続とfresh readbackを使う。

## 最小の受渡し
動画URL/ID、処理方式、対象区間、独自の画面・発話の観察、時刻別主張、読めなかった箇所。
字幕全文・動画・アカウント秘密情報は渡さない／保存しない。
映像→検証→技能の受渡しは同じ形式にし、取得役を交換可能にする。

## 技能の成果物
適用場面、必要入力、手順、道具、停止条件、確認方法、復旧、対象バージョン、証拠。
まず持ち運べるMarkdownを用意し、確認済みの利用場所にだけSkillとして導入する。
習得判定は「要約できた」だけでなく、別の安全な例で手順を適用し、誤りと失敗条件を説明できること。
外部モデルを起動しない静的演習から開始する。

## 合格条件
対象動画IDと取得範囲、字幕にない画面情報の確認、公式照合、技能化、quota/auth区別、
全文保存なし、重複NO-OP、非default書込みとreadback、途中復旧を確認する。
最初は視覚情報の重要な1本で比較し、必要な条件だけ追加検証する。
「1 URLで全部自動」は起動から保存までのreceiptが揃った後にだけCONFIRMED_TESTとする。
