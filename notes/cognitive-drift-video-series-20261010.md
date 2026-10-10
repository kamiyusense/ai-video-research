# AIとの認識ズレ・認知ドリフト対策：動画連続調査（受付台帳）

- 作成日: 2026-10-10 JST
- 状態: INTAKE_OPEN / MULTI_VIDEO_COLLECTION / FINAL_COMPARISON_PENDING
- 目的: ユーザーが順次提示する複数動画から、AIとの認識ズレの原因・予防策・適用条件・実装可能な手段を比較し、すべて揃った後に実用的な対応策を返す。
- 共有正本: private `kamiyusense/ai-video-research`、この研究ノートは調査途中の索引。
- 注意: **元動画を直接確認していない箇所を確認済みにしない。** 時刻は時刻付き一次資料に基づく場合のみ正確とする。外部記事の時刻は第三者による報告とする。
- 記録方針: 動画IDで重複しない。研究の完了判定と `registry.json` への正式登録は、独立確認と検品の後に行う。字幕全文・外部AI回答全文・動画本体・認証情報は保存しない。
- 人間による投稿完了の合図待ち。調査対象の追加は歓迎するが、総合評価は合図を受けてから作成。

## 受付済み

### 01｜3bLrrkA1nlQ
- URL（ユーザー提示）: https://www.youtube.com/watch?v=3bLrrkA1nlQ&t=55s
- 正規URL: https://www.youtube.com/watch?v=3bLrrkA1nlQ
- 動画タイトル（第三者の動画紹介記事より）: 【認識ズレ対策】世界で話題、Claude Code公式の『html-plan』スキル！AIとの認識ズレを1枚のHTMLで解消する方法を解説します
- 投稿者（第三者記事より）: まさおAIじっくり解説ch
- 公開日・長さ（第三者記事より）: 2026-10-07 / 8分35秒
- 元動画（音声・映像・字幕）: NOT_ACQUIRED / UNKNOWN
- 動画内の正確な発言・実演時刻: UNKNOWN（指定開始 `t=55s` はユーザーURLの再生位置であり内容の実証時刻ではない）
- 関連する第三者レビュー（動画原本ではない）: https://ai-kidou.jp/video-report-html-plan-ninshiki-zure/
- 一次資料（実際の公開スキル本文）: https://github.com/anthropics/claude-plugins-community/blob/main/html-plan/skills/html-plan/SKILL.md
- 配布元の説明: https://github.com/anthropics/claude-plugins-community/blob/main/README.md
- 一次資料からの独立確認（**動画要約ではない**）: `html-plan` は実装計画を一枚の対話可能なHTMLで可視化し、利用者が決定点に回答し、それをコピーしてAIへ返す仕組み。計画を作っているだけで開発完了とはしない。
- 一次資料からの重要な注意: 参照先の `claude-plugins-community` は**コミュニティ提供プラグインのマーケットプレイスのミラー**。Anthropic管理の `claude-plugins-official` とは別。動画表題の「Claude Code公式スキル」をClaude本体への標準搭載やAnthropic製作者による公式内製機能と同一視しない。
- 検証すべき効果: 計画画面によって「完成物イメージ」「実装判断」「責任範囲」のズレが減るか。レビュー時間、手戻り、利用者に必要な技術知識。効果の定量的実証はUNKNOWN。
- 次工程: 映像担当／字幕担当の独立報告（可能なら）。他の認識ズレ対策動画を追加し、共通原因と補完関係を比較。
- 判定: PUBLIC_SECONDARY_PLUS_UPSTREAM_DOC_ONLY / AWAITING_EXTERNAL_REPORT / NOT_TESTED

## 受付対象に含めなかったもの
- `MVVpR2Bb0Rk`: 前に提示された動画。外部AIが `sponsors_only_video` と報告したが、ユーザーは次の動画へ進むよう指定。アクセス制限の独立確認はUNKNOWN。今回は「認識ズレ」連続調査の対象動画に含めない。

## 比較の観点（今後の動画にも共通）
1. 認識ズレの種類: 目標／要件／実装／品質判定／状況把握・記憶。
2. 対策が働く時点: 着手前／途中／完了判定／新チャットへの引き継ぎ。
3. 必要な環境: 特定AI・Skill・ローカル/クラウド・GitHub・有料契約。
4. 実証の程度: 動画上の主張、画面実演、一次資料、別環境での試験。
5. 既存システムとの重複: `AGENTS.md`・`MEMORY.md`・引継ぎ・独立検品・GitHubの正本化。
6. 安全性: 権限・課金・外部実行・途中停止・誤認された完了の検知。

## 実行境界
- 保存は本研究室の許可された非default branchだけ。書込み後はGitHubから読み戻す。
- 外部AIやSkillのLIVE起動、課金、APIキー操作、権限変更、他リポジトリへの変更、Merge、force push、削除は行わない。
- この文書は**受付と一次資料調査**であって、複数動画を視聴済み、対策を実機検証済み、または自動調査が稼働中という意味ではない。

## 調査01・追記（2026-10-10）
- [html-planの暫定研究](../research/2026-10-10-3bLrrkA1nlQ-html-plan-preliminary.md) を登録。上流スキルと投稿者本人の解説を照合。
- 着手前の認識合わせが主な用途。未読デフォルトは承認ではない。計画の英語規約とNode依存は未検証の採用課題。
- 動画原本の音声・映像・字幕は未取得。効果の実測はNOT_TESTED。総合比較は他動画を待つ。
