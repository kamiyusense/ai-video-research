---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：今週のGitHub急上昇リポジトリTOP10（2026年10月）"
description: "スター数/日で並べたGitHub注目10リポジトリを紹介する動画の研究ノート。エージェントハーネス、エージェントスキル、有料アプリのOSSクローンという傾向と、動画側の検証結果・未検証点を整理する。"
tags:
  - "AI技術研究室"
  - "GitHubトレンド"
  - "エージェントハーネス"
video_id: "_P3YqBzHvSs"
logical_id: "youtube:_P3YqBzHvSs:research"
transcript_logical_id: "youtube:_P3YqBzHvSs:transcript"
resource: "https://www.youtube.com/watch?v=_P3YqBzHvSs"
canonical_url: "https://www.youtube.com/watch?v=_P3YqBzHvSs"
published_at: "2026-10-25"
---

# 今週のGitHub急上昇リポジトリTOP10（2026年10月）

## 独自要約

作成日からの平均スター数/日で10個のOSSリポジトリを順位付けし、安全に試せたものは実機で動作確認した動画。今週の傾向はエージェントハーネス、エージェントスキル、有料デスクトップアプリのRust製クリーンルーム複製の3系統。確認結果は成功・失敗・未実行が混在し、配信者自身も「デモは決定的な簡易タスクで、ベンチマークではない」と断っている。数値は2026年10月23日時点で、本ノートでは未照合。

## チャプター

- イントロ・選定基準（スター/日順、OSSライセンスのみ、怪しいものは除外）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=0s>
- 10位 SolidCraft（Rust製パラメトリック3D CAD、MCPサーバ内蔵）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=33s>
- 9位 WordCraft（Rust製ワープロ、docx対応、WebAssembly）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=71s>
- 8位 Harness squared（Google Research、ハーネスの再帰的改善）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=94s>
- 7位 Skills（Matt Pocock、エージェントスキル集）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=139s>
- 6位 OpenClaw（ローカル実行のAIアシスタント）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=175s>
- 5位 Anatomy（概念を等角投影オブジェクトで説明するClaudeスキル）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=202s>
- 4位 Ponytail（コードを書かない方向に誘導するエージェント規律）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=234s>
- 3位 DeepInfer（DeepSeekの推論フレームワーク）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=270s>
- 2位 PhotoCraft（Rust製Photoshop風アプリ）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=309s>
- 1位 DeepSeek Harness（プラグイン設計のエージェントハーネス）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=349s>
- 総括（今週の3傾向）: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=385s>

## 重要な知見

1. **ランキング方式は「作成日からの平均スター/日」**。累積スターの多さとは一致せず、新しいリポジトリが有利になる。Skillsは累積約30万だが7位、DeepSeek Harnessは71日で約26万となり1位。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=15s>
2. **Rust製クリーンルームの複製系が3件**（CAD、ワープロ、画像編集）。PhotoCraftは約1564ファイル・約70万行だが、公式ロードマップは初期アルファで、ベータまでさらに相当な工数が必要とされる。「Photoshop代替ではない」というのが動画の評価。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=309s>
3. **Harness squaredは「モデル重みを固定し、プロンプト・ツール・メモリ・オーケストレーションを再帰的に改善する」発想**。ローカルデモは認証情報不要で、2タスク成功・失敗0。ただし決定的なデモで、実ベンチはAPI費用がかかると明言。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=94s>
4. **スキル集はほぼプロンプトとMarkdown**で、導入負荷が小さい。Skillsは工学・生産性・その他に分かれ、用語集を持つ。AnatomyはNodeで確認し、依存ゼロ、スキル本体185行、例図9点。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=139s>、<https://www.youtube.com/watch?v=_P3YqBzHvSs&t=202s>
5. **Ponytailの「コード量が約半分」という主張はプロジェクト自身のREADME上のもので、動画は再現していない**。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=234s>
6. **安全方針の明示**: シェルへ直接パイプするインストーラは実行せず、OpenClawはデモ省略。「自分でインストーラを読んでから信頼せよ」という助言。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=175s>
7. **DeepInferはGPU（NVIDIA新世代またはHuawei Ascend）が必要で、GPUなしのクラウド機では実行不可**。コードはC++コアとPythonエンジン構成として閲覧のみ。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=270s>
8. **DeepSeek Harnessは開発者プレビューで、互換性を壊す変更の警告あり**。npmに0.2.1系のリリース候補が存在するが、npx起動は「コマンドが見つからない」で失敗と報告。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=349s>
9. **SolidCraftは規模が大きすぎてビルドせず、コード規模の計数のみ**（未実行）。MCPサーバ内蔵でAIエージェントから操作できるとされる。根拠: <https://www.youtube.com/watch?v=_P3YqBzHvSs&t=33s>

## この研究室への応用

- **ハーネス設計の比較材料**: Harness squaredとDeepSeek Harnessを、本研究室のエージェント運用（プロンプト・ツール・記憶の構成）の参照例として一次情報（各リポジトリ）で読む。
- **スキル/Markdown運用**: SkillsとAnatomyの構成（フォルダ分割、用語集、短いスキル本体）をスキル整理の参考にする。
- **検証手順の型**: 「インストーラは読んでから」「実行不能なら実行不能と報告」「作者の主張と再現を分ける」を、本研究室の検証ノートの書式に採り入れる。
- **MCP連携の観点**: SolidCraftのようにMCPを内蔵するツールが増えているかを、次回以降の観察項目とする。

## 限界・未確認

- 映像は未確認。字幕テキストのみを根拠とし、画面上の表示（数値、コマンド出力、スライド）は見ていない。
- 公式資料（各リポジトリ、GitHub、npm）は未照合。スター数、日割り、ファイル数、行数、ライセンス、日数はすべて動画の発言のまま。
- 字幕は取得上「手動」区分だが、transcript_statusはUNVERIFIED。固有名（DeepInfer、Harness squared、制作者名、チーム名）や数値の聞き取り・変換誤りの可能性がある。
- 各ツールの外部仕様（対応環境、機能の詳細、MCP仕様、対応モデル、GPU要件の正確な型番、ライセンス条項）: UNKNOWN。
- 動画は説明中に概要欄/コメント誘導など宣伝要素を含む。選定の網羅性や「怪しいもの」の除外基準は不明。
- 動作確認は1回・1環境の報告に限られ、再現性は未確認。
