---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "会議終了を起点にGemini Notebook追加と議事録再生成を自動化する手順の研究ノート [zY45n9fPmMM]"
description: "Workspace StudioでMeetの自動メモ出力を開始条件にし、Notebookへのソース追加、社内書式の議事録再生成、ドキュメント追記までを4ステップで組む手順と、応用・制約を整理した研究ノート。"
tags:
  - "AI技術研究室"
  - "Workspace Studio"
  - "Gemini Notebook"
  - "会議自動化"
video_id: "zY45n9fPmMM"
logical_id: "youtube:zY45n9fPmMM:research"
transcript_logical_id: "youtube:zY45n9fPmMM:transcript"
resource: "https://www.youtube.com/watch?v=zY45n9fPmMM"
canonical_url: "https://www.youtube.com/watch?v=zY45n9fPmMM"
published_at: "2026-10-25"
---

# 研究ノート：会議後のNotebook追加と議事録生成の自動化

## 独自要約

会議メモをNotebookへ手動で追加し続けるのは続かない、という課題から出発する。Workspace Studioで、Meetの自動メモ出力を開始条件にし、メモのリンクをNotebookのソースへ入れ、Geminiに社内書式の議事録を作らせ、元ドキュメントの新規タブへ追記する4ステップを示す。応用として、テンプレート添付による書式固定のドキュメント・スライド生成、課題管理表への行追加、条件分岐が紹介される。まず小さく始めて広げる方針である。

## チャプター

- 導入と今回の狙い：[開始 0秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=0s)
- 3部作の2作目という位置づけ、書籍の告知：[開始 33秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=33s)
- 前回の振り返り（会議メモは情報資産）：[開始 104秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=104s)
- 利用条件の注意（有償版が前提）：[開始 173秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=173s)
- 手動追加の手順と自動化したい2点：[開始 194秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=194s)
- Workspace Studioの概要：[開始 313秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=313s)
- テスト実行のデモ（4ステップの結果確認）：[開始 394秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=394s)
- ステップ1・2：開始条件とソース追加：[開始 598秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=598s)
- ステップ3：Geminiで議事録を再生成：[開始 837秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=837s)
- ステップ4：ドキュメントに新規タブで追記：[開始 1081秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1081s)
- 本番稼働（オン）と他者へのコピー配布：[開始 1219秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1219s)
- 応用編の導入：[開始 1359秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1359s)
- テンプレートでドキュメントを直接生成：[開始 1521秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1521s)
- スライドの直接生成：[開始 1646秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1646s)
- 課題管理表への行追加（繰り返し処理）：[開始 1773秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1773s)
- まず基本から始める勧め：[開始 2032秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=2032s)
- 作成数の上限と条件分岐：[開始 2119秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=2119s)
- 次回予告（Notebookの外部共有）：[開始 2317秒](https://www.youtube.com/watch?v=zY45n9fPmMM&t=2317s)

## 重要な知見

1. 開始条件にMeetの自動メモ出力が選べるようになり、会議終了を起点に動かせる。全会議にも特定の会議にも絞れる。根拠：[611秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=609s)、[639秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=634s)
2. ソース追加では、ドライブ指定だと固定ファイルしか選べず詰まりやすい。「WebまたはYouTubeリンク」を選び、ステップ1のメモのリンクを変数で渡す。根拠：[735秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=735s)、[755秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=750s)
3. ソース追加だけなら短時間で組めるとされる。根拠：[827秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=827s)
4. 議事録の再生成は、Geminiアプリと同じく「ファイル添付＋プロンプト」を、変数でステップ1のリンクを渡す形で再現する。プロンプトはGeminiに作らせる案も出る。根拠：[966秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=962s)、[938秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=934s)
5. 注意点として、ウェブ検索は議事録用途では外す。一方、ワークスペース内データ参照のチェックを外すとリンク先も読めなくなるため、Meetメモを読ませたいなら残す。根拠：[1014秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1011s)、[1031秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1027s)
6. ドキュメント追記は「作成」と「追加」の2択がある。追加では元ドキュメントに新しいタブを足し、ステップ3の出力を中身にできる。根拠：[1084秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1084s)、[1138秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1134s)
7. 稼働にはテスト実行とは別に「オン」にする操作が要る。共有リンクは社内限定で、受け取った人が自分の環境へコピーし、条件を直して使う。根拠：[1219秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1219s)、[1251秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1244s)
8. 書式の固定は、Markdown再出力より、空のテンプレートを添付して中身だけ差し替えさせる方が良いと話者は述べる。ドキュメントとスライドは直接生成できるが、シートは直接生成の対象外と述べられる。根拠：[1526秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1526s)、[1548秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1548s)、[1624秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1624s)
9. 生成前にNotebookへ構成を作らせ、その結果を次の生成ステップに渡して精度を上げる。根拠：[1737秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1737s)、[1746秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1746s)
10. 課題管理表は、課題の抽出→整理→列ごとの分割→行追加を、課題数分の繰り返しで回す。根拠：[1880秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1880s)、[1946秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=1946s)
11. 1アカウントのフロー上限は25個と話者は述べる。回避として、条件分岐で顧客ごとに投入先ノートブックを変える案がある。根拠：[2141秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=2141s)、[2202秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=2202s)
12. 利用にはGoogle Workspaceと有償版Geminiが必要とされる。根拠：[173秒付近](https://www.youtube.com/watch?v=zY45n9fPmMM&t=173s)

## この研究室への応用

- 動画・資料の研究ノートを溜めるNotebookがあるなら、「新規ファイル作成を起点にソース追加」の型は流用を検討できる。ただし開始条件の種類は本動画ではMeet以外の詳細が不明。
- 変数でステップ間のリンクを渡す設計は、他の自動化でも基本形になりうる。
- 書式を固定したい出力には、プロンプトで細かく指示するより、見本の添付を先に試す価値がある。
- 小さな範囲から始め、動作確認後に広げる進め方を、研究室の自動化導入の手順に取り入れられる。
- 外部共有は次回扱いのため、機密情報を含むNotebookの共有判断は、次回動画や公式資料の確認後にする。

## 限界・未確認

- 映像は未確認で、画面操作や設定項目名は音声字幕からの推定を含む。
- 公式資料とは未照合。Workspace Studioの仕様、提供条件、料金区分、上限の最新値は UNKNOWN。
- 字幕は自動字幕の誤変換の可能性がある（例：人名・社名・数字・「Notebook」表記）。数値（25個、ステップ数、繰り返し回数、所要時間）は要再確認。
- 字幕には聞き取り不明の箇所が1つあり、該当部分の内容は不明。
- 実際に再現して動作確認はしていない。出力品質（書式の再現性、課題抽出の精度）は話者の自己評価に依存する。
- 外部ユーザーへのNotebook共有の仕様は次回扱いで、本動画では UNKNOWN。
