# ==============================================================================
# Mirai Knowledge Systems - PowerShell ビルドスクリプト
# ==============================================================================
# 用途: CI/CD自動ビルド・テスト実行
# 対象: Windows PowerShell 7.x
# ==============================================================================

param(
    [switch]$DryRun,
    [switch]$SkipTests,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "=== Mirai Knowledge Systems Build Script ===" -ForegroundColor Cyan
Write-Host "実行日時: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"
Write-Host ""

# ==============================================================================
# 1. 環境チェック
# ==============================================================================
Write-Host "[STEP 1/5] 環境チェック..." -ForegroundColor Yellow

# Python確認
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python が見つかりません" -ForegroundColor Red
    exit 1
}

# Node.js確認（オプション）
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Node.js が見つかりません（オプション）" -ForegroundColor Yellow
}

# ==============================================================================
# 2. PowerShell構文チェック
# ==============================================================================
Write-Host "[STEP 2/5] PowerShell構文チェック..." -ForegroundColor Yellow

$ps1Files = Get-ChildItem -Path "." -Recurse -Filter "*.ps1" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules|\.git|venv" }

$syntaxErrors = 0

foreach ($file in $ps1Files) {
    try {
        $null = [System.Management.Automation.Language.Parser]::ParseFile(
            $file.FullName,
            [ref]$null,
            [ref]$errors
        )

        if ($errors.Count -gt 0) {
            Write-Host "  [ERROR] $($file.Name): $($errors.Count) 個の構文エラー" -ForegroundColor Red
            $syntaxErrors += $errors.Count
        } elseif ($Verbose) {
            Write-Host "  [OK] $($file.Name)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [ERROR] $($file.Name): 解析失敗" -ForegroundColor Red
        $syntaxErrors++
    }
}

if ($syntaxErrors -eq 0) {
    Write-Host "  構文チェック完了: $($ps1Files.Count) ファイル, エラーなし" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] $syntaxErrors 個の構文エラーが見つかりました" -ForegroundColor Red
    exit 1
}

# ==============================================================================
# 3. Python構文チェック
# ==============================================================================
Write-Host "[STEP 3/5] Python構文チェック..." -ForegroundColor Yellow

$pyFiles = Get-ChildItem -Path "./backend" -Recurse -Filter "*.py" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules|\.git|venv|__pycache__|migrations" }

$pythonErrors = 0

foreach ($file in $pyFiles) {
    try {
        $result = python -m py_compile $file.FullName 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [ERROR] $($file.Name)" -ForegroundColor Red
            $pythonErrors++
        } elseif ($Verbose) {
            Write-Host "  [OK] $($file.Name)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [ERROR] $($file.Name): チェック失敗" -ForegroundColor Red
        $pythonErrors++
    }
}

if ($pythonErrors -eq 0) {
    Write-Host "  構文チェック完了: $($pyFiles.Count) ファイル, エラーなし" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] $pythonErrors 個の構文エラーが見つかりました" -ForegroundColor Red
    exit 1
}

# ==============================================================================
# 4. テスト実行
# ==============================================================================
if (-not $SkipTests) {
    Write-Host "[STEP 4/5] テスト実行..." -ForegroundColor Yellow

    if ($DryRun) {
        Write-Host "  [DRY-RUN] テストをスキップ" -ForegroundColor Cyan
    } else {
        Push-Location "./backend"
        try {
            # 環境変数設定
            $env:MKS_ENV = "test"
            $env:MKS_USE_JSON = "true"
            $env:MKS_JWT_SECRET_KEY = "test-secret-key-for-ci-build-only"

            # pytest実行
            $testResult = python -m pytest tests/ -v --tb=short 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  [FAIL] テスト失敗" -ForegroundColor Red
                Write-Host $testResult
                exit 1
            }
            Write-Host "  テスト完了" -ForegroundColor Green
        } catch {
            Write-Host "  [ERROR] テスト実行エラー: $_" -ForegroundColor Red
            exit 1
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "[STEP 4/5] テスト実行... [SKIPPED]" -ForegroundColor Yellow
}

# ==============================================================================
# 5. ビルド完了
# ==============================================================================
Write-Host "[STEP 5/5] ビルド完了チェック..." -ForegroundColor Yellow

# 必須ファイル存在確認
$requiredFiles = @(
    "backend/app_v2.py",
    "backend/requirements.txt",
    "webui/index.html",
    "webui/app.js"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "  [FAIL] 必須ファイルが見つかりません:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "  必須ファイル確認完了" -ForegroundColor Green

# ==============================================================================
# 結果サマリー
# ==============================================================================
Write-Host ""
Write-Host "=== Build OK ===" -ForegroundColor Green
Write-Host "  PowerShellファイル: $($ps1Files.Count)"
Write-Host "  Pythonファイル: $($pyFiles.Count)"
Write-Host "  テスト: $(if ($SkipTests) { 'スキップ' } elseif ($DryRun) { 'ドライラン' } else { '完了' })"
Write-Host ""
