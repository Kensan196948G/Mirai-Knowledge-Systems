#!/bin/bash
# エラー自動検知・自動修復システム インストールスクリプト

set -e

echo "=============================================="
echo "エラー自動検知・自動修復システム インストール"
echo "=============================================="
echo

# 現在のディレクトリを確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "インストールディレクトリ: $SCRIPT_DIR"
echo "バックエンドディレクトリ: $BACKEND_DIR"
echo

# 1. 依存パッケージのチェック
echo "[1/5] 依存パッケージのチェック..."
python3 -c "import psutil, requests" 2>/dev/null || {
    echo "必要なPythonパッケージがインストールされていません"
    echo "インストールコマンド: pip3 install psutil requests"
    read -p "今すぐインストールしますか? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install psutil requests
    else
        echo "依存パッケージをインストールしてから再度実行してください"
        exit 1
    fi
}
echo "✓ 依存パッケージ確認完了"
echo

# 2. 実行権限の設定
echo "[2/5] 実行権限の設定..."
chmod +x "$SCRIPT_DIR/auto_fix_daemon.py"
chmod +x "$SCRIPT_DIR/health_monitor.py"
chmod +x "$SCRIPT_DIR/test_auto_fix.py"
echo "✓ 実行権限設定完了"
echo

# 3. 必要なディレクトリの作成
echo "[3/5] ディレクトリの作成..."
mkdir -p "$BACKEND_DIR/data"
mkdir -p "$BACKEND_DIR/logs"
mkdir -p "$BACKEND_DIR/uploads"
mkdir -p "$BACKEND_DIR/cache"
mkdir -p "$BACKEND_DIR/backups"
echo "✓ ディレクトリ作成完了"
echo

# 4. 設定ファイルの検証
echo "[4/5] 設定ファイルの検証..."
python3 -c "import json; json.load(open('$SCRIPT_DIR/error_patterns.json'))" || {
    echo "✗ error_patterns.json が無効です"
    exit 1
}
echo "✓ 設定ファイル検証完了"
echo

# 5. テスト実行
echo "[5/5] 動作テスト..."
python3 "$SCRIPT_DIR/health_monitor.py" > /dev/null 2>&1 || {
    echo "✗ ヘルスモニターのテストに失敗しました"
    exit 1
}
echo "✓ 動作テスト完了"
echo

echo "=============================================="
echo "インストール完了！"
echo "=============================================="
echo
echo "次のステップ:"
echo
echo "1. 手動で1回実行:"
echo "   cd $SCRIPT_DIR"
echo "   python3 auto_fix_daemon.py"
echo
echo "2. 継続的監視モードで実行:"
echo "   python3 auto_fix_daemon.py --continuous"
echo
echo "3. systemdサービスとしてインストール:"
echo "   sudo cp $SCRIPT_DIR/auto-fix-daemon.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable auto-fix-daemon"
echo "   sudo systemctl start auto-fix-daemon"
echo
echo "4. ログ確認:"
echo "   tail -f $BACKEND_DIR/logs/auto_fix.log"
echo
echo "詳細は QUICKSTART.md を参照してください"
echo
