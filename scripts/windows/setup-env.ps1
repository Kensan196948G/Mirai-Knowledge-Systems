# ============================================================
# Mirai Knowledge Systems - Windows環境セットアップスクリプト
# ============================================================
#
# 使用方法:
#   .\scripts\windows\setup-env.ps1 [オプション]
#
# オプション:
#   -Environment [dev|prod]  環境タイプ（デフォルト: dev）
#   -Force                   既存の仮想環境を再作成
#   -SkipVenv                仮想環境の作成をスキップ
#   -Help                    ヘルプ表示
#
# ============================================================

param(
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",
    [switch]$Force,
    [switch]$SkipVenv,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# プロジェクトルートを取得
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item "$ScriptDir\..\..").FullName

# ヘルプ表示
function Show-Help {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Mirai Knowledge Systems - 環境セットアップ" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "使用方法: .\setup-env.ps1 [オプション]"
    Write-Host ""
    Write-Host "オプション:"
    Write-Host "  -Environment [dev|prod]  環境タイプ（デフォルト: dev）"
    Write-Host "  -Force                   既存の仮想環境を再作成"
    Write-Host "  -SkipVenv                仮想環境の作成をスキップ"
    Write-Host "  -Help                    このヘルプを表示"
    Write-Host ""
    Write-Host "例:"
    Write-Host "  .\setup-env.ps1                    # 開発環境をセットアップ"
    Write-Host "  .\setup-env.ps1 -Environment prod # 本番環境をセットアップ"
    Write-Host "  .\setup-env.ps1 -Force            # 仮想環境を再作成"
    Write-Host ""
    exit 0
}

if ($Help) {
    Show-Help
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Mirai Knowledge Systems - 環境セットアップ" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "環境タイプ: $Environment" -ForegroundColor White
Write-Host "プロジェクトルート: $ProjectRoot" -ForegroundColor White
Write-Host ""

# Python確認
Write-Host "[STEP 1] " -ForegroundColor Cyan -NoNewline
Write-Host "Pythonの確認..."

try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host "Python: $pythonVersion"
} catch {
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host "Pythonが見つかりません。インストールしてください。"
    Write-Host "  https://www.python.org/downloads/"
    exit 1
}

# Node.js確認
Write-Host ""
Write-Host "[STEP 2] " -ForegroundColor Cyan -NoNewline
Write-Host "Node.jsの確認..."

try {
    $nodeVersion = node --version 2>&1
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host "Node.js: $nodeVersion"
} catch {
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host "Node.jsが見つかりません。フロントエンドテストには必要です。"
    Write-Host "  https://nodejs.org/"
}

# 仮想環境の作成
Write-Host ""
Write-Host "[STEP 3] " -ForegroundColor Cyan -NoNewline
Write-Host "Python仮想環境の作成..."

$VenvPath = Join-Path $ProjectRoot "venv_windows"

if (-not $SkipVenv) {
    if ((Test-Path $VenvPath) -and -not $Force) {
        Write-Host "[SKIP] " -ForegroundColor Yellow -NoNewline
        Write-Host "仮想環境が既に存在します: $VenvPath"
        Write-Host "       再作成するには -Force オプションを使用してください"
    } else {
        if ((Test-Path $VenvPath) -and $Force) {
            Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
            Write-Host "既存の仮想環境を削除中..."
            Remove-Item -Recurse -Force $VenvPath
        }

        Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
        Write-Host "仮想環境を作成中..."
        python -m venv $VenvPath

        Write-Host "[OK] " -ForegroundColor Green -NoNewline
        Write-Host "仮想環境を作成しました: $VenvPath"
    }

    # 仮想環境を有効化
    $VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $VenvActivate) {
        & $VenvActivate
        Write-Host "[OK] " -ForegroundColor Green -NoNewline
        Write-Host "仮想環境を有効化しました"
    }
} else {
    Write-Host "[SKIP] " -ForegroundColor Yellow -NoNewline
    Write-Host "仮想環境の作成をスキップしました"
}

# Python依存関係のインストール
Write-Host ""
Write-Host "[STEP 4] " -ForegroundColor Cyan -NoNewline
Write-Host "Python依存関係のインストール..."

$RequirementsFile = Join-Path $ProjectRoot "backend\requirements.txt"

if (Test-Path $RequirementsFile) {
    pip install --upgrade pip
    pip install -r $RequirementsFile
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host "Python依存関係をインストールしました"
} else {
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host "requirements.txt が見つかりません: $RequirementsFile"
}

# Windows用追加パッケージ（Waitress）
Write-Host ""
Write-Host "[STEP 5] " -ForegroundColor Cyan -NoNewline
Write-Host "Windows用追加パッケージのインストール..."

pip install waitress
Write-Host "[OK] " -ForegroundColor Green -NoNewline
Write-Host "Waitress（Windows用WSGIサーバー）をインストールしました"

# node_modulesのセットアップ
Write-Host ""
Write-Host "[STEP 6] " -ForegroundColor Cyan -NoNewline
Write-Host "Node.js依存関係のセットアップ..."

$WebuiDir = Join-Path $ProjectRoot "webui"
$NodeModulesWin = Join-Path $ProjectRoot "node_modules.windows"
$NodeModulesLink = Join-Path $WebuiDir "node_modules"

if (Test-Path (Join-Path $WebuiDir "package.json")) {
    # Windows用node_modulesディレクトリを作成
    if (-not (Test-Path $NodeModulesWin)) {
        New-Item -ItemType Directory -Path $NodeModulesWin -Force | Out-Null
    }

    # シンボリックリンクの作成（管理者権限が必要な場合がある）
    if (Test-Path $NodeModulesLink) {
        Remove-Item $NodeModulesLink -Force -Recurse -ErrorAction SilentlyContinue
    }

    try {
        New-Item -ItemType Junction -Path $NodeModulesLink -Target $NodeModulesWin -Force | Out-Null
        Write-Host "[OK] " -ForegroundColor Green -NoNewline
        Write-Host "node_modulesジャンクションを作成しました"
    } catch {
        Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
        Write-Host "ジャンクションの作成に失敗しました（管理者権限が必要かもしれません）"
    }

    # npm installを実行
    Set-Location $WebuiDir
    npm install
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host "Node.js依存関係をインストールしました"
    Set-Location $ProjectRoot
} else {
    Write-Host "[SKIP] " -ForegroundColor Yellow -NoNewline
    Write-Host "package.jsonが見つかりません"
}

# 環境設定ファイルの確認
Write-Host ""
Write-Host "[STEP 7] " -ForegroundColor Cyan -NoNewline
Write-Host "環境設定ファイルの確認..."

if ($Environment -eq "dev") {
    $EnvFile = Join-Path $ProjectRoot "envs\development\.env.development"
} else {
    $EnvFile = Join-Path $ProjectRoot "envs\production\.env.production"
}

if (Test-Path $EnvFile) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host "環境設定ファイルが存在します: $EnvFile"
} else {
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host "環境設定ファイルが見つかりません: $EnvFile"
    Write-Host "       テンプレートからコピーして設定してください"
}

# SSL証明書の確認（本番環境のみ）
if ($Environment -eq "prod") {
    Write-Host ""
    Write-Host "[STEP 8] " -ForegroundColor Cyan -NoNewline
    Write-Host "SSL証明書の確認..."

    $SslDir = Join-Path $ProjectRoot "ssl"
    $SslCert = Join-Path $SslDir "server.crt"
    $SslKey = Join-Path $SslDir "server.key"

    if (-not (Test-Path $SslDir)) {
        New-Item -ItemType Directory -Path $SslDir -Force | Out-Null
    }

    if ((Test-Path $SslCert) -and (Test-Path $SslKey)) {
        Write-Host "[OK] " -ForegroundColor Green -NoNewline
        Write-Host "SSL証明書が存在します"
    } else {
        Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
        Write-Host "SSL証明書が見つかりません"
        Write-Host "  証明書: $SslCert"
        Write-Host "  秘密鍵: $SslKey"
        Write-Host ""
        Write-Host "自己署名証明書を生成しますか？ (y/N): " -ForegroundColor Yellow -NoNewline
        $response = Read-Host
        if ($response -eq "y" -or $response -eq "Y") {
            Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
            Write-Host "OpenSSLで自己署名証明書を生成中..."
            try {
                openssl req -x509 -newkey rsa:4096 -keyout $SslKey -out $SslCert -days 365 -nodes -subj "/CN=localhost"
                Write-Host "[OK] " -ForegroundColor Green -NoNewline
                Write-Host "自己署名証明書を生成しました"
            } catch {
                Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
                Write-Host "証明書の生成に失敗しました。OpenSSLがインストールされているか確認してください。"
            }
        }
    }
}

# 完了メッセージ
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  セットアップ完了" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

if ($Environment -eq "dev") {
    Write-Host "開発環境を起動するには:" -ForegroundColor Cyan
    Write-Host "  .\scripts\windows\start-dev.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "アクセスURL:" -ForegroundColor Cyan
    Write-Host "  http://localhost:5100" -ForegroundColor White
    Write-Host "  https://localhost:5443" -ForegroundColor White
} else {
    Write-Host "本番環境を起動するには:" -ForegroundColor Cyan
    Write-Host "  .\scripts\windows\start-prod.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "アクセスURL:" -ForegroundColor Cyan
    Write-Host "  https://192.168.0.187:8443" -ForegroundColor White
}

Write-Host ""
