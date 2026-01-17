#!/bin/bash
# 建設土木ナレッジシステム - 監視システムセットアップスクリプト
# Prometheus + Grafana + Exporters の自動インストール・設定

set -e

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 実行ユーザーチェック
if [ "$EUID" -ne 0 ]; then
    log_warning "このスクリプトはroot権限が必要です（sudo付きで実行してください）"
    exit 1
fi

# OS検出
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    log_error "OSを検出できません"
    exit 1
fi

log_info "OS検出: $OS $VERSION"

# ================================
# 1. システムパッケージの更新
# ================================
log_info "システムパッケージを更新中..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get update -y
    apt-get upgrade -y
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
    yum update -y
else
    log_warning "サポートされていないOS: $OS"
fi

# ================================
# 2. Prometheus のインストール
# ================================
log_info "Prometheus をインストール中..."

PROMETHEUS_VERSION="2.48.0"
PROMETHEUS_USER="prometheus"

# Prometheusユーザー作成
if ! id "$PROMETHEUS_USER" &>/dev/null; then
    useradd --no-create-home --shell /bin/false $PROMETHEUS_USER
    log_success "Prometheusユーザーを作成しました"
fi

# ディレクトリ作成
mkdir -p /etc/prometheus
mkdir -p /var/lib/prometheus

# Prometheusダウンロード
cd /tmp
wget -q https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz
tar xvfz prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz
cd prometheus-${PROMETHEUS_VERSION}.linux-amd64

# バイナリ配置
cp prometheus /usr/local/bin/
cp promtool /usr/local/bin/
chown $PROMETHEUS_USER:$PROMETHEUS_USER /usr/local/bin/prometheus
chown $PROMETHEUS_USER:$PROMETHEUS_USER /usr/local/bin/promtool

# 設定ファイルとディレクトリ
cp -r consoles /etc/prometheus
cp -r console_libraries /etc/prometheus
chown -R $PROMETHEUS_USER:$PROMETHEUS_USER /etc/prometheus
chown -R $PROMETHEUS_USER:$PROMETHEUS_USER /var/lib/prometheus

log_success "Prometheus v${PROMETHEUS_VERSION} をインストールしました"

# 設定ファイルコピー
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/prometheus.yml" /etc/prometheus/prometheus.yml
cp "$SCRIPT_DIR/alert_rules.yml" /etc/prometheus/alert_rules.yml
chown $PROMETHEUS_USER:$PROMETHEUS_USER /etc/prometheus/prometheus.yml
chown $PROMETHEUS_USER:$PROMETHEUS_USER /etc/prometheus/alert_rules.yml

log_success "Prometheus設定ファイルを配置しました"

# Prometheusサービス作成
cat > /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=$PROMETHEUS_USER
Group=$PROMETHEUS_USER
Type=simple
ExecStart=/usr/local/bin/prometheus \\
    --config.file=/etc/prometheus/prometheus.yml \\
    --storage.tsdb.path=/var/lib/prometheus/ \\
    --web.console.templates=/etc/prometheus/consoles \\
    --web.console.libraries=/etc/prometheus/console_libraries \\
    --web.listen-address=0.0.0.0:9090

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

log_success "Prometheusサービスを作成しました"

# ================================
# 3. Node Exporter のインストール
# ================================
log_info "Node Exporter をインストール中..."

NODE_EXPORTER_VERSION="1.7.0"

cd /tmp
wget -q https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
tar xvfz node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
cd node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64

cp node_exporter /usr/local/bin/
chown $PROMETHEUS_USER:$PROMETHEUS_USER /usr/local/bin/node_exporter

log_success "Node Exporter v${NODE_EXPORTER_VERSION} をインストールしました"

# Node Exporterサービス作成
cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=$PROMETHEUS_USER
Group=$PROMETHEUS_USER
Type=simple
ExecStart=/usr/local/bin/node_exporter

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

log_success "Node Exporterサービスを作成しました"

# ================================
# 4. Grafana のインストール
# ================================
log_info "Grafana をインストール中..."

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get install -y software-properties-common
    wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
    echo "deb https://packages.grafana.com/oss/deb stable main" | tee /etc/apt/sources.list.d/grafana.list
    apt-get update
    apt-get install -y grafana
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
    cat > /etc/yum.repos.d/grafana.repo << EOF
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF
    yum install -y grafana
fi

log_success "Grafana をインストールしました"

# ================================
# 5. サービス起動
# ================================
log_info "サービスを起動中..."

systemctl daemon-reload

# Prometheus起動
systemctl enable prometheus
systemctl start prometheus
log_success "Prometheus を起動しました (http://localhost:9090)"

# Node Exporter起動
systemctl enable node_exporter
systemctl start node_exporter
log_success "Node Exporter を起動しました (http://localhost:9100)"

# Grafana起動
systemctl enable grafana-server
systemctl start grafana-server
log_success "Grafana を起動しました (http://localhost:3000)"

# ================================
# 6. Grafana データソース設定
# ================================
log_info "Grafana データソースを設定中..."

# Grafanaが起動するまで待機
sleep 10

# Prometheusデータソース追加
curl -X POST -H "Content-Type: application/json" \
    -d '{
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://localhost:9090",
        "access": "proxy",
        "isDefault": true
    }' \
    http://admin:admin@localhost:3000/api/datasources

log_success "Prometheusデータソースを追加しました"

# ダッシュボードインポート
log_info "Grafana ダッシュボードをインポート中..."

if [ -f "$SCRIPT_DIR/grafana-dashboard.json" ]; then
    curl -X POST -H "Content-Type: application/json" \
        -d @"$SCRIPT_DIR/grafana-dashboard.json" \
        http://admin:admin@localhost:3000/api/dashboards/db
    log_success "ダッシュボードをインポートしました"
else
    log_warning "ダッシュボードファイルが見つかりません: $SCRIPT_DIR/grafana-dashboard.json"
fi

# ================================
# 7. ファイアウォール設定（オプション）
# ================================
log_info "ファイアウォール設定をチェック中..."

if command -v ufw &> /dev/null; then
    log_info "UFW ファイアウォールを設定中..."
    ufw allow 9090/tcp comment 'Prometheus'
    ufw allow 9100/tcp comment 'Node Exporter'
    ufw allow 3000/tcp comment 'Grafana'
    log_success "ファイアウォールルールを追加しました"
elif command -v firewall-cmd &> /dev/null; then
    log_info "firewalld を設定中..."
    firewall-cmd --permanent --add-port=9090/tcp
    firewall-cmd --permanent --add-port=9100/tcp
    firewall-cmd --permanent --add-port=3000/tcp
    firewall-cmd --reload
    log_success "ファイアウォールルールを追加しました"
fi

# ================================
# 8. 状態確認
# ================================
log_info "サービス状態を確認中..."

echo ""
echo "========================================="
echo "  監視システムセットアップ完了"
echo "========================================="
echo ""
echo "サービス状態:"
systemctl status prometheus --no-pager -l | head -3
systemctl status node_exporter --no-pager -l | head -3
systemctl status grafana-server --no-pager -l | head -3
echo ""
echo "アクセスURL:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Node Exporter: http://localhost:9100/metrics"
echo "  - Grafana: http://localhost:3000"
echo "    (初期ログイン: admin / admin)"
echo ""
echo "次のステップ:"
echo "  1. Grafanaにログインしてパスワードを変更してください"
echo "  2. アプリケーション (http://localhost:5000/api/v1/metrics) を起動してください"
echo "  3. ダッシュボードでメトリクスを確認してください"
echo ""
log_success "セットアップが完了しました！"
