---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Claude Codeの新機能3つ（ultrathink・書き込み制限・idle compaction）"
description: "Claude Codeの週次更新動画の研究ノート。ultrathinkによる単発の深い思考、作業フォルダ外への書き込み禁止設定、長い放置会話の自動要約(idle compaction)を整理する。"
tags:
  - "AI技術研究室"
  - "Claude Code"
  - "動画研究"
video_id: "Q0zTJCgSlrY"
logical_id: "youtube:Q0zTJCgSlrY:research"
transcript_logical_id: "youtube:Q0zTJCgSlrY:transcript"
resource: "https://www.youtube.com/watch?v=Q0zTJCgSlrY"
canonical_url: "https://www.youtube.com/watch?v=Q0zTJCgSlrY"
published_at: "2026-11-01"
---

# 研究ノート：Claude Codeの新機能3つ

## 独自要約
今週のClaude Codeには3点の追加があると説明する動画。(1) 質問に特定キーワードを入れると、その回だけ深く考えさせられる。(2) 作業フォルダ外への書き込みを設定で一律に拒否できる。(3) VS CodeとDesktopで、長く放置した大きな会話が自動要約され、キャッシュ切れ後の再開コストを抑える。いずれも字幕のみが根拠である。

## チャプター
- 導入・今週は3点: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=3s
- 1つ目 ultrathink: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=8s
- 作業中に使った場合と表示条件: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=32s
- 無効化の環境変数: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=59s
- 2つ目 書き込み禁止設定: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=69s
- 3つ目 idle compaction: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=106s
- 次回予告: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=145s

## 重要な知見
1. ultrathinkを質問に含めると、その1回の応答だけ深く考える。思考の深さはxhighに相当し、トークン消費も増えると述べられる。根拠: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=11s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=19s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=29s
2. 作業中に書いた場合は、そのやり取りが終わるまで深い思考モードになる。根拠: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=32s
3. キーワードとして認識される位置だけ虹色表示になり、引用符内やパス途中では表示されない。VS Code拡張でもチャット欄で同様。根拠: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=41s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=48s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=52s
4. 環境変数 CLAUDE_CODE_DISABLE_ULTRATHINK でキーワード機能を切れる。根拠: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=59s
5. 外部の読み取り禁止は従来からあり、今回は書き込み禁止が加わった。設定名は permissions.blockWritesOutsideWorkingDirectories。根拠: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=74s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=84s
6. 有効時はWrite・Edit・NotebookEditが対象で、どの許可モードでも外部への書き込みは拒否される。根拠: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=91s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=98s
7. idle compactionはVS CodeとClaude Desktopのコードタブ向け。20万トークン超の会話を放置すると要約され、プロンプトキャッシュ切れ時の次回送信で使われる。根拠: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=111s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=117s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=124s
8. ターミナルには同種の仕組みが以前からあり、約54分の放置で1時間キャッシュ切れ前に圧縮される。根拠: https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=131s / https://www.youtube.com/watch?v=Q0zTJCgSlrY&t=135s

## この研究室への応用
- 難しい設計判断や調査の質問だけ、キーワードで一時的に深い思考へ切り替える運用を試せる。コスト増と引き換えである点を記録する。
- 調査用リポジトリでは、書き込み禁止設定を有効にして、vault外のファイルを誤って変更しない安全策にできる。
- 長時間の研究セッションを放置する場合、要約によって細部が落ちる可能性を踏まえ、重要事項はノートに残す。

## 限界・未確認
- 映像は未確認。字幕テキストのみを根拠とした。
- 公式資料（ドキュメント・変更履歴）は未照合。機能の提供バージョン・対象プラン・正確な挙動はUNKNOWN。
- 字幕は取得上manualとされるが、設定名・数値・固有名詞の誤変換の可能性が残る（transcript_statusはUNVERIFIED）。
- xhighの具体的な仕様、トークン増加量、設定ファイルの記述場所はUNKNOWN。
- 「約54分」「20万トークン」等の数値は動画内の発言であり、検証していない。
