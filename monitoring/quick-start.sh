#!/bin/bash
# 建設土木ナレッジシステム - 監視システムクイックスタート
# Docker Compose を使用した簡単セットアップ

set -e

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  監視システム クイックスタート${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# スクリプトディレクトリ取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Docker/Docker Composeチェック
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}[警告]${NC} Dockerがインストールされていません"
    echo "Dockerをインストールしてください: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}[警告]${NC} Docker Composeがインストールされていません"
    echo "Docker Composeをインストールしてください"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Docker環境を確認しました"

# Docker Composeコマンド判定
COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

# 既存コンテナ停止（もしあれば）
echo ""
echo -e "${BLUE}[INFO]${NC} 既存の監視コンテナを確認中..."
$COMPOSE_CMD -f docker-compose.monitoring.yml down 2>/dev/null || true

# コンテナ起動
echo ""
echo -e "${BLUE}[INFO]${NC} 監視スタックを起動中..."
$COMPOSE_CMD -f docker-compose.monitoring.yml up -d

# 起動待機
echo ""
echo -e "${BLUE}[INFO]${NC} サービスの起動を待機中..."
sleep 10

# 状態確認
echo ""
echo -e "${BLUE}[INFO]${NC} サービス状態を確認中..."
$COMPOSE_CMD -f docker-compose.monitoring.yml ps

# Prometheusヘルスチェック
echo ""
echo -e "${BLUE}[INFO]${NC} Prometheusの起動を確認中..."
for i in {1..30}; do
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} Prometheus が起動しました"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}[警告]${NC} Prometheusの起動確認がタイムアウトしました"
    fi
    sleep 2
done

# Grafanaヘルスチェック
echo -e "${BLUE}[INFO]${NC} Grafanaの起動を確認中..."
for i in {1..30}; do
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} Grafana が起動しました"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}[警告]${NC} Grafanaの起動確認がタイムアウトしました"
    fi
    sleep 2
done

# 完了メッセージ
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  監視システムのセットアップ完了！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "アクセスURL:"
echo "  🎯 Grafana:        http://localhost:3000"
echo "     ログイン:       admin / admin"
echo ""
echo "  📊 Prometheus:     http://localhost:9090"
echo "  🔔 Alertmanager:   http://localhost:9093"
echo "  💻 Node Exporter:  http://localhost:9100/metrics"
echo "  📦 cAdvisor:       http://localhost:8080"
echo ""
echo "  🏢 アプリ メトリクス: http://localhost:5000/api/v1/metrics"
echo "     ※ アプリケーションを起動してください"
echo ""
echo "次のステップ:"
echo "  1. Grafanaにログインしてパスワードを変更"
echo "  2. アプリケーションを起動: cd ../backend && python app_v2.py"
echo "  3. ダッシュボードを確認"
echo ""
echo "コマンド:"
echo "  ログ確認:    $COMPOSE_CMD -f docker-compose.monitoring.yml logs -f"
echo "  停止:        $COMPOSE_CMD -f docker-compose.monitoring.yml stop"
echo "  再起動:      $COMPOSE_CMD -f docker-compose.monitoring.yml restart"
echo "  完全削除:    $COMPOSE_CMD -f docker-compose.monitoring.yml down -v"
echo ""
echo -e "${GREEN}監視システムが正常に起動しました！${NC}"
