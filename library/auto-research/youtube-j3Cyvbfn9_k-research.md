---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "【研究ノート】【検証】AIを選ぶならどれ？ChatGPT・Claude・Gemini｜ゲーム制作・画像生成・料金比較 [j3Cyvbfn9_k]"
description: "ChatGPT、Claude、Geminiの主要AIモデルを、3Dブロックゲーム制作、レイトレーシングによる料金計算、画像生成で比較検証した動画。コーディングや総合性能ではClaude（Opus 5.5 / Sonnet 5.5）が優勢、料金面ではGemini 3.8 Flashが最安。画像生成はChatGPTが優れる。個人利用ではGoogleサービス連携やコスパからGeminiが推奨されている。"
resource: "https://www.youtube.com/watch?v=j3Cyvbfn9_k"
tags:
  - "AI技術研究室"
  - "動画研究"
logical_id: "youtube:j3Cyvbfn9_k:research"
record_id: "youtube:j3Cyvbfn9_k"
video_id: "j3Cyvbfn9_k"
published_date: "2026-10-12"
published_at: "2026-10-12T12:30:36+09:00"
channel: "キノコード / AI・プログラミング学習チャンネル"
duration_seconds: "1021"
created_at: "2026-10-21"
created_by: "Antigravity CLI (Gemini)"
source_transcript: "youtube:j3Cyvbfn9_k:transcript"
source_transcript_sha256: "e5ac47394b3effbd34e5d8d8347f5cb57da948ee7c2ed584892feefeb1b44d66"
time_source: "NONE"
related_records:
  - target_id: "youtube:j3Cyvbfn9_k:transcript"
    relation: "DERIVED_FROM"
    note: "本ノートの元になった字幕原文"
---

# 【研究ノート】【検証】AIを選ぶならどれ？ChatGPT・Claude・Gemini｜ゲーム制作・画像生成・料金比較 [j3Cyvbfn9_k]

本ノートは字幕原文 [[youtube-j3Cyvbfn9_k-transcript]] を元にした二次分析です。

## 独自要約
OpenAI、Anthropic、Googleの3大AIについて、3Dブロックゲーム制作・レイトレーシング（料金検証）・画像生成の3つの課題で実力を比較検証。ゲーム制作ではOpus 5.5とGPT 6 ASTRAが指示以上の工夫を見せた一方、Gemini 3.1 Proは失敗（Flashは成功）。ベンチマークではSonnet 5.5とOpus 5.5が上位を占めた。普段使いモデルの料金概算ではGemini 3.8 Flashが最安。画像生成はChatGPTが最も高品質。月額約3000円の有料プランでは、5TBストレージやGoogle連携、エージェント機能から個人利用にはGeminiが推奨されている。

## 内容の流れ
1. 導入と検証目的（ChatGPT、Claude、Geminiの比較）および各社最上位モデルの確認
2. 検証1：3Dブロックゲーム制作（前世代との比較と最新モデルでの挙動確認）
3. 第3者機関（Artificial Analysis）によるコーディング・総合性能ランキングの比較
4. 検証2：レイトレーシング実装による普段使いモデルのAPI料金・描画比較
5. 検証3：同一指示による画像生成精度の比較（ChatGPT vs Gemini）
6. 有料プラン（月額約3000円前後）の比較と個人利用におけるGeminiの推奨理由
7. 会社・組織におけるAI導入の課題とまとめ

## 重要な知見
- 3Dブロックゲーム制作において、Opus 5.5やGPT 6 ASTRAはプロンプトの指示を超えて自律的にブロック種類や座標表示などを追加・工夫する進化が見られた。「吉 に 調整 が できる」
- 最上位モデルのGemini 3.1 Proはゲーム生成に失敗した一方、速度重視のGemini 3.8 Flashはブロック配置やジャンプができるゲームを完成させた。「空 しか あり ませ ん」
- 第3者機関（Artificial Analysis）のコーディングテストではSonnet 5.5が最高スコアを記録し、上位をAnthropicモデルが占めた。「ソネッ 5.5 は 64% で」
- 普段使いモデルによるレイトレーシング実装の料金試算では、Gemini 3.8 Flashが最も低コストであった。「ジェミニ が 最も 安く」
- 画像生成検証ではClaude単体では生成不可であり、ChatGPTとGeminiのうち油彩タッチや水たまりの表現力でChatGPTが高く評価された。「チャット GPT の 方 が うまく」
- 月額3000円前後の有料プランにおいて、個人利用では5TBストレージやGoogleサービス連携、エージェント機能の充実度からGeminiが推奨された。「迷っ たら まず ジェミニ です」

## この研究室への応用
1. モデル特性に応じた使い分け方針の策定: コーディング・論理構築にはSonnet 5.5/Opus 5.5、コスト・速度重視の一次処理にはGemini 3.8 Flash、画像素材生成にはChatGPTといった役割分担の設計に活用できる。
2. 動画・マルチメディア制作ツールの選定基準: Google AI Pro（Gemini）における大容量ストレージ（5TB）や動画・音声生成、エージェント（Antigravity）の総合環境を研究室の制作基盤の選択肢として検討できる。
3. APIコスト評価モデルの参考: 入出力トークン量と単価に基づく実装タスクごとのコスト概算手法を、研究室での自動化スクリプトやツール運用の費用予測モデルに応用できる。

## 限界・未確認
- 字幕にタイムスタンプ（時刻情報）が含まれていないため、動画内の正確な経過時間や各シーンの頭出し確認ができない。
- YouTubeの自動生成字幕を取り込んでいるため、固有名詞の誤変換（「faブル」「JI」「Oパス」「エフォート は 貝」「油菜」など）が含まれている可能性がある。
- 字幕テキストのみを元にした分析であり、実際の動画内のデモ映像、生成された3Dゲームの動作画面、レイトレーシング描画結果、生成画像などの視覚情報は直接確認できていない。
