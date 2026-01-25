# ============================================================
# Mirai Knowledge Systems - Windows開発環境起動スクリプト
# ============================================================
#
# 使用方法:
#   .\scripts\windows\start-dev.ps1 [オプション]
#
# オプション:
#   -Background    バックグラウンドで起動
#   -Debug         デバッグモード有効
#   -Help          ヘルプ表示
#
# ポート番号:
#   HTTP:  5100 (固定)
#   HTTPS: 5443 (固定)
#
# ============================================================

param(
    [switch]$Background,
    [switch]$Debug,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# カラー定義
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Cyan = "Cyan"
    White = "White"
}

# ポート番号（固定）
$HTTP_PORT = 5100
$HTTPS_PORT = 5443

# プロジェクトルートを取得
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item "$ScriptDir\..\..").FullName

# ヘルプ表示
function Show-Help {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Mirai Knowledge Systems - 開発環境起動スクリプト" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "使用方法: .\start-dev.ps1 [オプション]"
    Write-Host ""
    Write-Host "オプション:"
    Write-Host "  -Background    バックグラウンドで起動"
    Write-Host "  -Debug         デバッグモード有効（デフォルト）"
    Write-Host "  -Help          このヘルプを表示"
    Write-Host ""
    Write-Host "ポート番号（固定）:"
    Write-Host "  HTTP:  $HTTP_PORT"
    Write-Host "  HTTPS: $HTTPS_PORT"
    Write-Host ""
    exit 0
}

if ($Help) {
    Show-Help
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Mirai Knowledge Systems - 開発環境起動" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 環境変数設定
$env:MKS_ENV = "development"
$env:MKS_HTTP_PORT = $HTTP_PORT
$env:MKS_HTTPS_PORT = $HTTPS_PORT
$env:MKS_DEBUG = "true"
$env:MKS_LOAD_SAMPLE_DATA = "true"
$env:MKS_CREATE_DEMO_USERS = "true"
$env:MKS_FORCE_HTTPS = "false"

# .env.development を読み込み
$EnvFile = Join-Path $ProjectRoot "envs\development\.env.development"
if (Test-Path $EnvFile) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host "環境設定ファイルを読み込み: $EnvFile"

    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
} else {
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host "環境設定ファイルが見つかりません: $EnvFile"
}

# プロジェクトルートに移動
Set-Location $ProjectRoot

# 仮想環境の有効化
$VenvPath = Join-Path $ProjectRoot "venv_windows"
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"

if (Test-Path $VenvActivate) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host "Python仮想環境を有効化: $VenvPath"
    & $VenvActivate
} else {
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host "Python仮想環境が見つかりません: $VenvPath"
    Write-Host "       システムのPythonを使用します"
}

# backendディレクトリに移動
$BackendDir = Join-Path $ProjectRoot "backend"
Set-Location $BackendDir

# 起動情報表示
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  起動設定" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  環境モード:   開発 (development)" -ForegroundColor Green
Write-Host "  HTTP ポート:  $HTTP_PORT" -ForegroundColor White
Write-Host "  HTTPS ポート: $HTTPS_PORT" -ForegroundColor White
Write-Host "  デバッグ:     有効" -ForegroundColor Green
Write-Host "  サンプルデータ: 有効" -ForegroundColor Green
Write-Host "  デモユーザー:   有効" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "アクセスURL:" -ForegroundColor Cyan
Write-Host "  HTTP:  http://localhost:$HTTP_PORT" -ForegroundColor White
Write-Host "  HTTPS: https://localhost:$HTTPS_PORT" -ForegroundColor White
Write-Host ""
Write-Host "停止するには Ctrl+C を押してください" -ForegroundColor Yellow
Write-Host ""

# アプリケーション起動
if ($Background) {
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host "バックグラウンドで起動中..."

    $Job = Start-Job -ScriptBlock {
        param($BackendDir)
        Set-Location $BackendDir
        python app_v2.py
    } -ArgumentList $BackendDir

    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host "バックグラウンドジョブID: $($Job.Id)"
    Write-Host "  停止: Stop-Job -Id $($Job.Id)"
    Write-Host "  ログ: Receive-Job -Id $($Job.Id)"
} else {
    python app_v2.py
}
