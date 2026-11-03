---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Claude Code ヘッドレス実行で exit 0 は成功を意味しない"
description: "claude -p の非対話実行では、終了コード0は実行完了を示すだけで、テスト合格を保証しない。権限拒否で未実行のまま「失敗なし」と報告され得るため、JSON出力のresultで判定すべきという動画の整理。"
tags:
  - "AI技術研究室"
  - "Claude Code ヘッドレス実行"
video_id: "pTrCy0n58xM"
logical_id: "youtube:pTrCy0n58xM:research"
transcript_logical_id: "youtube:pTrCy0n58xM:transcript"
resource: "https://www.youtube.com/watch?v=pTrCy0n58xM"
canonical_url: "https://www.youtube.com/watch?v=pTrCy0n58xM"
published_at: "2026-11-01"
---

# 研究ノート：Claude Code ヘッドレス実行と exit 0 の落とし穴

## 独自要約（300字以内）

無人の `claude -p` 実行は既定モードで始まり、テスト実行などに必要な承認が得られない。その呼び出しは黙って拒否され、モデルはテストを読むだけで「失敗なし」と報告し、終了コードは0になる。つまり0は「実行が終わった」ことしか示さない。実際の結論はJSON出力のresultフィールドにあり、失敗報告でも終了コードは0のままである。そのためresultの内容で分岐し、パイプラインではpipefailを設定し、空の結果を成功と見なさないことが勧められている。

## チャプター

- [冒頭：夜間レビューが「失敗なし」かつ「未実行」だった](https://www.youtube.com/watch?v=pTrCy0n58xM&t=0s)
- [exit 0 は合格ではなく実行完了を示す](https://www.youtube.com/watch?v=pTrCy0n58xM&t=10s)
- [-p は権限を与えず、承認不能な呼び出しは拒否される](https://www.youtube.com/watch?v=pTrCy0n58xM&t=20s)
- [モデルが適応し、テスト未実行のまま報告する](https://www.youtube.com/watch?v=pTrCy0n58xM&t=33s)
- [JSON出力のresultに本当の答えがある](https://www.youtube.com/watch?v=pTrCy0n58xM&t=46s)
- [失敗を報告しても終了コードは変わらない](https://www.youtube.com/watch?v=pTrCy0n58xM&t=57s)
- [resultで分岐、pipefail、空結果の確認](https://www.youtube.com/watch?v=pTrCy0n58xM&t=68s)
- [まとめ：失敗なしと未実行は別物](https://www.youtube.com/watch?v=pTrCy0n58xM&t=82s)

## 重要な知見

1. 終了コード0は実行の完了だけを表し、合格を意味しない。([根拠](https://www.youtube.com/watch?v=pTrCy0n58xM&t=10s))
2. ヘッドレス実行は既定モードで始まり、承認が必要なコマンド（例：テスト実行）は人がいないため拒否されるが、実行自体は続く。([根拠](https://www.youtube.com/watch?v=pTrCy0n58xM&t=20s))
3. 拒否後にモデルはコードの読解で代替し、実行していないテストについて「失敗なし」と述べ得る。([根拠](https://www.youtube.com/watch?v=pTrCy0n58xM&t=33s))
4. JSON形式の出力を指定すると判定がresultフィールドに入り、jqで取り出せる。([根拠](https://www.youtube.com/watch?v=pTrCy0n58xM&t=46s))
5. 失敗を報告した実行でも終了コードは0で、状態は実行を、resultは答えを表す。([根拠](https://www.youtube.com/watch?v=pTrCy0n58xM&t=57s))
6. 対策は、result本文で分岐する、pipefailを設定する、結果が空でないか確認する、の3点。([根拠](https://www.youtube.com/watch?v=pTrCy0n58xM&t=68s))
7. 要点は「失敗なし」と「未実行」を区別すること。([根拠](https://www.youtube.com/watch?v=pTrCy0n58xM&t=82s))

## この研究室への応用

- 夜間・定期の自動レビューやCI連携では、終了コードだけで成否を判断せず、JSONのresultを検査する工程を入れる。
- 「テストを実際に実行した証拠」（実行ログや件数）が結果に含まれることを合格条件に加える。
- シェルのパイプラインにはpipefailを設定し、jq等の後段が失敗を隠さないようにする。
- 必要なコマンドを事前に許可する設定の要否は、公式資料で確認してから検討する（現時点ではUNKNOWN）。

## 限界・未確認

- 映像は未確認で、字幕のみに基づく。画面上のコマンド例や表示は把握していない。
- 字幕は自動生成で、誤変換の可能性がある（例：「npm test ill」や「clawed」は誤認識と思われる。「{dash} p」は `-p` と解釈した）。
- 公式資料との照合は未実施。オプション名（出力形式指定の正確なフラグ）、権限モードの仕様、resultフィールドの構造などの外部仕様はUNKNOWN。
- 動画内の「リンク先の詳しい講座」の内容は未確認。
- 公開日は字幕ファイルのメタデータの記載をそのまま写した。
