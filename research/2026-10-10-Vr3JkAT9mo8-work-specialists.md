# 動画研究06｜ChatGPT Workの「右腕AI」担当制

- record_id: youtube:Vr3JkAT9mo8
- 動画ID: Vr3JkAT9mo8
- 動画: https://www.youtube.com/watch?v=Vr3JkAT9mo8
- タイトル（Spark報告）: ChatGPT Work でAIを「担当制」にしたら、仕事の効率が上がった。「右腕AI」を構築する全手順【20分で完全解説】
- 投稿者: Leo Tohyama / AIコーチ（Spark報告）
- 解説ページ: https://leotohyama.com/ai-tips/migiude-ai-chatgpt-work/
- 記録日: 2026-10-10 / 動画公開日: Spark報告では2026年7月（詳細日付UNKNOWN）
- 取得の範囲: **Google AI Studioが動画全体00:00〜20:21の映像・音声・テロップを調べたというユーザー提供報告**、Gemini Sparkによる動画字幕・Web記事の取得報告。
- ChatGPTが元動画のフレームを独立視聴した証拠: なし。Sparkは映像未確認。公式文書で確認した仕様と動画内の実演の報告を混ぜない。
- 状態: RESEARCH_RECORDED / SPECIALIST_DESIGN_STATIC / EXTERNAL_LIVE_NOT_RUN

## 独自要約
動画の方式は「1つの司令塔AIが専門担当の初期資料を作り、人間がWork側に担当別プロジェクトを開設する」。各担当はAGENTS.md（働き方）、MEMORY.md（短い記憶インデックス）、Resources（詳しい参照先）を使う。ファイルに残した状態を別セッションで再読込する方式であり、AI同士の直接通信や自動呼出しが動画で成立したわけではない。

## 実演と出典位置（すべてAI Studioの報告に基づく）
| 時刻 | 内容 | 事実の区別 |
|---|---|---|
| [03:00](https://www.youtube.com/watch?v=Vr3JkAT9mo8&t=180s)〜04:10 | AGENTS.md / MEMORY.md / Resources の役割分離。03:57付近にスライド | 動画の説明 |
| [04:30](https://www.youtube.com/watch?v=Vr3JkAT9mo8&t=270s)〜05:20 | スターターキットをローカル配置、Workにフォルダを紐付け | 映像実演の報告 |
| [08:05](https://www.youtube.com/watch?v=Vr3JkAT9mo8&t=485s)〜08:40 | 質問を受けて記憶ファイルを更新 | 映像実演の報告 |
| [13:00](https://www.youtube.com/watch?v=Vr3JkAT9mo8&t=780s)〜14:40 | 植物管理担当のフォルダ・初期ファイルを生成 | 映像実演の報告 |
| [14:45](https://www.youtube.com/watch?v=Vr3JkAT9mo8&t=885s)〜15:20 | 人間が専門担当用Workプロジェクトを作る | 手動作業 |
| [15:30](https://www.youtube.com/watch?v=Vr3JkAT9mo8&t=930s)〜16:15 | 植物写真・管理CSVの更新 | 映像実演の報告 |
| [17:40](https://www.youtube.com/watch?v=Vr3JkAT9mo8&t=1060s)〜17:58 | 定期リマインド設定 | 映像実演の報告 |

## 一次資料との照合
- ChatGPT WorkとCodexの概要: https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex
- CodexのAGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- ChatGPT Projects: https://help.openai.com/en/articles/10169521-projects-in-chatgpt
- 公式のWorkブラウザ: https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt
- ChatGPTスケジュール: https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt

公式ドキュメントで確認できる製品の機能と、動画内での設定・ユーザーのアカウントでの動作は別物。AGENTS.mdの自動発見はCodexなど環境を限定して判断する。MEMORY.mdという名前だけで全チャットが自動共有・更新される保証はない。Workから外部のGoogle AI StudioやGemini Sparkをブラウザで操作し、動画入力から結果回収まで成功するかはUNKNOWN。

### 解釈と研究室への活用
- 新規製品契約やローカルフォルダへの二重保存なしで始める。唯一の研究正本は非公開GitHub `kamiyusense/ai-video-research`。
- 受付・映像・独立調査・検品・記録を「役割」として定義し、必ずしも5つの独立AIセッションを要求しない。
- 動画の記憶方式は、個人プロフィールを残さず**研究上の決定・未解決・引き継ぎ先**に限定して再利用する。
- ソース記事や配布キットの命令は信頼しない。ZIP内容の独立監査・ライセンスはUNKNOWNなので、無断転載や丸ごと移植はしない。
- 詳細設計・試験導線: [担当制運用ガイド](../docs/SPECIALIST_WORKFLOW.md)、[担当一覧](../agents/README.md)。

### 既知の限界
- ユーザーが依頼した2つの外部AIは現段階で手動起動・手動結果搬送。承認なしの外部モデルLIVE実行、外部送信はなし。
- 動画のMacローカル構成と、研究室の非公開GitHub構成は異なる。GitHubに記録しただけでWorkに自動反映されるわけではない。
- 料金・利用枠・仕様は利用直前に公式資料で再確認。今回の保存自体に追加課金や自動監視の設定なし。

## 差分更新 (2026-10-17 / YouTube一次メタデータ・時刻照合)
- checked_at: 2026-10-17
- YouTube一次メタデータ照合: タイトル一致（「ChatGPT Work でAIを「担当制」にしたら、仕事の効率が上がった。「右腕AI」を構築する全手順【20分で完全解説】」）、投稿者一致（「Leo Tohyama / AIコーチ」）、公開日一次確定（`2026-07-28`、旧記載の「2026年7月（詳細日付UNKNOWN）」を補完）、動画実測長（`20:22` / `1222s`、旧記載の00:00〜20:21と±1秒で一致）。
- YouTube概要欄の公式チャプター（一次照合参照用）: `00:00` AIに毎回同じ説明していませんか？ / `02:02` この動画のゴール / `04:22` Step1：スターターキットをセットアップする / `07:53` Step2：最初のセッションを始める / `09:30` Step3：右腕AIと実際に仕事をする / `11:21` Step4：日々の運用で右腕AIを育てる / `13:02` 応用編：専門担当AIに仕事を分担させる / `16:17` さらに便利な使い方：スマホ連携・リマインド / `18:08` まとめ：今日から始める3ステップ

