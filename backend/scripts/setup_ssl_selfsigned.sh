#!/bin/bash
# 自己署名SSL証明書セットアップスクリプト
# Mirai Knowledge Systems - Phase B-11
#
# 使用方法:
#   ./setup_ssl_selfsigned.sh [generate|nginx|status|remove]
#
# 注意: 自己署名証明書は開発・テスト環境専用です
#       本番環境ではLet's Encryptを使用してください

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定
CERT_DIR="/etc/ssl/mks"
CERT_DAYS=365
KEY_SIZE=2048
DOMAIN="${MKS_DOMAIN:-localhost}"
ORG_NAME="Mirai Knowledge Systems"
NGINX_CONF="/etc/nginx/sites-available/mirai-knowledge-system"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 証明書生成
generate_cert() {
    log_info "自己署名SSL証明書を生成中..."

    # ディレクトリ作成
    sudo mkdir -p "$CERT_DIR"
    sudo chmod 755 "$CERT_DIR"

    # 秘密鍵生成
    log_info "秘密鍵を生成中..."
    sudo openssl genrsa -out "$CERT_DIR/mks.key" $KEY_SIZE
    sudo chmod 600 "$CERT_DIR/mks.key"

    # CSR設定ファイル作成
    log_info "証明書署名要求を生成中..."
    cat << EOF | sudo tee "$CERT_DIR/openssl.cnf" > /dev/null
[req]
default_bits = $KEY_SIZE
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext
x509_extensions = v3_ca

[dn]
C = JP
ST = Tokyo
L = Tokyo
O = $ORG_NAME
OU = Development
CN = $DOMAIN

[req_ext]
subjectAltName = @alt_names

[v3_ca]
subjectAltName = @alt_names
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = localhost
DNS.3 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    # 証明書生成
    log_info "証明書を生成中..."
    sudo openssl req -x509 -nodes \
        -days $CERT_DAYS \
        -key "$CERT_DIR/mks.key" \
        -out "$CERT_DIR/mks.crt" \
        -config "$CERT_DIR/openssl.cnf"

    sudo chmod 644 "$CERT_DIR/mks.crt"

    # DHパラメータ生成（オプション）
    if [ ! -f "$CERT_DIR/dhparam.pem" ]; then
        log_info "DHパラメータを生成中（時間がかかる場合があります）..."
        sudo openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048
    fi

    log_success "証明書を生成しました: $CERT_DIR"

    # 証明書情報表示
    echo ""
    log_info "証明書情報:"
    openssl x509 -in "$CERT_DIR/mks.crt" -noout -subject -dates
}

# Nginx設定作成
setup_nginx() {
    log_info "Nginx HTTPS設定を作成中..."

    # 証明書存在確認
    if [ ! -f "$CERT_DIR/mks.crt" ] || [ ! -f "$CERT_DIR/mks.key" ]; then
        log_error "証明書が見つかりません。先に 'generate' を実行してください"
        exit 1
    fi

    # Nginx設定ファイル作成
    sudo tee "$NGINX_CONF" > /dev/null << 'NGINX_EOF'
# HTTP → HTTPS リダイレクト
server {
    listen 80;
    listen [::]:80;
    server_name _;

    # HTTPS にリダイレクト
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS サーバー
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    # SSL証明書設定
    ssl_certificate /etc/ssl/mks/mks.crt;
    ssl_certificate_key /etc/ssl/mks/mks.key;

    # SSL設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    # SSLセッション設定
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # DHパラメータ（存在する場合）
    # ssl_dhparam /etc/ssl/mks/dhparam.pem;

    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    # HSTS（自己署名では有効化しない）
    # add_header Strict-Transport-Security "max-age=31536000" always;

    # ログ
    access_log /var/log/nginx/mks-access.log;
    error_log /var/log/nginx/mks-error.log;

    # リクエストサイズ制限
    client_max_body_size 10M;

    # バックエンドへのプロキシ
    location / {
        proxy_pass http://127.0.0.1:5100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静的ファイル（WebUI）
    location /static/ {
        alias /mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/;
        expires 1d;
        add_header Cache-Control "public";
    }
}
NGINX_EOF

    # シンボリックリンク作成
    if [ ! -L /etc/nginx/sites-enabled/mirai-knowledge-system ]; then
        sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
    fi

    # デフォルト設定を無効化
    if [ -L /etc/nginx/sites-enabled/default ]; then
        sudo rm /etc/nginx/sites-enabled/default
    fi

    # 設定テスト
    log_info "Nginx設定をテスト中..."
    if sudo nginx -t; then
        log_success "Nginx設定は正常です"

        # Nginx再起動
        log_info "Nginxを再起動中..."
        sudo systemctl reload nginx
        log_success "Nginx設定を適用しました"
    else
        log_error "Nginx設定にエラーがあります"
        exit 1
    fi
}

# ステータス確認
check_status() {
    log_info "SSL/HTTPS設定状態を確認中..."

    echo ""
    echo "=== 証明書 ==="
    if [ -f "$CERT_DIR/mks.crt" ]; then
        log_success "証明書: $CERT_DIR/mks.crt"
        openssl x509 -in "$CERT_DIR/mks.crt" -noout -subject -dates 2>/dev/null || true
    else
        log_warn "証明書: 未生成"
    fi

    if [ -f "$CERT_DIR/mks.key" ]; then
        log_success "秘密鍵: $CERT_DIR/mks.key"
    else
        log_warn "秘密鍵: 未生成"
    fi

    echo ""
    echo "=== Nginx ==="
    if [ -f "$NGINX_CONF" ]; then
        log_success "設定ファイル: $NGINX_CONF"
    else
        log_warn "設定ファイル: 未作成"
    fi

    if systemctl is-active --quiet nginx; then
        log_success "Nginx: 稼働中"
    else
        log_warn "Nginx: 停止中"
    fi

    echo ""
    echo "=== 接続テスト ==="
    if curl -k -s https://localhost/api/v1/health > /dev/null 2>&1; then
        log_success "HTTPS接続: OK"
    else
        log_warn "HTTPS接続: 失敗（サービスが起動していない可能性）"
    fi
}

# 証明書削除
remove_cert() {
    log_warn "証明書を削除します"
    read -p "続行しますか？ (y/N): " confirm

    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_info "キャンセルしました"
        return 0
    fi

    sudo rm -rf "$CERT_DIR"
    log_success "証明書を削除しました"

    if [ -L /etc/nginx/sites-enabled/mirai-knowledge-system ]; then
        sudo rm /etc/nginx/sites-enabled/mirai-knowledge-system
    fi

    if [ -f "$NGINX_CONF" ]; then
        sudo rm "$NGINX_CONF"
    fi

    log_success "Nginx設定を削除しました"
}

# ヘルプ表示
show_help() {
    echo "自己署名SSL証明書セットアップスクリプト"
    echo ""
    echo "使用方法:"
    echo "  $0 [コマンド]"
    echo ""
    echo "コマンド:"
    echo "  generate   自己署名証明書を生成"
    echo "  nginx      Nginx HTTPS設定を作成・適用"
    echo "  status     現在の設定状態を確認"
    echo "  remove     証明書と設定を削除"
    echo "  help       このヘルプを表示"
    echo ""
    echo "環境変数:"
    echo "  MKS_DOMAIN   ドメイン名（デフォルト: localhost）"
    echo ""
    echo "例:"
    echo "  sudo $0 generate          # 証明書生成"
    echo "  sudo $0 nginx             # Nginx設定適用"
    echo "  MKS_DOMAIN=mks.local sudo $0 generate  # カスタムドメイン"
    echo ""
    echo "注意:"
    echo "  自己署名証明書は開発・テスト環境専用です"
    echo "  本番環境ではLet's Encryptを使用してください"
}

# メイン処理
case "${1:-help}" in
    generate)
        generate_cert
        ;;
    nginx)
        setup_nginx
        ;;
    status)
        check_status
        ;;
    remove)
        remove_cert
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "不明なコマンド: $1"
        show_help
        exit 1
        ;;
esac
