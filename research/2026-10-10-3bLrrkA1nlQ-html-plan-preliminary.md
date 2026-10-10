# 認識ズレ対策・動画3bLrrkA1nlQ：html-plan暫定研究
- 動画: https://www.youtube.com/watch?v=3bLrrkA1nlQ （ユーザー提示開始位置55秒）
- タイトル: 【認識ズレ対策】世界で話題、Claude Code公式の『html-plan』スキル！AIとの認識ズレを1枚のHTMLで解消する方法を解説します
- 投稿者: まさおAIじっくり解説ch / 公開日: 2026-10-07 / 長さ: 8分35秒（投稿者の関連記事と視聴レポートによる）
- 研究日: 2026-10-10。直接視聴、音声、映像、字幕: NOT_ACQUIRED。以下の動画時刻は第三者レポートに基づき、独立確認はUNKNOWN。
- 判定: CREATOR_ARTICLE_AND_UPSTREAM_SOURCE_CONFIRMED / SECONDARY_TIMESTAMP / DIRECT_VIDEO_UNKNOWN / LIVE_NOT_RUN

## 結論
html-planはClaude Codeでの実装着手**前**に、完成する機能・仕組み・具体的な修正箇所を見える形で一枚のHTMLに並べ、人間が必要な判断を選択・コメントし、ひとつの回答をAIに貼り戻すスキル。実装中の暴走や完成後の検品を自動で防ぐものではない。

## 動画時刻（第三者報告、直接確認ではない）
- [00:43](https://www.youtube.com/watch?v=3bLrrkA1nlQ&t=43s) 認識ズレ
- [01:19](https://www.youtube.com/watch?v=3bLrrkA1nlQ&t=79s) HTML計画画面
- [01:36](https://www.youtube.com/watch?v=3bLrrkA1nlQ&t=96s) 回答コピー
- [03:24](https://www.youtube.com/watch?v=3bLrrkA1nlQ&t=204s) 判断の要約
- [03:39](https://www.youtube.com/watch?v=3bLrrkA1nlQ&t=219s) 非開発者にとってのコードの難しさ
- [05:02](https://www.youtube.com/watch?v=3bLrrkA1nlQ&t=302s) 赤ペン方式との比較
- [06:40](https://www.youtube.com/watch?v=3bLrrkA1nlQ&t=400s) HTMLで認識を合わせる評価
出典: https://ai-kidou.jp/video-report-html-plan-ninshiki-zure/

## 上流実装と投稿者本人による一次照合
1. 公式ソース https://github.com/anthropics/claude-plugins-community/blob/main/html-plan/skills/html-plan/SKILL.md : WHAT（利用者に見える動作）→ HOW（仕組み）→ WHERE（実際のファイル/コード行）。最大3階層、決定点2〜5件。利用者の回答が戻るまで実装しない。
2. README https://github.com/anthropics/claude-plugins-community/blob/main/html-plan/README.md : Respond / Copy responseを使い、人間がClaudeへ貼る。NodeでオフラインHTML化。外部AIへの自動送信機能ではない。
3. **重要な誤認防止**: 「開いて了承したデフォルト」と「開いていないデフォルト」は別。後者は承認ではない。未確認の重要決定は再確認する。
4. SKILL.mdは計画文書に英語のASD-STE100を指定。日本語UI標準対応は未確認で、日本語利用者への導入障壁。
5. pack.mjsの静的チェックは構造・参照など。実装が要件を満たすかどうかを保証しない。
6. 出所はClaude Code関係者による試作公開で、配布先はAnthropicの**コミュニティ**プラグインマーケット。Claude本体に標準搭載された公式製品との同一視は不可。投稿者自身も正式発表前と記述。
7. 投稿者自身の補足記事（直接の動画字幕ではない）: https://note.com/masa_wunder/n/n29b09dec1896
8. Anthropic公式のプラグイン仕様・権限注意: https://code.claude.com/docs/en/plugins

## 研究室向けの独自提案
- 各仕事に一律に導入せず、重要・不可逆・複数ファイル変更時の着手前だけ「利用者に見える結果」「変更しない範囲」「決めたい2〜4点」「根拠」「合格条件」を短く説明する。
- AGENTS/MEMORYは前提知識の共有、html-plan型は着手前の認識合わせ、reviewerは完成後の検品。目的が異なるので置き換えない。
- 日本語で短い確認書をSTATIC設計してから、必要ならhtml-planの実機試用を別途検討。英語原文規約のまま日本語可用性は未証明。
- 無人Loopの全工程に人手承認を要求すると止まるので、リスクに応じた選択制とする。LIVE/課金/権限/mergeは別承認。
- 未解決: 動画原本直接確認、Windows/Claudeでの動作試験、認識ズレを減らす実測効果はUNKNOWN。
