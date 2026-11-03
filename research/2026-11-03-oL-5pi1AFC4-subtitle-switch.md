---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：thirdshiftはGitHub issueからレビュー済みPRまでをどう自動化するか"
description: "動画字幕を基に、thirdshiftがissueを起点にworktree作業、二重レビュー、CI監視と修復ループ、Spec分割、定期的な課題探索を経てPRを仕上げる流れを整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "thirdshift"
  - "自律型コーディングエージェント"
video_id: "oL-5pi1AFC4"
resource: "https://www.youtube.com/watch?v=oL-5pi1AFC4"
canonical_url: "https://www.youtube.com/watch?v=oL-5pi1AFC4"
published_at: "2026-10-20"
logical_id: "youtube:oL-5pi1AFC4:research"
transcript_logical_id: "youtube:oL-5pi1AFC4:transcript"
---

# 研究ノート：thirdshiftの仕組み（issueからレビュー済みPRまで）

## 独自要約

人間が目的・成功条件・対象外をissueに書いて実行すると、thirdshiftはissueを検証して着手の印を付け、専用worktreeで無人のエージェントに実装させる。その後、規約とissueの二系統のレビューを経てPRを開く。以降は決定論的なコードがベースのマージ、push、CI監視を行い、競合や失敗には修復セッションを回す。予算で反復は有限になる。大きな仕事はSpecとしてサブissueに分け、定期実行で自ら課題も探す。

## チャプター

- [開始: 作業をissueに書いて任せる](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=2s)
- [人間の役割: 変更内容・成功条件・対象外を書く](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=13s)
- [issueの検証・ラベル付け・worktree作成](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=29s)
- [無人セッションによる実装と二重レビュー](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=48s)
- [PR作成後の決定論的ループ（CI監視と修復）](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=74s)
- [結果: レビュー待ち、依頼時はマージ、失敗時はドラフト](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=98s)
- [Spec: サブissueを依存順・並列で実行](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=119s)
- [自律的な課題探索（定期実行）](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=139s)
- [まとめ](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=151s)

## 重要な知見

1. 仕様はissueに書く前提で、人間は成功条件と対象外を明示する役に回る。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=13s)
2. 着手時にissueが開いていて自分のcloneのものか確認し、ラベルで「claim」を表す。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=29s)
3. 専用ブランチのworktreeで作業するため、人間の作業ツリーは切り替わらない。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=34s)
4. 可能な場合はテスト先行で実装し、規約用とissue適合用の独立レビュアー2系統で確認する。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=48s)
5. PR作成を終点とせず、LLMではない自前の決定論的コードがマージ・push・CI監視を担う点が設計上の特徴。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=74s)
6. 競合やCI失敗は修復セッションで再試行し、予算で上限を設ける。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=84s)
7. 失敗時も作業はcommit・pushされ、PRはドラフト化されて再開できる。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=109s)
8. Specはサブissueを依存順に実行し、独立分は並列にする。各worktreeの成果はSpecブランチに集約される。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=124s)
9. 定期実行のPickup、Architect、Securityが対象課題を探し、同じRunへ渡す。[根拠](https://www.youtube.com/watch?v=oL-5pi1AFC4&t=142s)

## この研究室への応用

- 「LLM判断部分」と「決定論的な制御部分」を分ける設計は、字幕処理や研究ノート生成のパイプラインにも使える。
- worktree分離とclaimラベルは、複数ジョブの並行実行や二重着手の防止の参考になる。
- 独立した2観点のレビューは、研究ノートの検品（形式面と内容面）に転用できる。
- 失敗時に途中成果を残して再開可能にする方針は、ジョブ運用の復旧設計に有用。

## 限界・未確認

- 映像は未確認で、字幕テキストのみを根拠にしている。画面上の図や操作は把握していない。
- 公式資料やリポジトリとは未照合。実際の挙動、設定、予算の値、対応環境は UNKNOWN。
- 字幕の種別は取得情報上「manual」だが、正確性は UNVERIFIED で、誤変換の可能性が残る。固有名詞（Pickup、Architect等）の定義は動画内で説明がなく UNKNOWN。
- 外部仕様（GitHub APIやCI連携の詳細、ライセンス、提供形態）は UNKNOWN。
- 参照テンプレート research_note_prompt_template.md は作業ディレクトリに存在せず読めなかったため、指示文の形式に従って作成した。
