# AI技術研究室 | Q&A・動画検索ランチャー
# 使い方:
#   .\run_qa.ps1               -> 対話モード起動
#   .\run_qa.ps1 "質問文"       -> 単発質問実行

param (
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string]$Query
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "automation\gemini-notebook\query_research.py"

if (-not (Test-Path $PythonScript)) {
    Write-Error "検索スクリプトが見つかりません: $PythonScript"
    exit 1
}

# Python実行可能ファイルの検出
$PythonCmd = "py"
if (-not (Get-Command "py" -ErrorAction SilentlyContinue)) {
    $PythonCmd = "python"
}

if ([string]::IsNullOrWhiteSpace($Query)) {
    & $PythonCmd -3 $PythonScript -i
} else {
    & $PythonCmd -3 $PythonScript -q "$Query"
}
