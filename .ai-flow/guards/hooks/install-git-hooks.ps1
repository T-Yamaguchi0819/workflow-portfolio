# ai-dev-flow: git pre-commit フックのインストーラ（Windows / PowerShell 5.1+）
# 使い方:
#   .\install-git-hooks.ps1                  # カレントのプロジェクトルート配下の repos（guard-rules.json）へ導入
#   .\install-git-hooks.ps1 -Repo <path>     # 指定リポジトリへ導入（複数回実行可）
#   .\install-git-hooks.ps1 -Force           # 既存の pre-commit を上書き
param(
    [string]$Repo = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$guardsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$verifyDiff = Join-Path (Split-Path -Parent $guardsDir) "verify_diff.py"
$template = Join-Path $guardsDir "pre-commit"

if (-not (Test-Path $verifyDiff)) { Write-Error "verify_diff.py が見つかりません: $verifyDiff" }
if (-not (Test-Path $template)) { Write-Error "pre-commit テンプレートが見つかりません: $template" }

# 対象リポジトリの決定
$repos = @()
if ($Repo -ne "") {
    $repos += (Resolve-Path $Repo).Path
} else {
    # guard-rules.json の repos（プロジェクトルート相対）を使う
    $projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $guardsDir))
    $rules = Get-Content (Join-Path (Split-Path -Parent $guardsDir) "guard-rules.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($r in $rules.repos) {
        $repos += (Resolve-Path (Join-Path $projectRoot $r)).Path
    }
}

# フック本文の生成（パス埋め込み。git hooks は sh で動くためスラッシュ区切りに変換）
$verifyDiffSh = $verifyDiff -replace "\\", "/"
$hookBody = (Get-Content $template -Raw -Encoding UTF8) -replace "__VERIFY_DIFF_PATH__", $verifyDiffSh

foreach ($repoPath in $repos) {
    if (-not (Test-Path (Join-Path $repoPath ".git"))) {
        Write-Warning "git リポジトリではないためスキップ: $repoPath"
        continue
    }
    $hookPath = Join-Path $repoPath ".git\hooks\pre-commit"
    if ((Test-Path $hookPath) -and (-not $Force)) {
        $existing = Get-Content $hookPath -Raw -Encoding UTF8
        if ($existing -match "ai-dev-flow") {
            Write-Host "更新: $hookPath"
        } else {
            Write-Warning "既存の pre-commit が存在します（ai-dev-flow 以外）: $hookPath"
            Write-Warning "  手動でマージするか、-Force で上書きしてください。スキップします。"
            continue
        }
    } else {
        Write-Host "導入: $hookPath"
    }
    # sh が読むため改行 LF・BOM なしで書き出す
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($hookPath, ($hookBody -replace "`r`n", "`n"), $utf8NoBom)
}
Write-Host "完了。動作確認: 対象リポジトリで禁止パターンを含む変更を git commit してブロックされることを確認してください。"
