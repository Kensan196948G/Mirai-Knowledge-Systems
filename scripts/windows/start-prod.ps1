# ============================================================
# Mirai Knowledge Systems - Windows本番環境起動スクリプト
# ============================================================
#
# 使用方法:
#   .\scripts\windows\start-prod.ps1 [オプション]
#
# オプション:
#   -Force         確認をスキップして起動
#   -Workers N     ワーカー数を指定（デフォルト: CPU数 * 2 + 1）
#   -Help          ヘルプ表示
#
# ポート番号:
#   HTTP:  8100 (固定)
#   HTTPS: 8443 (固定)
#
# ⚠️ 警告: 本番環境です。設定を確認してから起動してください。
#
# ============================================================

param(
    [switch]$Force,
    [int]$Workers = 0,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# ポート番号（固定）
$HTTP_PORT = 8100
$HTTPS_PORT = 8443

# プロジェクトルートを取得
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item "$ScriptDir\..\..").FullName

# ヘルプ表示
function Show-Help {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Mirai Knowledge Systems - 本番環境起動スクリプト" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "使用方法: .\start-prod.ps1 [オプション]"
    Write-Host ""
    Write-Host "オプション:"
    Write-Host "  -Force         確認をスキップして起動"
    Write-Host "  -Workers N     ワーカー数を指定（デフォルト: CPU数 * 2 + 1）"
    Write-Host "  -Help          このヘルプを表示"
    Write-Host ""
    Write-Host "ポート番号（固定）:"
    Write-Host "  HTTP:  $HTTP_PORT"
    Write-Host "  HTTPS: $HTTPS_PORT"
    Write-Host ""
    Write-Host "⚠️ 注意: 本番環境では以下を確認してください:"
    Write-Host "  - MKS_SECRET_KEY が安全なランダム値に設定されていること"
    Write-Host "  - MKS_JWT_SECRET_KEY が安全なランダム値に設定されていること"
    Write-Host "  - DATABASE_URL がPostgreSQLの接続情報を指していること"
    Write-Host "  - SSL証明書が正しく配置されていること"
    Write-Host ""
    exit 0
}

if ($Help) {
    Show-Help
}

Write-Host "============================================================" -ForegroundColor Red
Write-Host "  Mirai Knowledge Systems - 本番環境起動" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""
Write-Host "⚠️ 警告: 本番環境モードで起動します" -ForegroundColor Yellow
Write-Host ""

# 確認プロンプト
if (-not $Force) {
    Write-Host "本番環境で起動しますか？ (y/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "[CANCELLED] " -ForegroundColor Yellow -NoNewline
        Write-Host "起動をキャンセルしました"
        exit 0
    }
}

# 環境変数設定
$env:MKS_ENV = "production"
$env:MKS_HTTP_PORT = $HTTP_PORT
$env:MKS_HTTPS_PORT = $HTTPS_PORT
$env:MKS_DEBUG = "false"
$env:MKS_LOAD_SAMPLE_DATA = "false"
$env:MKS_CREATE_DEMO_USERS = "false"
$env:MKS_FORCE_HTTPS = "true"
$env:MKS_USE_POSTGRESQL = "true"

# .env.production を読み込み
$EnvFile = Join-Path $ProjectRoot "envs\production\.env.production"
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
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host "本番環境設定ファイルが見つかりません: $EnvFile"
    Write-Host "       envs/production/.env.production を作成してください"
    exit 1
}

# 必須環境変数のチェック
$requiredVars = @("MKS_SECRET_KEY", "MKS_JWT_SECRET_KEY", "DATABASE_URL")
$missingVars = @()

foreach ($var in $requiredVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if (-not $value -or $value -match "CHANGE_THIS") {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host "以下の必須環境変数が未設定または安全でない値です:"
    foreach ($var in $missingVars) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "envs/production/.env.production を編集して設定してください"
    exit 1
}

# SSL証明書の確認
$SslCert = Join-Path $ProjectRoot "ssl\server.crt"
$SslKey = Join-Path $ProjectRoot "ssl\server.key"

if (-not (Test-Path $SslCert) -or -not (Test-Path $SslKey)) {
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host "SSL証明書が見つかりません"
    Write-Host "  証明書: $SslCert"
    Write-Host "  秘密鍵: $SslKey"
    Write-Host ""
    Write-Host "HTTPS通信にはSSL証明書が必要です"
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

# ワーカー数の設定
if ($Workers -eq 0) {
    $Workers = ([Environment]::ProcessorCount * 2) + 1
}
$env:GUNICORN_WORKERS = $Workers

# 起動情報表示
Write-Host ""
Write-Host "============================================================" -ForegroundColor Red
Write-Host "  起動設定 [本番環境]" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host "  環境モード:   本番 (production)" -ForegroundColor Red
Write-Host "  HTTP ポート:  $HTTP_PORT" -ForegroundColor White
Write-Host "  HTTPS ポート: $HTTPS_PORT" -ForegroundColor White
Write-Host "  ワーカー数:   $Workers" -ForegroundColor White
Write-Host "  デバッグ:     無効" -ForegroundColor Gray
Write-Host "  サンプルデータ: 無効" -ForegroundColor Gray
Write-Host "  デモユーザー:   無効" -ForegroundColor Gray
Write-Host "  PostgreSQL:     有効" -ForegroundColor Green
Write-Host "  HTTPS強制:      有効" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""
Write-Host "アクセスURL:" -ForegroundColor Cyan
Write-Host "  HTTP:  http://192.168.0.187:$HTTP_PORT (リダイレクト)" -ForegroundColor White
Write-Host "  HTTPS: https://192.168.0.187:$HTTPS_PORT" -ForegroundColor Green
Write-Host ""

# Gunicornで起動（Windowsではwaitressまたはwerkzeug使用を推奨）
# Windows環境でのgunicornは制限があるため、代替手段を提案
Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
Write-Host "Windows環境での本番起動..."
Write-Host ""
Write-Host "⚠️ 注意: WindowsではGunicornの代わりにWaitressの使用を推奨します" -ForegroundColor Yellow
Write-Host "   pip install waitress" -ForegroundColor Gray
Write-Host "   waitress-serve --port=$HTTP_PORT app_v2:app" -ForegroundColor Gray
Write-Host ""

# Pythonで直接起動（開発用WSGIサーバー）
Write-Host "Flaskの開発サーバーで起動します（本番環境ではWaitress推奨）" -ForegroundColor Yellow
Write-Host ""

python app_v2.py
