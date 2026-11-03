---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Claude CodeからCodexを呼び出す方法と使いどころ [V7tbia_t9yA]"
description: "Claude CodeからCodex CLIを呼び出す3つの動機（別AIでの確認・Claude Codeにできない作業・使用枠の分担）と、1行コマンドでの呼び出し実演、家計分析と画像生成の例を字幕から整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "Claude CodeとCodexの連携"
video_id: "V7tbia_t9yA"
logical_id: "youtube:V7tbia_t9yA:research"
transcript_logical_id: "youtube:V7tbia_t9yA:transcript"
resource: "https://www.youtube.com/watch?v=V7tbia_t9yA"
canonical_url: "https://www.youtube.com/watch?v=V7tbia_t9yA"
published_at: "2026-10-27"
---

# 研究ノート：Claude CodeからCodexを呼ぶ

## 独自要約（300字以内）

Claude Codeを主に使う話者が、Codexを併用する理由と手順を実演する動画。理由は、別モデルによる確認、Claude Codeにない機能やプラグインの利用、使用上限が近い時の作業分担の3つ。最も簡単な方法はClaude Codeにコマンドを実行させること。例として、家計分析をCodex側のプラグインで行い、結果を画像生成して返させた。

## チャプター

- [導入：Claude CodeからCodexを呼ぶ意味](https://www.youtube.com/watch?v=V7tbia_t9yA&t=0s)
- [呼び出す深い事情と調査した事例（3パターン）](https://www.youtube.com/watch?v=V7tbia_t9yA&t=71s)
- [理由2：Claude Codeにできないこと（画像生成・プラグイン）](https://www.youtube.com/watch?v=V7tbia_t9yA&t=117s)
- [理由3：使用枠・上限の分担](https://www.youtube.com/watch?v=V7tbia_t9yA&t=176s)
- [呼び出し方の種類（コマンド・MCP・プラグイン）](https://www.youtube.com/watch?v=V7tbia_t9yA&t=216s)
- [準備：両CLIのインストール](https://www.youtube.com/watch?v=V7tbia_t9yA&t=252s)
- [実演1：Codexにメリットを調査させる](https://www.youtube.com/watch?v=V7tbia_t9yA&t=321s)
- [実演2：家計分析と画像生成](https://www.youtube.com/watch?v=V7tbia_t9yA&t=391s)
- [スキル化とまとめ](https://www.youtube.com/watch?v=V7tbia_t9yA&t=501s)
- [雑談（飲み物の話・主題外）](https://www.youtube.com/watch?v=V7tbia_t9yA&t=587s)

## 重要な知見

1. 話者は国内外の事例を調べ、今年の記事だけで50件以上、大きく3パターンに分かれたと述べる（件数は話者の主張で未検証）。根拠：[t=71s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=71s)
2. パターン1は別のAIに確認させる使い方。Claude Codeで書き、レビューをCodexに任せる例が挙がる。根拠：[t=81s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=81s)
3. パターン2はClaude Codeにできないことの依頼。画像生成が主で、ブログ最後のサムネイルだけを依頼する例がある。根拠：[t=117s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=117s)
4. Codex側にだけあるプラグインがあり、話者は家計の財務分析に使うと述べる。根拠：[t=146s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=146s)
5. パターン3は使用枠の分担。上限が近い時に重い処理をCodexへ回す。話者は「節約」ではなく分担と表現。根拠：[t=176s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=176s)
6. 最も簡単な方法は、Claude Codeにターミナルでコマンドを打たせ、後続の指示をCodexへ渡すこと。他にMCPやプラグインもあると述べる。根拠：[t=216s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=216s)
7. 準備は両CLIをターミナルで使えるようにするだけ、と説明される。根拠：[t=265s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=265s)
8. 実演では、Codexに調べさせた結果として、セカンドオピニオン、会話の圧迫を防ぐこと、役割分担、並列実行が挙がった。根拠：[t=345s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=345s)
9. 家計分析では、プラグイン経由で直近6か月を分析し、続けて画像生成ツールで1枚にまとめた。数字は個人情報のためダミー化した。根拠：[t=459s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=459s)
10. 話者は、よく使う処理はスキル化すれば、画像作成の依頼で自動的にCodex呼び出しが起動すると述べる。根拠：[t=501s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=501s)
11. 話者の主張として、2026年10月時点でマネーフォワードMEはClaude Code側のプラグインに見当たらないとされる。根拠：[t=405s](https://www.youtube.com/watch?v=V7tbia_t9yA&t=405s)

## この研究室への応用

- 執筆や実装の成果物を別モデルにレビューさせる二重チェック工程を、研究ノート作成の検品に取り入れる案。
- 画像生成など主環境にない機能だけを外部CLIへ委譲する分業設計の参考にする。
- 使用上限が近い時の退避先を事前に用意し、手順をスキル化しておく運用案。
- 個人情報を含むデータを扱う際は、動画のようにダミー化してから公開する習慣を確認する。

## 限界・未確認

- 映像は未確認。字幕のみを根拠としており、画面上の操作や画像の中身は確認していない。
- 公式資料は未照合。インストール手順、各CLIの仕様、プラグインの有無や上限条件は UNKNOWN。
- 自動字幕のため誤変換の可能性が高い。特にコマンド名は「コデx」などと崩れており、正確なコマンド綴りとオプションは UNKNOWN。
- 「50件以上」「Codexの方が優秀だった時期」などは話者の主張で、裏付けなし。
- 動画後半の雑談部分は主題外のため、知見から除外した。
