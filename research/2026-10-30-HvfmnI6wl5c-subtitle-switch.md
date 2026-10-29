---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：Claude CodeとREAによるリバースエンジニアリング入門"
description: "REAがGhidra・IDA Pro・Hopperを使いAIに解析させる仕組みと、Macの電卓再現でREA有無を比べた動画の研究ノート。字幕のみに基づく。"
tags:
  - "AI技術研究室"
  - "リバースエンジニアリング"
  - "Claude Code"
video_id: "HvfmnI6wl5c"
logical_id: "youtube:HvfmnI6wl5c:research"
transcript_logical_id: "youtube:HvfmnI6wl5c:transcript"
resource: "https://www.youtube.com/watch?v=HvfmnI6wl5c"
canonical_url: "https://www.youtube.com/watch?v=HvfmnI6wl5c"
published_at: "2026-10-15"
---

# 研究ノート：Claude CodeとREAによるリバースエンジニアリング入門

> 根拠は自動字幕のみ。映像は未確認、公式資料は未照合。自動字幕には誤変換の可能性がある（例：Claudeが「Cloud」と表記されている）。

## 独自要約

REAは、Ghidra・IDA Pro・Hopperといった既存の解析ツールをAIエージェントへ渡す道具箱として紹介されている。投稿者はMac標準の電卓の基本モードをWebページで再現させ、REAありのClaude Codeとなしのものを比べた。どちらも「200+10%=220」という隠れた挙動を再現できた。違いは経路である。REAありは逆コンパイル結果の該当コードを根拠に示した。なしは実機操作の総当たりで推定し、実装箇所は不明と答えた。見た目はなしの方が近かったという。投稿者は新技術ではなく、既存ツールを導入しやすく包んだものと位置づけている。

## チャプター

- [導入：REAの概要と動画の狙い](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=0s)
- [本棚の例えで見るリバースエンジニアリング](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=37s)
- [Ghidra：逆アセンブルと逆コンパイル](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=72s)
- [IDA ProとHopper](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=117s)
- [REAなし・ありの比較設計と電卓の隠れた規則](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=170s)
- [導入手順（リポジトリ確認・セットアップ）](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=222s)
- [REAありでの電卓再現](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=289s)
- [規則の出どころの確認（REAあり）](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=412s)
- [REAなしでの電卓再現と回答](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=448s)
- [まとめと所感](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=583s)

## 重要な知見

1. REAは新しい解析ツールではなく、既存ツールをAIへ橋渡しする「道具箱」と説明されている。投稿者は三つの主要ツールを挙げる。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=72s)
2. 解析には逆アセンブル（低レベルの命令列）と逆コンパイル（擬似コード）の二段階がある。擬似コードには名前の手がかりが乏しく、各部の役割の特定に専門知識と時間が要る。投稿者はAIが得意な作業と述べる。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=82s)
3. HopperはMacやiPhoneアプリ向けとされ、今回のMac電卓に使われた。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=130s)
4. 検証題材は電卓の「200+10%」である。素朴な実装なら200.1になるが、実機は220を返す。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=194s)
5. 偽物のリポジトリがあるとの注意があり、正しい配布元を確認するよう促している。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=227s)
6. REAありは、Hopperの逆コンパイル出力から該当の関数と計算を示し、観察だけの推測ではないと説明した。所要は約20分とされる。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=412s)
7. REAなしは、実装箇所は「分からない」と回答し、アクセシビリティ経由の操作と表示読み取りによる総当たりだったと述べた。所要は約44分とされる。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=558s)
8. 最終的な機能は両者とも同等に見えたという。見た目はREAなしの方が原本に近かったと投稿者は述べる。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=522s)
9. REAありの出力には、原本との色の差が少しあったという。[根拠](https://www.youtube.com/watch?v=HvfmnI6wl5c&t=382s)

## この研究室への応用

- 「結果が同じでも根拠の質が違う」という比較軸は、AIエージェント評価に使える。出力の正しさだけでなく、根拠の追跡可能性も測る。
- 既存ツールをMCPで包む設計は、研究室のツール連携の参考になる。
- 動画の比較は一回の試行である。再現するなら、題材・指示・試行回数を揃えて記録する。
- 解析対象は、自分が権利を持つもの、または許諾のあるものに限る。この点は動画では確認できていない。

## 限界・未確認

- 映像は未確認。画面上の操作や出力は、字幕と投稿者の発言からの推測を含む。
- 公式資料は未照合。REAの仕様、導入手順、ツールの来歴や価格などの外部仕様は UNKNOWN。
- 自動字幕のため、固有名詞や数値に誤変換の可能性がある。リポジトリ名やコマンドは、利用前に原典で確認が必要。
- 比較は単発の事例で、所要時間も投稿者の申告である。統計的な優劣は言えない。
- 動画の公開日や再生数などの数値は、字幕外の情報であり確認していない。
- 利用規約やライセンスの面での適法性は、動画では扱われておらず UNKNOWN。
