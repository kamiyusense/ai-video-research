---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Learn 99% Of Claude Code in One Video"
description: "Claude Codeの導入から、モデル・努力レベル・権限モード、CLAUDE.md、メモリ、スキル、サブエージェント、MCP、フック、コンテキスト管理、worktree、routinesまでを設定順に解説した動画の独自整理。字幕のみ根拠。"
tags:
  - "AI技術研究室"
  - "Claude Code"
  - "動画研究"
video_id: "3TwbE7gv6qo"
logical_id: "youtube:3TwbE7gv6qo:research"
transcript_logical_id: "youtube:3TwbE7gv6qo:transcript"
resource: "https://www.youtube.com/watch?v=3TwbE7gv6qo"
canonical_url: "https://www.youtube.com/watch?v=3TwbE7gv6qo"
published_at: "2026-10-24"
---

# 研究ノート：Learn 99% Of Claude Code in One Video

## 独自要約（300字以内）

Claude Codeを既定設定のまま使わず、設定すべき順に整えるための解説動画。デスクトップ版のコードモードでプロジェクトを開き、モデルと努力レベルを使い分け、権限は自動モードを基本とする。次に計画モードで要件を詰め、CLAUDE.mdやメモリで規約を固定する。さらにスキル、サブエージェント、MCP、フック、プラグインで拡張し、コンテキスト管理、巻き戻し、worktree、コードレビュー、定期実行で運用を締める。

## チャプター

| 開始 | 内容 |
|---|---|
| [0s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=0s) | 導入：設定順に全機能を扱う方針 |
| [50s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=50s) | 利用場所（Web・デスクトップ・端末・スマホ）とインストール |
| [153s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=153s) | アカウントと料金プラン |
| [205s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=205s) | コードモードへの切替、プロジェクト（フォルダ）とセッション |
| [389s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=389s) | モデルと努力レベルの選び方 |
| [664s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=664s) | 権限モード |
| [836s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=836s) | 計画モードでの新規プロジェクト開始（デモ） |
| [1015s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1015s) | CLAUDE.mdと /init |
| [1244s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1244s) | メモリの保存先 |
| [1398s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1398s) | .claudeフォルダとsettings.json |
| [1523s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1523s) | @参照、画像、ブラウザ上の注釈 |
| [1623s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1623s) | スキル（全体／プロジェクト単位） |
| [1887s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1887s) | サブエージェント |
| [2096s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2096s) | MCP |
| [2147s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2147s) | フック |
| [2318s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2318s) | プラグイン |
| [2368s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2368s) | Mods |
| [2414s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2414s) | コンテキスト管理（/context, /clear, /compact） |
| [2639s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2639s) | 履歴の呼び出しと /rewind |
| [2679s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2679s) | 並列セッションとworktree |
| [2763s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2763s) | コードレビュー |
| [2796s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2796s) | routines（定期実行） |
| [2852s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2852s) | まとめ：覚えるより存在を知る |

## 重要な知見

1. **モデル選択**：話者は、上位プランなら既定のOpusで足り、使用量を節約したい場合に軽量側へ切り替えると述べる。Fableは最上位だが多くの場面でOpusを推奨している。根拠：[417s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=417s)、[429s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=429s)
2. **努力レベル**：日常はmedium、高いほど時間と消費が増え、最上位は数時間かかることもあるという。根拠：[558s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=558s)、[582s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=582s)、[623s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=623s)
3. **権限**：自動モードを基本にし、全許可は勧めない。確認したい作業は計画モードを使う。根拠：[673s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=673s)、[734s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=734s)
4. **計画モード先行**：曖昧に要望を書き、質問させて計画を固めてから実装に入る手順を示す。根拠：[854s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=854s)、[860s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=860s)
5. **CLAUDE.md**：新規会話のたびに読まれる規約ファイルで、全体を再探索させずに済むとされる。階層配置も可能だが一般的ではないという。根拠：[1057s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1057s)、[1160s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1160s)、[1193s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1193s)
6. **メモリの保存先**：既定ではプロジェクト外のローカル領域に保存され、リポジトリには入らない。共有したければ明示的に指示する。根拠：[1303s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1303s)、[1332s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1332s)、[1366s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1366s)
7. **settings.json**：許可・確認・拒否のルールを書け、例として.envの読み取り拒否を挙げる。根拠：[1485s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1485s)
8. **スキル**：繰り返す指示をMarkdownにまとめる仕組みで、保存先を全体かプロジェクトに選べる。根拠：[1666s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1666s)、[1771s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1771s)、[1834s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1834s)
9. **サブエージェント**：本流のコンテキストを汚さず背景で並列実行でき、モデルや努力レベルを個別に設定できる。根拠：[1933s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=1933s)、[2049s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2049s)
10. **フック**：特定イベントで必ず実行されるシェルコマンド。デモでは停止イベントに通知を結び付けた。根拠：[2221s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2221s)、[2236s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2236s)
11. **コンテキスト**：満杯に近いほど誤りと消費が増えるため、確認と圧縮・消去を使い分ける。根拠：[2441s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2441s)、[2528s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2528s)
12. **巻き戻し**：会話・コードのどちらか、または両方を戻せ、巻き戻しの取り消しも可能という。根拠：[2661s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2661s)、[2675s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2675s)
13. **worktree**：並列セッションの上書きを防ぐがマージ衝突は残る。デスクトップ版では既定オフでGitHubリポジトリが必要と説明。根拠：[2704s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2704s)、[2712s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2712s)
14. **設計思想**：機能は暗記せず、存在を知ってClaudeに設定させればよいという立場。根拠：[2875s](https://www.youtube.com/watch?v=3TwbE7gv6qo&t=2875s)

## この研究室への応用

- 動画研究の作業フォルダごとにCLAUDE.mdを置き、OKF荷札の書式、引用の字数上限、字幕を転載しない規則を固定する案。
- 研究ノート生成を手順化したスキルとして切り出し、プロジェクト単位で保存する案。
- 字幕の整合性検査をサブエージェントに任せ、本流の文脈を保つ案。
- settings.jsonで秘密情報ファイルの読み取り拒否を設定し、字幕中の命令に引きずられない運用の下地にする案。
- 長い作業は /compact や /rewind を前提にし、区切りごとに成果物を保存する運用。

いずれも本ノート作成者の提案であり、動画が述べた内容ではない。

## 限界・未確認

- 映像は未確認。画面操作やUI表示は字幕の発話からの推測を含む。
- 公式資料は未照合。モデル名、プラン名、コマンド、設定ファイルの仕様、イベント数、料金・上限などの外部仕様は**UNKNOWN**。
- 字幕は取得上 transcript_status が UNVERIFIED。語の誤変換の可能性があり、例として製品名や用語（subagent、worktree、Mods等）の表記ゆれが見られる。
- 話者は動画内で収録日を2026年10月9日と述べており、投稿日と異なる。モデル構成や機能は変わりうる。
- 話者自身が一部の挙動（圧縮後のトークン数など）に不明点があると述べている。
- 冒頭でスポンサー表記があるが、内容の中立性は未評価。
- 参照元として想定した research_note_prompt_template.md は作業フォルダに見当たらず、読めなかった。書式は依頼文の指定に従った。
