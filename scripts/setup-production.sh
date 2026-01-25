#!/bin/bash

# Mirai Knowledge System - 本番環境セットアップスクリプト
# このスクリプトはsudo権限が必要です
#
# 機能:
# - 本番用systemdサービスのインストール
# - SSL/TLS証明書の確認
# - Nginx設定のインストール
# - 本番環境変数ファイルの作成
# - ログディレクトリの作成

set -e  # エラーが発生したら停止

echo "============================================================"
echo "Mirai Knowledge System - 本番環境セットアップ"
echo "============================================================"
echo ""

# カレントディレクトリを確認
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "プロジェクトディレクトリ: $SCRIPT_DIR"
echo ""

# sudo権限の確認
if ! sudo -n true 2>/dev/null; then
    echo "このスクリプトはsudo権限が必要です。"
    echo "パスワードの入力を求められる場合があります。"
    echo ""
fi

# ステップ0: 前提条件の確認
echo "[0/7] 前提条件を確認中..."
ERRORS=0

# SSL証明書の確認
if [ ! -f "$SCRIPT_DIR/../backend/ssl/server.crt" ] || [ ! -f "$SCRIPT_DIR/../backend/ssl/server.key" ]; then
    echo "✗ SSL証明書が見つかりません: $SCRIPT_DIR/../backend/ssl/"
    echo "  以下のコマンドで生成してください:"
    echo "  openssl req -x509 -newkey rsa:4096 -keyout backend/ssl/server.key -out backend/ssl/server.crt -days 365 -nodes"
    ERRORS=$((ERRORS+1))
else
    echo "✓ SSL証明書が存在します"
fi

# Python仮想環境の確認
if [ ! -f "$SCRIPT_DIR/../venv_linux/bin/python3" ]; then
    echo "✗ Python仮想環境が見つかりません: $SCRIPT_DIR/../venv_linux/"
    ERRORS=$((ERRORS+1))
else
    echo "✓ Python仮想環境が存在します"
fi

# 依存関係の確認
if [ ! -f "$SCRIPT_DIR/../venv_linux/bin/gunicorn" ]; then
    echo "✗ Gunicornがインストールされていません"
    ERRORS=$((ERRORS+1))
else
    echo "✓ Gunicornがインストールされています"
fi

# Nginxの確認
if ! command -v nginx &> /dev/null; then
    echo "⚠ Nginxがインストールされていません（オプション）"
else
    echo "✓ Nginxがインストールされています"
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "✗ 前提条件の確認に失敗しました。上記のエラーを修正してください。"
    exit 1
fi
echo ""

# ステップ1: ログディレクトリの作成
echo "[1/7] ログディレクトリを作成中..."
sudo mkdir -p /var/log/mirai-knowledge
sudo chown kensan:kensan /var/log/mirai-knowledge
sudo chmod 755 /var/log/mirai-knowledge
echo "✓ ログディレクトリを作成しました: /var/log/mirai-knowledge"
echo ""

# ステップ2: 本番環境変数ファイルの確認/作成
echo "[2/7] 本番環境変数ファイルを確認中..."
if [ ! -f "$SCRIPT_DIR/../backend/.env.production" ]; then
    echo "本番環境変数ファイルが存在しません。作成します..."
    if [ -f "$SCRIPT_DIR/../backend/.env.production.example" ]; then
        cp "$SCRIPT_DIR/../backend/.env.production.example" "$SCRIPT_DIR/../backend/.env.production"
        echo "✓ .env.production を作成しました（テンプレートからコピー）"
        echo "⚠ 重要: $SCRIPT_DIR/../backend/.env.production を編集して"
        echo "  MKS_JWT_SECRET_KEY と MKS_SECRET_KEY を安全な値に変更してください！"
    else
        echo "✗ テンプレートファイルが見つかりません"
        exit 1
    fi
else
    echo "✓ 本番環境変数ファイルが存在します"
fi
echo ""

# ステップ3: 本番サービスファイルのコピー
echo "[3/7] 本番サービスファイルをインストール中..."
sudo cp "$SCRIPT_DIR/../config/mirai-knowledge-production.service" /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/mirai-knowledge-production.service
echo "✓ 本番サービスファイルをインストールしました"
echo ""

# ステップ4: systemdデーモンの再読み込み
echo "[4/7] systemdデーモンを再読み込み中..."
sudo systemctl daemon-reload
echo "✓ systemdデーモンを再読み込みしました"
echo ""

# ステップ5: サービスの有効化
echo "[5/7] 本番サービスを有効化中（自動起動設定）..."
sudo systemctl enable mirai-knowledge-production.service
echo "✓ 本番サービスを有効化しました（再起動時に自動起動します）"
echo ""

# ステップ6: Nginx設定のインストール（オプション）
echo "[6/7] Nginx設定を確認中..."
if command -v nginx &> /dev/null; then
    if [ -d "/etc/nginx/sites-available" ]; then
        sudo cp "$SCRIPT_DIR/../config/nginx-production.conf" /etc/nginx/sites-available/mirai-knowledge-production
        if [ ! -L "/etc/nginx/sites-enabled/mirai-knowledge-production" ]; then
            sudo ln -s /etc/nginx/sites-available/mirai-knowledge-production /etc/nginx/sites-enabled/
        fi
        echo "✓ Nginx設定をインストールしました"

        # Nginx設定テスト
        if sudo nginx -t 2>/dev/null; then
            echo "✓ Nginx設定テスト: OK"
        else
            echo "⚠ Nginx設定テストに失敗しました。手動で確認してください。"
        fi
    else
        echo "⚠ Nginx sites-available ディレクトリが見つかりません"
    fi
else
    echo "⚠ Nginxがインストールされていません。スキップします。"
fi
echo ""

# ステップ7: サービスの起動
echo "[7/7] 本番サービスを起動中..."

# 開発環境サービスが動いている場合は停止
if sudo systemctl is-active --quiet mirai-knowledge-system.service 2>/dev/null; then
    echo "開発環境サービスを停止します..."
    sudo systemctl stop mirai-knowledge-system.service
fi

# 本番サービスの起動
if sudo systemctl is-active --quiet mirai-knowledge-production.service; then
    echo "本番サービスは既に起動しています。再起動します..."
    sudo systemctl restart mirai-knowledge-production.service
else
    sudo systemctl start mirai-knowledge-production.service
fi

sleep 3  # サービスの起動を待つ

if sudo systemctl is-active --quiet mirai-knowledge-production.service; then
    echo "✓ 本番サービスは正常に起動しています"
    echo ""
    sudo systemctl status mirai-knowledge-production.service --no-pager -l
else
    echo "✗ 本番サービスの起動に失敗しました"
    echo ""
    echo "エラーログ:"
    sudo journalctl -u mirai-knowledge-production.service -n 30 --no-pager
    exit 1
fi

echo ""
echo "============================================================"
echo "本番環境セットアップ完了！"
echo "============================================================"
echo ""
echo "✅ Mirai Knowledge System 本番環境が起動しています"
echo "✅ サーバー再起動時に自動起動します"
echo "✅ クラッシュ時に自動再起動します（10秒後）"
echo "✅ 環境モード: production"
echo ""
echo "アクセスURL:"
LOCAL_IP=$(hostname -I | awk '{print $1}')
if command -v nginx &> /dev/null; then
    echo "  HTTPS:  https://$LOCAL_IP/ (推奨)"
    echo "  HTTP:   http://$LOCAL_IP/ (HTTPSにリダイレクト)"
fi
echo "  直接:   http://$LOCAL_IP:8000/ (Gunicorn直接、テスト用)"
echo ""
echo "⚠️  自己署名証明書を使用しているため、ブラウザで警告が表示されます。"
echo "   「詳細設定」→「安全でないページに進む」で続行できます。"
echo ""
echo "管理コマンド:"
echo "  ステータス確認: sudo systemctl status mirai-knowledge-production.service"
echo "  ログ確認:       sudo journalctl -u mirai-knowledge-production.service -f"
echo "  再起動:         sudo systemctl restart mirai-knowledge-production.service"
echo "  停止:           sudo systemctl stop mirai-knowledge-production.service"
echo ""
echo "Nginx管理（インストール済みの場合）:"
echo "  設定テスト:     sudo nginx -t"
echo "  リロード:       sudo systemctl reload nginx"
echo ""
echo "📖 詳細は PRODUCTION_DEPLOYMENT.md を参照してください。"
echo "============================================================"
