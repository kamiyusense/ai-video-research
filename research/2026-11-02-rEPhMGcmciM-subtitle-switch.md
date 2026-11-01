---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Skills vs MCP vs CLAUDE.md の読み込みタイミングとコスト"
description: "Claude Codeで CLAUDE.md・スキル・MCPがいつ文脈に載り、どうコストが変わるかを整理した動画の研究ノート。置き場所の判断基準、フックの必要性、字幕に基づく限界も記す。"
tags:
  - "AI技術研究室"
  - "Claude Codeの文脈コスト（CLAUDE.md・スキル・MCP）"
video_id: "rEPhMGcmciM"
logical_id: "youtube:rEPhMGcmciM:research"
transcript_logical_id: "youtube:rEPhMGcmciM:transcript"
resource: "https://www.youtube.com/watch?v=rEPhMGcmciM"
canonical_url: "https://www.youtube.com/watch?v=rEPhMGcmciM"
published_at: "2026-10-28"
---

# 独自要約

CLAUDE.mdは毎リクエストで文脈に載る常時型、スキルは名前と説明だけが起動時に載り本文は使用時に読まれるオンデマンド型、MCPはツール名だけが先に載り定義は必要時に読まれる。MCPは指示ではなく新しい行為能力を与える。CLAUDE.mdやスキルの指示は強制ではなく、必ず実行させたい処理はフックに置く。長い手順はCLAUDE.mdからスキルへ移すのが安価とされる。

# チャプター

- 導入：始める前に設定の一部が読み込まれ、三者は読み込み時期でコストが違う — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=0s>
- 公式表の要点（常時／ほぼ無料／呼出まで安価） — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=18s>
- 空セッションで最初に載る4要素 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=36s>
- CLAUDE.md：常時読込、向く内容と向かない内容、200行目安 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=64s>
- スキル：説明で照合し、使用時に全文を読む — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=119s>
- スキルの注意点：一度読むと残る、圧縮後の再読込上限 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=168s>
- MCP：新しい行為能力、ツール検索 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=206s>
- MCPの出力コストとCLI優先の助言 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=245s>
- 強制力の限界とフック — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=269s>
- 置き場所の4つの目安 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=300s>
- 結論と未解決の問い — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=336s>

# 重要な知見

1. 起動時にはCLAUDE.md、自動メモリ、MCPツール名、各スキルの短い説明が文脈に載る。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=36s>
2. CLAUDE.mdは全文が毎リクエストに含まれるため、常に真である規約向き。週1回の長い手順は不向き。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=64s>
3. インポートで分割しても、読み込みは親と一緒で節約にならない。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=88s>
4. 1ファイル200行未満が目標。AGENTS.mdのみの場合はそれが既定で読まれると述べられる。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=103s>
5. スキルは説明文の質が選択精度を左右する。説明の長さ上限と全体予算があり、超えると使用頻度の低いものから説明が落ちる。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=148s>
6. スキルは読み込み後、本文が以後の全ターンに残る。圧縮後は各スキル先頭部分のみ再読込され、数が多いと古いものが落ち得る。重要事項は先頭に置く。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=168s>
7. MCPは「何をするか」を増やし、スキルは「どうやるか」を教える。両者は併用できる。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=223s>
8. MCPのコストは出力側に出やすく、警告と上限がある。ghのようなCLIがあればツール一覧が増えない分、効率的とされる。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=245s>
9. CLAUDE.mdは強制設定ではなく文脈であり、確実に毎回実行させたい処理はフックにする。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=269s>
10. /context で文脈の内訳と読み込まれたCLAUDE.mdを確認できる。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=328s>
11. 配置の目安：2回間違えた常時規約はCLAUDE.md、3回貼った手順はスキル、見えない外部系はMCPかCLI、必須動作はフック。 — <https://www.youtube.com/watch?v=rEPhMGcmciM&t=305s>

# この研究室への応用

- 既存のCLAUDE.mdを点検し、長い手順をスキルへ移す候補を洗い出す。
- スキルの説明文を「いつ使うか」が明確になるよう見直し、選択ミスを減らす。
- 重要な指示はスキル本文の先頭へ置く運用を試す。
- 必須の検査や禁止事項はCLAUDE.mdの依頼文ではなくフックで担保する案を検討する。
- 外部連携はCLIの有無を先に確認し、なければMCPを検討する。
- /context で導入前後の文脈使用量を比較し、効果を自環境で測る。

# 限界・未確認

- 映像は未確認で、字幕のみに基づく。画面上の図表は把握していない。
- 公式資料は未照合。数値（行数、文字数、割合、トークン上限など）は動画内の発言であり、現行仕様かは UNKNOWN。動画自身も版により変わると述べている。
- 字幕の種別は manual と記録されているが、固有名詞や数値に誤変換が残る可能性がある。transcript_status は UNVERIFIED。
- 外部仕様（Claude Codeの内部挙動、ツール検索の既定、圧縮時の挙動）は UNKNOWN。
- 「最も安価な改善」は話者の意見であり、実測根拠は動画中に示されていない。
- 末尾の「正しいスキルが選ばれたかをどう確かめるか」は未解決として残されている。
