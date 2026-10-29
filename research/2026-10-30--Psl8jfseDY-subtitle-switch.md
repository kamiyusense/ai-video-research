---
okf_version: "0.2"
type: "RESEARCH_NOTE"
title: "研究ノート：REA（Reverse Engineer Anything）を使った道具作りの実践"
description: "配布物をREAで解析し、翻訳・音声入力・話して図を作るプレゼンターを実装する流れを整理した研究ノート。確認済みの点と独自設計の区別、未確認事項を明記する。"
tags:
  - "AI技術研究室"
  - "REA"
  - "リバースエンジニアリング"
  - "動画研究"
video_id: "-Psl8jfseDY"
logical_id: "youtube:-Psl8jfseDY:research"
transcript_logical_id: "youtube:-Psl8jfseDY:transcript"
resource: "https://www.youtube.com/watch?v=-Psl8jfseDY"
canonical_url: "https://www.youtube.com/watch?v=-Psl8jfseDY"
published_at: "2026-10-18"
---

# 研究ノート：REAを使った道具作りの実践

## 独自要約

気になるアプリ操作を1つ選び、手元の配布物をREAで解析して根拠を集め、「解析で確認できたこと」「独自に決めたこと」「未確認のこと」に分けて仕様化し、AIに実装させて動かす流れを、翻訳・音声入力・話して図を作るプレゼンターの3例で示した動画。開発速度の比較実験はしていないと明言している。

## チャプター

- 導入：話した言葉が図とプレゼンになる完成イメージ [0秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=0s)
- REAで開発のどこに根拠が増えるかを確かめる趣旨 [47秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=47s)
- 先行動画との関係と、見てほしい流れの説明 [73秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=73s)
- 例1：翻訳アプリの「Ctrl+C2回」操作の解析と自作 [105秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=105s)
- 例2：音声入力アプリの配布物から対象を絞って解析 [214秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=214s)
- 解析できる範囲の限界と3分類の考え方 [287秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=287s)
- 例3：話しながら図を作るプレゼンターの発想と処理分担 [316秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=316s)
- ページ化、プレゼンモード、テンプレート切替 [395秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=395s)
- 全体分析：インフォグラフィックとマインドマップ [433秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=433s)
- マインドマップの参考調査と独自実装部分 [474秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=474s)
- 自分で試す手順 [511秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=511s)
- 得られた成果と未実施事項、実践の範囲 [546秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=546s)
- まとめと視聴者への問いかけ [586秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=586s)

## 重要な知見

1. 見る順序は「操作を1つ選ぶ → 根拠を調べる → 実装できる仕様にする → 動作を試す」。[86秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=86s)
2. 翻訳例では、配布DLLを実行せずに解析し、ショートカット判定とクリップボード周辺処理を調べた。翻訳モデル自体を取り出したわけではない。[120秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=120s)
3. 設定クラスに2回コピーの既定期限があり、古い要求を区別する連番も確認できたとされ、これが操作仕様の材料になった。ただし期限は調べた版の既定値で、全環境の実測値ではない。[138秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=138s)、[162秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=162s)
4. 翻訳は別途接続した翻訳APIが担当し、元アプリの翻訳エンジンは使っていない。[173秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=173s)
5. 大きな配布物は全部を深掘りせず、必要な2つのスクリプトに絞って解析した。絞り込みが活用のコツ。[214秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=214s)
6. 音声入力は、ローカルの音声認識を用い、合成音声と専用テスト入力欄で確認。入力先が変わると送信を見送る。実マイクから各アプリまでは追加確認が必要。[248秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=248s)
7. 配布物から処理名が分かっても、外部サーバー側のモデルやプロンプトまでは分かるとは限らない。元アプリと同じ精度・速度を再現した結果ではない。[287秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=287s)
8. 「解析で確認」「独自に決定」「未確認」の3分類が、AIへ渡す仕様とテスト内容を具体化する。[297秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=297s)
9. プレゼンターは、音声認識・文章整理・図の構成判断・描画に分割。各段階の出力を比較でき、意味がずれた段階を特定しやすい。[356秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=356s)
10. 文字演出や図への変換は参考元にない独自設計。参考にしたのは音声を受け取り整理して返す流れ。[316秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=316s)
11. ページ単位で保持するため、テンプレートを変えても話し直しは不要。[395秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=395s)
12. マインドマップは公開ビューアーの配布スクリプトと実画面を調べた。左右配置・折りたたみ・編集・出典ページへの移動は独自実装で、元製品の編集機能全体の解析ではない。[474秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=474s)
13. REAの有無で開発速度を比べる実験はしておらず、一発で完成した記録でもない。入力先変更や遅い応答、2回目入力は試して修正した。[563秒](https://www.youtube.com/watch?v=-Psl8jfseDY&t=563s)

## この研究室への応用

- 調査メモを「確認済み／独自設計／未確認」の3列で管理し、実装依頼やテスト項目に直結させる。
- 解析対象は必要箇所に絞り、根拠付きで範囲を限定する習慣を取り入れる。
- 認識・整理・判断・描画のように処理を段階分割し、各段階の中間出力を残して原因切り分けに使う。
- 自分が使う認識モデルや翻訳エンジンに差し替える前提で、操作の流れと失敗条件をAIへ渡す。
- 配布物の解析は、ライセンス・利用規約の確認を前提とする（動画では言及が確認できない）。

## 限界・未確認

- 映像は未確認。本ノートは字幕テキストのみに基づく。
- 字幕は自動生成で、誤変換の可能性がある（例：製品名・用語・「出点／出展」などの表記ゆれ、固有名詞の誤認識）。数値（1000ミリ秒、バージョン1.8.0）も要確認。
- 動画内で名指しされる製品・ツールの正式名称や公式資料との照合はしていない。
- REAの仕様、先行動画の内容、各製品の外部仕様・ライセンス：UNKNOWN。
- 動画内の動作確認結果は投稿者の主張であり、再現確認はしていない。
- 動画が明言する未実施事項：開発速度の比較、実マイクから各アプリまでの一連確認、2回コピー動作の全環境での検証。
