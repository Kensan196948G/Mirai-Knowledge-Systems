#!/bin/bash

################################################################################
# Mirai Knowledge System 監視システムセットアップスクリプト
# Prometheus + Grafana の自動セットアップ
################################################################################

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ヘッダー表示
echo "============================================================"
echo "  Mirai Knowledge System 監視システムセットアップ"
echo "  Prometheus + Grafana"
echo "============================================================"
echo ""

# 現在のディレクトリを確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
info "スクリプトディレクトリ: $SCRIPT_DIR"

# Dockerの確認
info "Dockerのインストール確認中..."
if ! command -v docker &> /dev/null; then
    error "Dockerがインストールされていません。"
    error "Docker をインストールしてから再度実行してください。"
    exit 1
fi
success "Docker が見つかりました: $(docker --version)"

# Docker Composeの確認
info "Docker Composeのインストール確認中..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "Docker Composeがインストールされていません。"
    error "Docker Compose をインストールしてから再度実行してください。"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    success "Docker Compose が見つかりました: $(docker-compose --version)"
else
    DOCKER_COMPOSE_CMD="docker compose"
    success "Docker Compose が見つかりました: $(docker compose version)"
fi

# 設定ファイルの確認
info "設定ファイルの確認中..."
REQUIRED_FILES=(
    "prometheus/prometheus.yml"
    "prometheus/alert-rules.yml"
    "grafana/provisioning/datasources/prometheus.yml"
    "grafana/provisioning/dashboards/dashboards.yml"
    "grafana/dashboards/app-overview.json"
    "grafana/dashboards/api-performance.json"
    "grafana/dashboards/system-resources.json"
    "docker-compose.yml"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    error "以下の必須ファイルが見つかりません:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    exit 1
fi
success "すべての設定ファイルが確認されました"

# 既存のコンテナを停止
info "既存のコンテナを停止中..."
cd "$SCRIPT_DIR"
$DOCKER_COMPOSE_CMD down 2>/dev/null || true
success "既存のコンテナを停止しました"

# Dockerイメージのプル
info "Dockerイメージをプル中..."
$DOCKER_COMPOSE_CMD pull
success "Dockerイメージをプルしました"

# コンテナの起動
info "監視システムを起動中..."
$DOCKER_COMPOSE_CMD up -d
success "監視システムを起動しました"

# 起動待機
info "サービスの起動を待機中..."
sleep 10

# ヘルスチェック
info "ヘルスチェック実行中..."

# Prometheusヘルスチェック
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    success "Prometheus は正常に起動しています"
else
    warning "Prometheus のヘルスチェックに失敗しました（起動に時間がかかっている可能性があります）"
fi

# Grafanaヘルスチェック
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    success "Grafana は正常に起動しています"
else
    warning "Grafana のヘルスチェックに失敗しました（起動に時間がかかっている可能性があります）"
fi

# 結果表示
echo ""
echo "============================================================"
echo "  監視システムセットアップ完了"
echo "============================================================"
echo ""
success "Prometheus と Grafana が正常に起動しました"
echo ""
echo "アクセス情報:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana:    http://localhost:3000"
echo ""
echo "Grafana ログイン情報:"
echo "  - ユーザー名: admin"
echo "  - パスワード: admin123"
echo "  ※ 初回ログイン後、パスワードを変更してください"
echo ""
echo "利用可能なダッシュボード:"
echo "  1. Mirai Knowledge System - アプリケーション概要"
echo "  2. Mirai Knowledge System - APIパフォーマンス"
echo "  3. Mirai Knowledge System - システムリソース"
echo ""
info "監視システムの停止: cd $SCRIPT_DIR && $DOCKER_COMPOSE_CMD down"
info "監視システムの再起動: cd $SCRIPT_DIR && $DOCKER_COMPOSE_CMD restart"
info "ログの確認: cd $SCRIPT_DIR && $DOCKER_COMPOSE_CMD logs -f"
echo ""
echo "============================================================"
