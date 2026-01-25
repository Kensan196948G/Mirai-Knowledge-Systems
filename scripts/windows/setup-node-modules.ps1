# ============================================================
# Mirai Knowledge Systems - Windows Node.js モジュールセットアップ
# ============================================================
#
# このスクリプトは、Windows環境でNode.jsモジュールをセットアップします。
# Linux環境との共有フォルダ使用時のバイナリ非互換問題を解決します。
#
# 使用方法:
#   .\scripts\windows\setup-node-modules.ps1 [-Install] [-Clean]
#
# オプション:
#   -Install    Windows用node_modulesをセットアップ
#   -Clean      node_modulesディレクトリを削除
#   -Help       ヘルプ表示
#
# 注意:
#   ネットワークドライブ（共有フォルダ）ではジャンクションが使用できないため、
#   node_modules.windows を直接使用するモードに自動切替します。
#
# ============================================================

param(
    [switch]$Install,
    [switch]$Clean,
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

# プロジェクトルートを取得
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item "$ScriptDir\..\..").FullName

# ネットワークドライブかどうかを判定
function Test-NetworkDrive {
    param([string]$Path)

    $drive = Split-Path -Qualifier $Path
    if ($drive) {
        try {
            $driveInfo = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DeviceID -eq $drive }
            # DriveType 4 = Network Drive
            return ($driveInfo.DriveType -eq 4)
        } catch {
            # UNCパスの場合もネットワークと判定
            return $Path.StartsWith("\\")
        }
    }
    return $false
}

function Show-Help {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Mirai Knowledge Systems - Node.js モジュールセットアップ" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "使用方法: .\setup-node-modules.ps1 [オプション]"
    Write-Host ""
    Write-Host "オプション:"
    Write-Host "  -Install    Windows用node_modulesをセットアップ"
    Write-Host "  -Clean      node_modulesディレクトリを削除"
    Write-Host "  -Help       このヘルプを表示"
    Write-Host ""
    Write-Host "例:"
    Write-Host "  .\setup-node-modules.ps1 -Install"
    Write-Host "  .\setup-node-modules.ps1 -Clean"
    Write-Host ""
    Write-Host "注意:"
    Write-Host "  ネットワークドライブではジャンクションが使用できないため、"
    Write-Host "  node_modules.windows を直接使用するモードで動作します。"
    Write-Host ""
    exit 0
}

function Setup-NodeModules {
    param([string]$TargetDir)

    $PackageJson = Join-Path $TargetDir "package.json"
    if (-not (Test-Path $PackageJson)) {
        Write-Host "[SKIP] " -ForegroundColor Yellow -NoNewline
        Write-Host "package.json が見つかりません: $TargetDir"
        return
    }

    $NodeModules = Join-Path $TargetDir "node_modules"
    $NodeModulesWindows = Join-Path $TargetDir "node_modules.windows"
    $IsNetworkDrive = Test-NetworkDrive -Path $TargetDir

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  セットアップ: $(Split-Path $TargetDir -Leaf)" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan

    if ($IsNetworkDrive) {
        Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
        Write-Host "ネットワークドライブを検出 - 直接モードで動作"
    }

    # 既存のnode_modulesがジャンクションでない場合
    if ((Test-Path $NodeModules) -and -not ((Get-Item $NodeModules).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        # node_modules.windowsにリネーム
        if (-not (Test-Path $NodeModulesWindows)) {
            Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
            Write-Host "既存のnode_modulesを移動: node_modules -> node_modules.windows"
            Move-Item $NodeModules $NodeModulesWindows
        } else {
            Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
            Write-Host "node_modules.windows が既に存在。node_modulesを削除します。"
            Remove-Item -Recurse -Force $NodeModules
        }
    }

    # ジャンクションを削除（ローカルドライブの場合のみ存在する可能性がある）
    if ((Test-Path $NodeModules) -and ((Get-Item $NodeModules).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
        Write-Host "既存のジャンクションを削除"
        cmd /c rmdir $NodeModules 2>$null
    }

    # node_modules.windowsを作成
    if (-not (Test-Path $NodeModulesWindows)) {
        Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
        Write-Host "ディレクトリ作成: node_modules.windows"
        New-Item -ItemType Directory -Path $NodeModulesWindows | Out-Null
    }

    # ネットワークドライブの場合はジャンクションをスキップ
    if (-not $IsNetworkDrive) {
        # ローカルドライブの場合はジャンクション作成を試行
        Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
        Write-Host "ジャンクション作成: node_modules -> node_modules.windows"
        cmd /c mklink /J $NodeModules $NodeModulesWindows 2>$null

        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] " -ForegroundColor Green -NoNewline
            Write-Host "ジャンクション作成成功"
        } else {
            Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
            Write-Host "ジャンクション作成失敗 - 直接モードにフォールバック"
            $IsNetworkDrive = $true
        }
    }

    # npm install 実行
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host "npm install を実行中..."

    Push-Location $TargetDir
    try {
        if ($IsNetworkDrive) {
            # ネットワークドライブの場合は --no-bin-links を使用
            Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
            Write-Host "直接モード: --no-bin-links オプションで実行"

            # シンボリックリンクを無効にしてインストール
            npm install --no-bin-links 2>&1 | ForEach-Object { Write-Host $_ }

            # node_modules を node_modules.windows にリネーム
            if ((Test-Path $NodeModules) -and -not (Test-Path $NodeModulesWindows)) {
                Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
                Write-Host "node_modules を node_modules.windows にリネーム"
                Rename-Item $NodeModules "node_modules.windows"
            } elseif ((Test-Path $NodeModules) -and (Test-Path $NodeModulesWindows)) {
                Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
                Write-Host "node_modules を node_modules.windows にマージ"

                # node_modules の内容を node_modules.windows にコピー
                Get-ChildItem $NodeModules | ForEach-Object {
                    $destPath = Join-Path $NodeModulesWindows $_.Name
                    if (-not (Test-Path $destPath)) {
                        Move-Item $_.FullName $NodeModulesWindows -Force
                    }
                }

                # node_modules を削除
                Remove-Item $NodeModules -Recurse -Force -ErrorAction SilentlyContinue
            }
        } else {
            # ローカルドライブの場合は通常通り
            npm install
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] " -ForegroundColor Green -NoNewline
            Write-Host "npm install 完了"
        } else {
            Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
            Write-Host "npm install に警告があります"
        }
    } catch {
        Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
        Write-Host "npm が見つかりません。手動で npm install を実行してください。"
    }
    Pop-Location

    # ネットワークドライブの場合の使用方法を表示
    if ($IsNetworkDrive) {
        Write-Host ""
        Write-Host "[NOTE] " -ForegroundColor Cyan -NoNewline
        Write-Host "ネットワークドライブモード:"
        Write-Host "       npm スクリプト実行時は以下のように指定してください:"
        Write-Host "       npm run <script> --prefix $TargetDir"
        Write-Host "       または NODE_PATH=$NodeModulesWindows を設定"
    }
}

function Clean-NodeModules {
    param([string]$TargetDir)

    $NodeModules = Join-Path $TargetDir "node_modules"
    $NodeModulesWindows = Join-Path $TargetDir "node_modules.windows"
    $NodeModulesLinux = Join-Path $TargetDir "node_modules.linux"

    # ジャンクション削除
    if ((Test-Path $NodeModules) -and ((Get-Item $NodeModules).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
        Write-Host "ジャンクション削除: $NodeModules"
        cmd /c rmdir $NodeModules
    } elseif (Test-Path $NodeModules) {
        Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
        Write-Host "ディレクトリ削除: $NodeModules"
        Remove-Item -Recurse -Force $NodeModules
    }

    # OS別ディレクトリ削除
    @($NodeModulesWindows, $NodeModulesLinux) | ForEach-Object {
        if (Test-Path $_) {
            Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
            Write-Host "ディレクトリ削除: $_"
            Remove-Item -Recurse -Force $_
        }
    }
}

# メイン処理
if ($Help) {
    Show-Help
}

if (-not $Install -and -not $Clean) {
    Show-Help
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Mirai Knowledge Systems - Node.js モジュールセットアップ" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "プロジェクトルート: $ProjectRoot"
Write-Host "OS: Windows"
Write-Host ""

# package.jsonを持つディレクトリを検索
$TargetDirs = @(
    (Join-Path $ProjectRoot "backend"),
    (Join-Path $ProjectRoot "webui"),
    $ProjectRoot
)

foreach ($TargetDir in $TargetDirs) {
    if (Test-Path (Join-Path $TargetDir "package.json")) {
        if ($Clean) {
            Clean-NodeModules -TargetDir $TargetDir
        }
        if ($Install) {
            Setup-NodeModules -TargetDir $TargetDir
        }
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  完了" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
