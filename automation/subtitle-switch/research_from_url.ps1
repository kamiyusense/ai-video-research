# AI技術研究室: YouTube URLを渡すだけで「字幕取得 → 字幕原文OKF＋研究ノートOKF作成 → 保存」まで自動実行
# 使い方:  pwsh -File research_from_url.ps1 "https://www.youtube.com/watch?v=XXXXXXXXXXX" [-Writer claude|manual]
#   -Writer claude（既定）: 研究ノートはClaude（Claude Code）が書く
#   -Writer manual        : 字幕原文OKFまで保存して止める（exit 9）。研究ノートは相棒が他のAIに頼み、もう一度実行すると検品・台帳・目次まで仕上げる
# 字幕はGoogle側（字幕取り込み専用Notebook）に取らせる＝自宅回線からYouTubeへ直接アクセスしない。
# 研究室Notebookには書き込まない。認証情報は表示しない。
# 2026-10-25: Antigravity CLI（agy -p）を外のプログラムから呼ぶ方式は規約上のおそれがあるためやめ、書き手をClaudeか手動にした。
param(
    [Parameter(Mandatory = $true)][string]$Url,
    [string]$Vault = "C:\Users\yuuki\Documents\AI動画研究室",
    [string]$Backup = "G:\マイドライブ\AI動画研究室_予備",
    [ValidateSet("claude", "manual")][string]$Writer = "claude",
    [string]$Model = "claude-sonnet-5-5",
    [string]$Effort = "medium",
    [switch]$Force,
    [switch]$NoGitHub
)
$ErrorActionPreference = "Stop"
# どこから起動されても日本語が文字化けしないよう、入出力をUTF-8に固定する
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$uvx = "C:\Users\yuuki\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uvx.exe"
$Tools = $PSScriptRoot
$CaptureNotebook = "15e2893c-1485-4abc-bd70-e4dfef9cb348"   # AI技術研究室_字幕取り込み専用
$Today = Get-Date -Format "yyyy-MM-dd"

function Say($m) { Write-Host "[$(Get-Date -Format HH:mm:ss)] $m" }
function Nlm { & $uvx --from "notebooklm-py[mcp]" notebooklm @args 2>$null | Out-String }
function Sha256([string]$s) { ([System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($s)))).Replace("-", "").ToLower() }
function YamlSafe([string]$s) { ($s -replace '"', '”' -replace "[\r\n]+", " ").Trim() }

# 0. 動画IDを取り出す
$m = [regex]::Match($Url, '(?:v=|youtu\.be/|shorts/|live/|embed/)([A-Za-z0-9_-]{11})')
if ($m.Success) { $vid = $m.Groups[1].Value } elseif ($Url -match '^[A-Za-z0-9_-]{11}$') { $vid = $Url } else { Say "STOP: 動画IDを読み取れません"; exit 2 }
$canon = "https://www.youtube.com/watch?v=$vid"
$trFile = Join-Path $Vault "transcripts\youtube-$vid-transcript.md"
$rnFile = Join-Path $Vault "research\youtube-$vid-research.md"
New-Item -ItemType Directory -Force (Join-Path $Vault "transcripts"), (Join-Path $Vault "research") | Out-Null
Say "動画ID: $vid"

# 1. 重複チェック（①保管庫 ②GitHubの過去の台帳 registry.json＝昔のGeminiルートで研究済みの動画 ③GitHub自動保存の台帳）
# 字幕・研究ノート・台帳の行がそろっていれば保存済み。台帳に行が無ければ、手動で書いた研究ノートの仕上げ待ち
$regPath = Join-Path $Vault "registry.json"
$reg = @(); if (Test-Path $regPath) { $reg = @(Get-Content $regPath -Raw -Encoding utf8 | ConvertFrom-Json) }
$inReg = @($reg | Where-Object { $_.video_id -eq $vid }).Count -gt 0
if ((Test-Path $trFile) -and (Test-Path $rnFile) -and $inReg -and -not $Force) { Say "SKIP: この動画は保存済みです（$vid）"; exit 0 }
# 字幕原文OKFが既にあれば字幕は取り直さない（研究ノート待ち・仕上げ待ちの続きから）
$reuse = (Test-Path $trFile) -and -not $Force
if (-not $reuse) {
$repo = Join-Path $Tools "ai-video-research-fix"
$oldBranch = "feature/gemini-notebook-research-loop-20261016"
try {
    & git.exe -C $repo fetch -q origin $oldBranch 2>$null
    $oldReg = (& git.exe -C $repo show "origin/${oldBranch}:registry.json" 2>$null | Out-String | ConvertFrom-Json).records
    $hit = @($oldReg | Where-Object { $_.video_id -eq $vid -or $_.record_id -eq "youtube:$vid" })
    if ($hit.Count -gt 0 -and -not $Force) { Say "SKIP: 過去に研究済みです（GitHubの台帳に登録あり: $($hit[0].research_path)）。やり直すなら -Force"; exit 0 }
    if ($oldReg) { Say "過去の台帳照合OK（$(@($oldReg).Count)件と照合・未登録）" }
} catch { Say "WARN: GitHubの過去台帳を照合できませんでした（ネットワーク等）。保管庫の照合のみで続行します" }

# 1.5 動画の投稿日時・チャンネル・長さ（yt-dlpで動画情報だけ1回取得。字幕はここでは取らない。失敗してもUNKNOWNで続行）
$ytdlp = Join-Path $Tools "video-fetcher-to-markdown\.venv\Scripts\yt-dlp.exe"
$pubAt = "UNKNOWN"; $pubDate = "UNKNOWN"; $channel = "UNKNOWN"; $duration = "UNKNOWN"
try {
    $meta = (& $ytdlp --js-runtimes node --skip-download --no-warnings --print "%(upload_date)s|%(timestamp)s|%(channel)s|%(duration)s" $canon 2>$null | Select-Object -Last 1)
    $p = "$meta".Split("|")
    if ($p.Count -ge 4 -and $p[0] -match '^\d{8}$') {
        $pubDate = "{0}-{1}-{2}" -f $p[0].Substring(0, 4), $p[0].Substring(4, 2), $p[0].Substring(6, 2)
        if ($p[1] -match '^\d+$') { $pubAt = [DateTimeOffset]::FromUnixTimeSeconds([long]$p[1]).ToOffset([TimeSpan]::FromHours(9)).ToString("yyyy-MM-ddTHH:mm:sszzz") }
        $channel = YamlSafe $p[2]; if ($p[3] -match '^\d+$') { $duration = $p[3] }
    }
} catch {}
Say "投稿日: $pubDate / チャンネル: $channel"

# 2. ログイン確認（切れていたら1回だけログインし直し）
& (Join-Path $Tools "ensure_notebook_login.ps1")
if ($LASTEXITCODE -ne 0) { Say "STOP: Notebookにログインできません。相棒の操作が必要です"; exit 3 }

# 3. 字幕取り込み専用Notebookに登録（既にあれば再利用＝重複登録しない）
$list = (Nlm source list -n $CaptureNotebook --json | ConvertFrom-Json).sources
$src = $list | Where-Object { $_.url -and $_.url -match [regex]::Escape($vid) } | Select-Object -First 1
if ($src) { Say "字幕取り込みNotebookに登録済み → 再利用 ($($src.id))"; $sid = $src.id }
else {
    Say "字幕取り込みNotebookへ登録中…"
    $add = Nlm source add $canon --type youtube -n $CaptureNotebook --json | ConvertFrom-Json
    $sid = if ($add.source) { $add.source.id } else { $add.id }
    if (-not $sid) { Say "STOP: 登録に失敗しました"; exit 4 }
}
$wait = Nlm source wait $sid -n $CaptureNotebook --timeout 300 --interval 5 --json | ConvertFrom-Json
if ($wait.status -ne "ready") { Say "STOP: 字幕の取り込みが完了しません（状態: $($wait.status)）。字幕が無い動画の可能性"; exit 5 }
$title = YamlSafe $wait.title

# 4. 字幕本文を読み出す
$tmp = Join-Path $env:TEMP "nlm_$vid.txt"
Nlm source fulltext $sid -n $CaptureNotebook -o $tmp --force --json | Out-Null
$body = (Get-Content $tmp -Raw -Encoding utf8).Trim()
Remove-Item $tmp -Force -ErrorAction SilentlyContinue
if ($body.Length -lt 200) { Say "STOP: 字幕が短すぎます（$($body.Length)文字）。字幕が無い動画の可能性"; exit 6 }
$sha = Sha256 $body
Say "字幕取得OK: $($body.Length)文字"

# 5. 字幕原文OKFを保存（AIを使わず機械的に作成）
$fm = @"
---
okf_version: "0.2"
type: "TRANSCRIPT"
title: "【字幕原文】$title [$vid]"
description: "YouTube動画 $vid の字幕原文（Googleが取り込んだ字幕テキスト）。要約・加工なし。"
resource: "$canon"
tags:
  - "AI技術研究室"
  - "字幕原文"
logical_id: "youtube:${vid}:transcript"
record_id: "youtube:$vid"
video_id: "$vid"
canonical_url: "$canon"
published_date: "$pubDate"
published_at: "$pubAt"
channel: "$channel"
duration_seconds: "$duration"
metadata_source: "yt-dlp（YouTubeの動画情報）"
captured_at: "$Today"
capture_route: "字幕取り込み専用Notebook（$CaptureNotebook）のYouTubeソース（$sid）の保存本文を読み出し"
timestamps: "NONE（取り込み経路に時刻情報が無い）"
char_count: $($body.Length)
sha256: "$sha"
transcript_status: "CAPTURED_NO_TIMESTAMPS"
related_records:
  - target_id: "youtube:${vid}:research"
    relation: "SOURCE_OF"
    note: "本字幕を元に作成した研究ノート"
storage_policy: "ローカル保管のみ。GitHubへの保存禁止（字幕全文）"
---

# 【字幕原文】$title [$vid]

> 本ファイルは字幕原文（一次資料）です。研究ノート: [[youtube-$vid-research]]（logical_id: youtube:${vid}:research）

## 字幕原文

"@
Set-Content -LiteralPath $trFile -Value ($fm + $body + "`n") -Encoding utf8
Say "字幕原文OKFを保存: $trFile"
} else {
    # 保存済みの字幕原文OKFから、字幕本文と荷札の値を読み戻す（指紋が合わなければ止める）
    $tr = Get-Content $trFile -Raw -Encoding utf8
    function FmVal([string]$name) { $mm = [regex]::Match($tr, '(?m)^' + $name + ': "?(.*?)"?\r?$'); if ($mm.Success) { $mm.Groups[1].Value } else { "UNKNOWN" } }
    $tm = [regex]::Match($tr, '(?m)^title: "【字幕原文】(.*) \[' + [regex]::Escape($vid) + '\]"\r?$')
    $title = if ($tm.Success) { $tm.Groups[1].Value } else { "UNKNOWN" }
    $pubDate = FmVal "published_date"; $pubAt = FmVal "published_at"; $channel = FmVal "channel"; $duration = FmVal "duration_seconds"
    $sha = FmVal "sha256"
    $sm = [regex]::Match($tr, 'のYouTubeソース（([^）]*)）'); $sid = if ($sm.Success) { $sm.Groups[1].Value } else { "UNKNOWN" }
    $bm = [regex]::Match($tr, '(?s)\n## 字幕原文\r?\n(.*)$')
    $body = $bm.Groups[1].Value.Trim()
    if (-not $bm.Success -or (Sha256 $body) -ne $sha) { Say "STOP: 保存済みの字幕原文OKFが読めないか、指紋が合いません（$trFile）"; exit 6 }
    Say "字幕原文OKFは保存済み → 字幕は取り直さず続きから（$($body.Length)文字）"
}

# 6. 研究ノートOKF（書き手: claude＝Claudeが書く／manual＝ここで止めて相棒が他のAIに頼む）
if ((Test-Path $rnFile) -and $Force) { Move-Item $rnFile "$rnFile.old-$(Get-Date -Format yyyyMMddHHmmss)" }
$wrote = $false
if (-not (Test-Path $rnFile)) {
    if ($Writer -eq "manual") { Say "WAIT_MANUAL: 字幕原文OKFまで保存して停止。研究ノートは手動で作成してください（$rnFile）"; exit 9 }
    $prompt = (Get-Content (Join-Path $Tools "research_note_prompt_template.md") -Raw -Encoding utf8).
        Replace("{VIDEO_ID}", $vid).Replace("{TITLE}", $title).Replace("{SHA256}", $sha).Replace("{DATE}", $Today).Replace("{CREATED_BY}", "Claude Code ($Model)")
    Say "研究ノートをClaudeで作成中…（1〜3分）"
    # 公式CLIを1回だけ実行。使える道具はファイルの読み書きだけ（コマンド実行・ネット検索なし）、書き込みは保管庫の中だけ自動許可
    Push-Location $Vault
    try { $res = $prompt | & claude -p --model $Model --effort $Effort --permission-mode acceptEdits --tools Read Write Glob Grep --output-format json 2>$null | Out-String } finally { Pop-Location }
    if (-not (Test-Path $rnFile)) { Say "STOP: 研究ノートが作成されませんでした"; exit 7 }
    $wrote = $true
} else { Say "研究ノートは作成済み → 検品・台帳・目次の仕上げへ" }
# 研究ノートの荷札にも投稿日時を機械的に追記（AIに任せず正確に入れる）
$rnText = Get-Content $rnFile -Raw -Encoding utf8
if ($rnText -notmatch '(?m)^published_date:') {
    $ins = "video_id: `"$vid`"`npublished_date: `"$pubDate`"`npublished_at: `"$pubAt`"`nchannel: `"$channel`"`nduration_seconds: `"$duration`""
    $rnText = [regex]::Replace($rnText, '(?m)^video_id: "' + [regex]::Escape($vid) + '"\r?$', $ins, 1)
    Set-Content -LiteralPath $rnFile -Value $rnText -Encoding utf8 -NoNewline
}

# 7. 検品（荷札・指紋・引用の実在）
$rn = Get-Content $rnFile -Raw -Encoding utf8
$checks = [ordered]@{
    "OKF荷札"        = $rn.StartsWith("---") -and $rn.Contains('type: "RESEARCH_NOTE"')
    "論理ID"         = $rn.Contains("youtube:${vid}:research")
    "字幕へのリンク" = $rn.Contains("youtube:${vid}:transcript")
    "字幕の指紋一致" = $rn.Contains($sha)
}
$sec = [regex]::Match($rn, '(?s)## 重要な知見(.*?)(\n## |\z)').Groups[1].Value   # 根拠の引用は「重要な知見」の各行末だけを照合
$quotes = [regex]::Matches($sec, '「([^」]{2,40})」\s*$', 'Multiline') | ForEach-Object { $_.Groups[1].Value } | Where-Object { $_ -match ' ' }
$bodyNs = $body -replace '\s', ''   # 字幕は単語ごとに空白区切り。空白の位置違いは同じ言葉とみなす
$found = @($quotes | Where-Object { $bodyNs.Contains(($_ -replace '\s', '')) }).Count
$total = @($quotes).Count
$okAll = -not ($checks.Values -contains $false)
foreach ($k in $checks.Keys) { Say ("検品 {0}: {1}" -f $k, $(if ($checks[$k]) { "OK" } else { "NG" })) }
Say "検品 引用の実在: $found / $total"

# 8. 台帳に記録（保管庫内 registry.json）
$reg = @($reg | Where-Object { $_.video_id -ne $vid })
$noteModel = if ($wrote) { $Model } else { "manual" }
$reg += [pscustomobject]@{
    video_id = $vid; title = $title; url = $canon; published_date = $pubDate; published_at = $pubAt; channel = $channel; duration_seconds = $duration; processed_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
    transcript_file = "transcripts/youtube-$vid-transcript.md"; research_file = "research/youtube-$vid-research.md"
    transcript_chars = $body.Length; transcript_sha256 = $sha; capture_source_id = $sid
    checks_passed = $okAll; quotes_found = "$found/$total"; model = $noteModel
}
ConvertTo-Json @($reg) -Depth 4 | Set-Content -LiteralPath $regPath -Encoding utf8
$status = if ($okAll -and $found -eq $total) { "SUCCESS" } else { "PARTIAL（検品で要確認あり）" }
Say "完了: $status"

# 9. Googleドライブへ予備コピー（追加・更新のみ。予備側のファイルは消さない。Obsidianの設定フォルダは除外）
# 2026-10-21 相棒の選択「1」：Googleドライブ公式の同期機能で保管庫を同期するため、ここでのコピーは無効化（-Backup指定時のみ実行）
if ($PSBoundParameters.ContainsKey("Backup")) { & (Join-Path $Tools "backup_vault.ps1") -Vault $Vault -Backup $Backup }

# 9.5 目次（00_目次.md）を台帳から作り直す（研究のたびに最新の一覧にする）
try {
    $reg = @(Get-Content $regPath -Raw -Encoding utf8 | ConvertFrom-Json) | Sort-Object published_date -Descending
    $L = @("# AI動画研究室 目次", "", "研究済み（正式保存）: $($reg.Count) 本　／　最終更新: $(Get-Date -Format 'yyyy-MM-dd HH:mm')", "", "> 投稿日の新しい順。投稿日・チャンネルはYouTube本体の情報。", "", "| 投稿日 | 動画 | チャンネル | 研究ノート | 字幕原文 |", "|---|---|---|---|---|")
    foreach ($x in $reg) { $t = ($x.title -replace '\|', '｜'); $L += "| $($x.published_date) | $t | $($x.channel) | [[youtube-$($x.video_id)-research]] | [[youtube-$($x.video_id)-transcript]] |" }
    Set-Content -LiteralPath (Join-Path $Vault "00_目次.md") -Value ($L -join "`n") -Encoding utf8
    Say "目次を更新（$($reg.Count)本）"
} catch { Say "WARN: 目次の更新に失敗（研究ノートは保存済み）" }

# 10. 研究ノートと台帳だけをGitHubの専用ブランチへ自動保存（字幕原文は送らない。-NoGitHub で省略）
if (-not $NoGitHub) {
    $env:GIT_TERMINAL_PROMPT = "0"
    & (Join-Path $Tools "publish_to_github.ps1") -Vault $Vault
    if ($LASTEXITCODE -ne 0) { Say "WARN: GitHub保存に失敗（PC・ドライブには保存済み）"; exit 8 }
}
exit 0
