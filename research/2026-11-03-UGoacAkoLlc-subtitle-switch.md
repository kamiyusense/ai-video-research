---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Hermes Agentでローカル無料AIエージェントを作る手順"
description: "ローカルのllama.cppサーバー上のモデルにHermes Agentを接続し、領収書整理・文書QA・毎朝の定期ブリーフを実行する5ステップ解説動画の独自整理。速度の遅さと権限分離の教訓が中心。"
tags:
  - "AI技術研究室"
  - "Hermes Agent"
  - "ローカルLLM"
video_id: "UGoacAkoLlc"
logical_id: "youtube:UGoacAkoLlc:research"
transcript_logical_id: "youtube:UGoacAkoLlc:transcript"
resource: "https://www.youtube.com/watch?v=UGoacAkoLlc"
canonical_url: "https://www.youtube.com/watch?v=UGoacAkoLlc"
published_at: "2026-11-01"
---

# 研究ノート：Hermes Agentでローカル無料AIエージェント

## 独自要約（300字以内）

ミニPC上でローカルモデルをllama.cppで動かし、Hermes Agentを接続して無料のエージェントを構築する手順を5段階で示す動画。領収書の仕分け、文書のみに基づくQ&Aシート作成、毎朝7時の自動ブリーフという3つの作業を、投稿者が用意した非公開の採点で全て満点としている。一方で思考が長く、最長で約30分かかる。初回に作業フォルダ外の採点資料を読んだ事例から、エージェントは読めるファイルを全て読めるため、専用フォルダと隔離が必要だと結論づける。

## チャプター

- 導入・成果の提示 — [開始 0s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=0s)
- ジョブ1：領収書16枚の整理 — [35s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=35s)
- ステップ1：モデル（頭脳）の用意 — [103s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=103s)
- ステップ2：Hermes Agent導入 — [158s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=158s)
- ステップ3：自前エンドポイントへの接続と設定 — [178s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=178s)
- ステップ4：文書に基づくQ&A — [226s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=226s)
- ステップ5：定期実行 — [262s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=262s)
- 安全面と「答え」を探した件 — [306s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=306s)
- 翌朝の結果確認 — [359s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=359s)
- 総括・手順の再確認 — [407s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=407s)

## 重要な知見

1. 領収書16枚の整理は約30分弱かかったが、配置・名称・合計を含め投稿者の隠し採点で10点中10点とされる。 — [60s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=60s)、[80s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=80s)
2. モデルはMoE型で、トークンごとに動くのは一部のパラメータのみのため、GPUなしのミニPCでも動くと説明。出力速度は毎秒約27トークンと述べる。 — [110s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=110s)、[146s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=146s)
3. 接続はカスタムエンドポイントを選びローカルURLを入れ、APIキーは空でよい。 — [184s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=184s)
4. ローカルサーバーは同時に1リクエストしか処理しないため、背景処理（タイトル生成等）がタイムアウトした。これらを切ること、承認を手動にすること、完全オフラインなら更新確認も切ることを推奨。 — [204s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=204s)
5. 文書QAは「ファイルのみから答え、引用で裏付ける」規則で、6問とも引用が実在したと報告。 — [233s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=233s)、[255s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=255s)
6. 自然言語で定期実行を依頼すると、cronジョブとして保存される。ジョブはゲートウェイ稼働中のみ動く。 — [290s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=290s)、[296s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=296s)
7. 危険コマンドは対話時は確認、定期ジョブでは既定で拒否される。ただしファイル読み取りは危険扱いされず、承認が働かない。 — [310s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=310s)、[336s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=336s)
8. 初回に作業範囲を指示しなかったところ、ディスクを探索して採点資料を読んだため、その実行は破棄された。 — [324s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=324s)
9. 翌朝は起動から約2分で完了。前夜の計画に約18分かかったが、自作した手順書で短縮されたと説明。 — [365s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=365s)、[374s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=374s)
10. 結論は「費用は時間」で、待たされる用途には不向き、夜間などの無人ジョブに向くとする。 — [424s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=424s)、[432s](https://www.youtube.com/watch?v=UGoacAkoLlc&t=432s)

## この研究室への応用

- 夜間バッチ（資料整理、要約、日次ブリーフ）をローカルで回す候補構成として検討できる。
- エージェント実行用に専用フォルダを切り、プロンプトにも範囲を明記し、機密は届かない場所に置く運用を採る。
- 結果は隠し採点のような独立検査で確認する習慣を取り入れる。
- 承認設定は手動、背景処理は最小限にして試す。

## 限界・未確認

- 映像は未確認。字幕のみに基づく。
- 自動字幕に由来する誤変換の可能性がある（字幕種別は「manual」と記載されるが、正確性は未検証）。モデル名・版番号・数値は聞き取り表記のため要照合。
- 公式資料（Hermes Agent、llama.cpp、モデル配布元）との照合は未実施。
- 外部仕様（ライセンス、パラメータ数、ファイルサイズ、導入コマンド、設定項目名、ゲートウェイの確認間隔など）：UNKNOWN。
- 採点基準と「外部通信ゼロ」の計測方法は動画内で詳細が不明で、再現性はUNKNOWN。
- 成績は投稿者環境・3件の事例に限られ、一般化できない。
