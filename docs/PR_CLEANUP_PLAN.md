# 下書きPR整理案（2026-10-21 作成・案のみ。Merge／閉じる操作は未実行）

## 現状（GitHub実測）
- PR 14個。mainに入ったものは0個（#12は閉じただけ）。開いている下書きは12個。main は初期コミットのみ。
- PRは積み木状に連なる。矢印は「このPRの土台（base）の枝」。

```
#1 setup/research-lab → main
 ├ #2 kickoff-bottleneck → #1
 └ #3 video05 → #1
     └ #4 video06 → #3
         ├ #5 video07 → #4
         ├ #6 reusable-agent-team-starter → #4
         │    └ #9 staged-video-handoff → #6
         │         └ #10 gemini-notebook-research-loop → #9
         │              ├ #11 claude-jules-loop-port → #10
         │              └ #13 検品ループ運用 → #10
         │                   └ #14 notebooklm-py 道具・ロードマップ → #13
         └ #7 cognitive-drift → #4
              └ #8 video08 → #7
```

## 案A（おすすめ）: 上の積み木から順にMergeして、最後に #1 を main へ
下から順に畳むと衝突が多いので、**先端（#14）から根元（#1）へ**、各PRを土台の枝へMergeする。
1. #14 → #13 の枝、#13 → #10 の枝、#11 → #10 の枝、#10 → #9 の枝、#9 → #6 の枝、#6 → #4 の枝
2. #8 → #7 の枝、#7 → #4 の枝、#5 → #4 の枝
3. #4 → #3 の枝、#3 → #1 の枝、#2 → #1 の枝
4. 最後に #1 → main（ここで初めてmainが変わる）
- 事前確認: 各段で衝突（特に registry.json・README.md・RESEARCH_ROADMAP.md）を検査し、衝突は「新しい側を正」で解決しテスト全件OKを確認。
- 注意: 先端の枝（requirements-alignment／project-thread 系）には、side枝にしかない次のファイルが無い可能性がある。Merge時に取り込む:
  video07（proposals/008、research/2026-10-10-BStkW1HTfmk…）、cognitive-drift／video08（notes/cognitive-drift…、research/2026-10-10-3bLrrkA1nlQ…、…ZjUJ-35acaU…）、kickoff（proposals/005）。

## 案B: 新しい1本のPRにまとめる
先端の枝へ side枝（#2・#5・#7・#8・#11）を取り込んで、`main ← 先端` の1本のPRを新規作成。古いPRは「統合済み」とコメントして閉じる。Merge回数は少ないが、古いPRの履歴は閉じる。

## どちらでも必要な相棒の許可
- main へ入れる操作（Merge）と、古いPRを閉じる操作は、相棒本人の許可が出るまで実行しない。
- 研究ノートの追加（Notebook側）や課金・権限変更は含まない。
