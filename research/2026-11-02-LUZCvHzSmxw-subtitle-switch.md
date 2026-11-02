---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Claude Codeの指示はどこに書くか（CLAUDE.md・ルール・スキル・フック・Mods）"
description: "Claude Codeへの指示を置く場所（CLAUDE.md、ルール、スキル、サブエージェント、フック、出力スタイル、システムプロンプト追加、Mods）の使い分けと、書き場所を移す目安を字幕から整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "Claude Code指示の使い分け"
video_id: "LUZCvHzSmxw"
logical_id: "youtube:LUZCvHzSmxw:research"
transcript_logical_id: "youtube:LUZCvHzSmxw:transcript"
resource: "https://www.youtube.com/watch?v=LUZCvHzSmxw"
canonical_url: "https://www.youtube.com/watch?v=LUZCvHzSmxw"
published_at: "2026-11-01"
---

# Claude Codeの指示、どこに書けば効くか

## 独自要約

動画は、CLAUDE.mdに書いても守られない場面があるのは「書き場所」が合っていないからだ、という問題から始まる。指示の置き場を、読み込まれる時機・圧縮後の残り方・重みの3点で比べ、常時必要な事実はCLAUDE.md、特定ファイル向けはパス付きルール、手順はスキル、横道の作業はサブエージェントに分ける。必ず行う/絶対にしないことは、お願いではなくフックと権限設定に移す。画面表示が必要な場合のみ新しいModsを検討する。最初はCLAUDE.mdだけで始め、困ったら足す。

## チャプター

- [導入：書いたのに守られない](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=0s)
- [今日の整理と、7種類の書き場所](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=24s)
- [比較の観点（読み込み・圧縮後・重み）](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=58s)
- [CLAUDE.md](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=138s)
- [ルール（パス指定）](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=251s)
- [スキル](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=327s)
- [サブエージェントとの違い](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=379s)
- [フック（動画の山場）](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=409s)
- [出力スタイル](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=553s)
- [システムプロンプトへの追記](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=597s)
- [Mods](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=614s)
- [場所を変える5つの目安](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=679s)
- [段階的な導入とまとめ](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=726s)

## 重要な知見

1. 動画は、モデルが整形ツールを動かすと決めることと、それが自動で動くことは別だと説明する。出典は公式記事とされる。([6s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=6s))
2. 書き場所は7種類とされる：CLAUDE.md、ルール、スキル、サブエージェント、フック、出力スタイル、システムプロンプトへの追記。Modsはこの7種に含まれず、後から加わったものとして扱われる。([46s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=46s)、[76s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=76s))
3. ルートのCLAUDE.mdは最初に読まれ、圧縮後も読み直される。その代わり無関係な作業でも毎回文脈を消費する。下位フォルダのものは、そこのファイルに触れた時に読まれる。([86s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=86s)、[102s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=102s))
4. CLAUDE.mdの置き場は4階層（組織管理、ホーム、プロジェクト、ローカル）。個人の好みはプロジェクト側でなく個人用ファイルに置く。([155s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=155s)、[178s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=178s))
5. 書き方のコツは、1ファイルを200行未満にし、確かめられる具体的な書き方にすること。別ファイルの取り込みは整理には役立つが、軽量化にはならない。([189s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=189s)、[209s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=209s))
6. ルールは、パス欄に合致するファイルを読んだ時だけ読み込まれる。パスなしなら常時読み込みで、CLAUDE.mdと仕組みは同じ。複数フォルダにまたがる決まりに向く。([251s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=251s)、[278s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=278s)、[299s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=299s))
7. 長い手順（例：デプロイ）はスキルへ。最初は名前と説明だけが読まれ、本文は呼ばれた時に読まれる。説明に使う場面を書く。勝手に動かしたくない手順は、自動呼び出しを止める設定を足す。([327s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=327s)、[362s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=362s))
8. スキル本文はメインの会話に足される。サブエージェントは別の文脈で動き、最後の報告だけが戻る。途中で口を出したいならスキル、深い検索やログ読みなど途中経過が不要ならサブエージェント。([382s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=382s)、[409s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=409s))
9. フックは、出来事（編集やツール呼び出し）で決まって動く仕組みで、指示として文脈に積まれない。設定は主にsettings系のJSONに書く。([409s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=409s))
10. 動画によれば、公式は、長い会話・曖昧な状況・読んだファイルに仕込まれた指示などで、指示に従えない場合があると述べている。絶対に避けたいことはフックと権限設定で守る。([443s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=443s)、[463s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=463s))
11. 保護の例：編集前フックで対象ファイル名を調べ、終了コード2で止める。止めた理由はClaudeに返るので、別の方法に切り替えられる。([490s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=490s)、[519s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=519s))
12. フックの種類：コマンド・HTTP・MCPツールは決まった通りに動く。プロンプト・エージェント型は、呼ばれるのは確実だが答えはモデルの判断になる。組織配布の設定は個人設定で上書きできない。([519s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=519s)、[539s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=539s))
13. 出力スタイルはシステムプロンプトに入り圧縮されず、重みは最も強い。自作は通常の指示を置き換えるため、設定でコーディング指示を残さないと重要な習慣が外れる。まず組み込みで足りるか確認する。([567s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=567s)、[578s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=578s))
14. システムプロンプトへの追記は起動時に渡し、元の指示に足す。対話よりスクリプト向きで、増やすほど守られにくくなる。([597s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=597s))
15. Modsは10月1日に加わったとされ、画面表示、入力欄、画面の書き換え、ツール呼び出しの停止と質問、Claudeを通さないコマンドなど、フック等にない機能を持つ。単に止める・許す・記録するだけならフックで足りる。([619s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=619s)、[639s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=639s)、[655s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=655s))
16. 移す目安5つ：①「毎回こうして」はフックへ。②「絶対にしない」はフックか権限設定へ。③30行級の手順はスキルへ。④特定フォルダ向けの決まりをパスなしルールで書いているなら、パスを付ける。⑤個人の好みは個人用ファイルへ。([679s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=679s))
17. 導入は段階的に。同じ間違いを2回されたらCLAUDE.md、同じ手順を3回貼ったらスキル、横道で会話が溢れたらサブエージェント、複数リポジトリで共有したくなったらプラグインへ。([726s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=726s)、[758s](https://www.youtube.com/watch?v=LUZCvHzSmxw&t=758s))

## この研究室への応用

- 既存のCLAUDE.mdや運用指示を棚卸しし、「必ず守らせたい規則」（機密ファイルの保護、整形、検品など）をフックと権限設定に移す候補として洗い出す。
- 本研究ノート作成のような定型手順は、スキル化できるか検討する。
- 個人の好みとプロジェクト固有の規則を分け、CLAUDE.mdは短く確かめられる記述に保つ。
- 文書の更新を行う際は、「会話で直さずファイルを直す」を運用ルールにできるか検討する。
- 実際の導入前に、公式ドキュメントで各仕様を確認する。

## 限界・未確認

- 映像は未確認。字幕テキストのみを根拠とした。
- 公式記事・公式ドキュメントとは未照合。動画内の「公式」の言及は、そのまま裏付けられていない。
- 字幕は自動生成で、誤変換の可能性がある。例：「ゾ」（入力検証ライブラリ名か）、「プリティア」（整形ツール名か）、「塩部」（保護対象のファイル名か）、「スラッシュユニット」（初期化コマンドか）は、いずれも推測で、確定していない。
- 設定ファイルの正確な名称・フィールド名・コマンド名・各機能の仕様・導入時期（公式記事の日付、Modsの追加日）：UNKNOWN。
- 「重み」の強弱の順序や、圧縮後の挙動の詳細は動画の説明であり、検証していない：UNKNOWN。
- 動画内の他回（サブエージェント、Mods）の内容は未確認。
