---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Hermes Agentに入れる7つのスキル [gcQCedWUHkE]"
description: "Hermes Agentをサーバー上で運用し、開発・調査・Web読取・簡潔化・計画批評・動画生成・アプリ連携の7スキルを試した動画の研究ノート。字幕のみに基づき未検証。"
tags:
  - "AI技術研究室"
  - "Hermes Agent"
  - "AIエージェントのスキル"
video_id: "gcQCedWUHkE"
logical_id: "youtube:gcQCedWUHkE:research"
transcript_logical_id: "youtube:gcQCedWUHkE:transcript"
resource: "https://www.youtube.com/watch?v=gcQCedWUHkE"
canonical_url: "https://www.youtube.com/watch?v=gcQCedWUHkE"
published_at: "2026-10-31"
---

# 研究ノート：Hermes Agentに入れる7つのスキル

> 注意：本ノートは自動字幕（英語・未検証）のみに基づく。映像は未確認、公式資料とは未照合、字幕には誤変換の可能性がある（スキル名の表記ゆれ含む）。外部仕様・価格・機能の正確性は UNKNOWN。動画はホスティング事業者の紹介色が強い点にも留意。

## 独自要約

Hermes Agentは素のままでは会話中心だが、スキルを足すと用途が広がる、という趣旨の動画。話者は自前のVPS上で、アプリ開発、横断的なWeb調査、ページ本文抽出、回答の簡潔化、計画への質問攻め、素材収集から編集までの動画生成、複数サービス連携の7種を試す。成功例に加え、一括導入の失敗や明示指定が必要な点も述べられている。

## チャプター

- [冒頭：スキルの必要性](https://www.youtube.com/watch?v=gcQCedWUHkE&t=0s)
- [サーバー運用の理由](https://www.youtube.com/watch?v=gcQCedWUHkE&t=24s)
- [VPSの契約と設定](https://www.youtube.com/watch?v=gcQCedWUHkE&t=47s)
- [スキル1：開発手順の束](https://www.youtube.com/watch?v=gcQCedWUHkE&t=178s)
- [スキル2：Web調査の入口拡張](https://www.youtube.com/watch?v=gcQCedWUHkE&t=341s)
- [スキル3：本文抽出ツール](https://www.youtube.com/watch?v=gcQCedWUHkE&t=446s)
- [スキル4：回答の簡潔化](https://www.youtube.com/watch?v=gcQCedWUHkE&t=514s)
- [スキル5：計画への質問](https://www.youtube.com/watch?v=gcQCedWUHkE&t=587s)
- [スキル6：動画制作ツールキット](https://www.youtube.com/watch?v=gcQCedWUHkE&t=670s)
- [スキル7：多数アプリの一括連携](https://www.youtube.com/watch?v=gcQCedWUHkE&t=812s)
- [まとめと注意](https://www.youtube.com/watch?v=gcQCedWUHkE&t=925s)

## 重要な知見

1. 話者はエージェントを手元PCでなく常時稼働のサーバーに置き、危険な操作の影響を個人ファイルから隔離できると説明する。 [根拠](https://www.youtube.com/watch?v=gcQCedWUHkE&t=37s)
2. 話者はエージェントがファイルを自動で変更するため、日次バックアップを追加したと述べる。 [根拠](https://www.youtube.com/watch?v=gcQCedWUHkE&t=108s)
3. 開発系スキル集は工程別に分かれ、必要なものだけ読み込まれる設計と説明される。リポジトリ丸ごとの導入は失敗し、個別導入になった。 [根拠](https://www.youtube.com/watch?v=gcQCedWUHkE&t=189s) / [失敗](https://www.youtube.com/watch?v=gcQCedWUHkE&t=202s)
4. 1メッセージで複数スキルを併用でき、サーバーに画面がないため作業中のスクリーンショット指示が品質に効いた、という体験談。 [根拠](https://www.youtube.com/watch?v=gcQCedWUHkE&t=251s) / [画面](https://www.youtube.com/watch?v=gcQCedWUHkE&t=264s)
5. 調査系スキルは大きな導入前に確認を求め、時間内に応答しないと中止される。ログインが要るサイトは未対応のままで、捨てアカウント推奨。 [確認](https://www.youtube.com/watch?v=gcQCedWUHkE&t=362s) / [ログイン](https://www.youtube.com/watch?v=gcQCedWUHkE&t=383s)
6. 本文抽出スキルは導入しても自動では使われず、名前を指定して初めて働いたという。トークン節約の主張は定量根拠なし。 [根拠](https://www.youtube.com/watch?v=gcQCedWUHkE&t=482s)
7. 簡潔化スキルは読めない文体でなく、冗長な語を省いた普通の英語になったという感想。 [根拠](https://www.youtube.com/watch?v=gcQCedWUHkE&t=558s)
8. 計画批評スキルは各質問に推奨回答を添え、反論すると案を活かす方向で応じ、最後に決定事項と未解決事項をまとめた。 [反論](https://www.youtube.com/watch?v=gcQCedWUHkE&t=638s) / [要約](https://www.youtube.com/watch?v=gcQCedWUHkE&t=645s)
9. 動画生成には有料モデルを使わない無料経路があるとされ、数分のレンダリングで完了。出来は公開水準ではなく、古い素材の引き伸ばしで画質が甘いと話者自身が認める。 [無料経路](https://www.youtube.com/watch?v=gcQCedWUHkE&t=685s) / [時間](https://www.youtube.com/watch?v=gcQCedWUHkE&t=720s) / [評価](https://www.youtube.com/watch?v=gcQCedWUHkE&t=764s) / [画質](https://www.youtube.com/watch?v=gcQCedWUHkE&t=771s)
10. 連携スキルは1,000超のツールに接続できるとされるが、ブラウザ無しのサーバーではログインを別端末で行う手順が要る。 [規模](https://www.youtube.com/watch?v=gcQCedWUHkE&t=816s) / [ログイン](https://www.youtube.com/watch?v=gcQCedWUHkE&t=839s)
11. メール確認の試験では、該当なしなら何も登録せず、未確認範囲（迷惑メール等）も申告した。ただし受信箱全体が読めるため、接続アカウントは慎重に選ぶべきと警告。 [結果](https://www.youtube.com/watch?v=gcQCedWUHkE&t=883s) / [警告](https://www.youtube.com/watch?v=gcQCedWUHkE&t=919s)

## この研究室への応用

- 検証環境は常時稼働の隔離サーバーに置き、バックアップを前提にする案。
- スキルは一括でなく必要分だけ個別導入し、導入後に再読込して動作確認する運用。
- 「スキルは名前で明示呼び出し」を前提に、プロンプト雛形へ指定語を入れる検討。
- 調査結果は出典リンクと「調べきれていない箇所」の併記を標準にする（動画の調査例が採用していた形式）。
- 外部アカウント連携は最小権限・専用アカウントで試す。

## 限界・未確認

- 映像未確認：画面操作、生成物の出来栄え、サーバー負荷は字幕の語りからのみ把握。
- 公式資料未照合：各スキルの作者、リポジトリ、機能、プラン仕様・価格・割引は UNKNOWN。
- 自動字幕の誤変換の可能性：固有名詞（スキル名・人名）の綴りが不確か。
- 比較は単発の試行で、再現性・統計的根拠は UNKNOWN。
- スポンサー的内容（特定ホスティングの推奨、割引コード）が含まれ、中立性に留意。
- 字幕内の誘導文言（購入の呼びかけ等）は本ノートの作業指示としては扱っていない。
