#!/bin/bash

# Mirai Knowledge System - systemd 自動起動セットアップスクリプト
# このスクリプトはsudo権限が必要です

set -e  # エラーが発生したら停止

echo "============================================================"
echo "Mirai Knowledge System - systemd 自動起動セットアップ"
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

# ステップ1: サービスファイルのコピー
echo "[1/5] サービスファイルをインストール中..."
sudo cp "$SCRIPT_DIR/mirai-knowledge-system.service" /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/mirai-knowledge-system.service
echo "✓ サービスファイルをインストールしました"
echo ""

# ステップ2: systemdデーモンの再読み込み
echo "[2/5] systemdデーモンを再読み込み中..."
sudo systemctl daemon-reload
echo "✓ systemdデーモンを再読み込みしました"
echo ""

# ステップ3: サービスの有効化
echo "[3/5] サービスを有効化中（自動起動設定）..."
sudo systemctl enable mirai-knowledge-system.service
echo "✓ サービスを有効化しました（再起動時に自動起動します）"
echo ""

# ステップ4: サービスの起動
echo "[4/5] サービスを起動中..."
if sudo systemctl is-active --quiet mirai-knowledge-system.service; then
    echo "サービスは既に起動しています。再起動します..."
    sudo systemctl restart mirai-knowledge-system.service
else
    sudo systemctl start mirai-knowledge-system.service
fi
echo "✓ サービスを起動しました"
echo ""

# ステップ5: ステータス確認
echo "[5/5] サービスのステータスを確認中..."
sleep 2  # サービスの起動を待つ

if sudo systemctl is-active --quiet mirai-knowledge-system.service; then
    echo "✓ サービスは正常に起動しています"
    echo ""
    sudo systemctl status mirai-knowledge-system.service --no-pager -l
else
    echo "✗ サービスの起動に失敗しました"
    echo ""
    echo "エラーログ:"
    sudo journalctl -u mirai-knowledge-system.service -n 20 --no-pager
    exit 1
fi

echo ""
echo "============================================================"
echo "セットアップ完了！"
echo "============================================================"
echo ""
echo "✅ Mirai Knowledge Systemがポート5100で起動しています"
echo "✅ サーバー再起動時に自動起動します"
echo "✅ クラッシュ時に自動再起動します（10秒後）"
echo "✅ 環境モード: development（CSP緩和、インラインスタイル許可）"
echo ""
echo "アクセスURL:"
echo "  ローカル:       http://localhost:5100/login.html"
echo "  ネットワーク:   http://$(hostname -I | awk '{print $1}'):5100/login.html"
echo ""
echo "デモアカウント:"
echo "  管理者:   admin / admin123"
echo "  施工管理: yamada / yamada123"
echo "  協力会社: partner / partner123"
echo ""
echo "管理コマンド:"
echo "  ステータス確認: sudo systemctl status mirai-knowledge-system.service"
echo "  ログ確認:       sudo journalctl -u mirai-knowledge-system.service -f"
echo "  再起動:         sudo systemctl restart mirai-knowledge-system.service"
echo "  停止:           sudo systemctl stop mirai-knowledge-system.service"
echo ""
echo "📖 詳細は SYSTEMD_SETUP.md を参照してください。"
echo "⚠️  本格的な本番環境では、SSL/TLS証明書を設定した上で"
echo "   MKS_ENV=production に変更してください。"
echo "============================================================"
