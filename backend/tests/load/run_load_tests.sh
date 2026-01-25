#!/bin/bash

################################################################################
# 負荷テスト実行スクリプト
# Locust、ストレステスト、パフォーマンスベンチマークを実行し、レポート生成
################################################################################

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ディレクトリ設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORTS_DIR="$BACKEND_DIR/tests/reports"

# タイムスタンプ
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}負荷テスト実行スクリプト${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# レポートディレクトリ作成
mkdir -p "$REPORTS_DIR"

# サーバー起動確認
check_server() {
    echo -e "${YELLOW}サーバー起動確認中...${NC}"

    if curl -s http://localhost:5000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ サーバーが起動しています${NC}"
        return 0
    else
        echo -e "${RED}✗ サーバーが起動していません${NC}"
        echo -e "${YELLOW}サーバーを起動してから再実行してください${NC}"
        exit 1
    fi
}

# Locustのインストール確認
check_locust() {
    echo -e "${YELLOW}Locustのインストール確認中...${NC}"

    if command -v locust &> /dev/null; then
        echo -e "${GREEN}✓ Locustがインストールされています${NC}"
        locust --version
        return 0
    else
        echo -e "${RED}✗ Locustがインストールされていません${NC}"
        echo -e "${YELLOW}インストール中...${NC}"
        pip install locust
        echo -e "${GREEN}✓ Locustをインストールしました${NC}"
    fi
}

# Pythonパッケージのインストール確認
check_dependencies() {
    echo -e "${YELLOW}依存パッケージ確認中...${NC}"

    pip install -q psutil requests
    echo -e "${GREEN}✓ 依存パッケージを確認しました${NC}"
}

# 1. パフォーマンスベンチマーク実行
run_benchmark() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}1. パフォーマンスベンチマーク${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""

    python3 "$SCRIPT_DIR/performance_benchmark.py"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ベンチマーク完了${NC}"
    else
        echo -e "${RED}✗ ベンチマーク失敗${NC}"
    fi
}

# 2. Locust負荷テスト実行
run_locust() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}2. Locust負荷テスト${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""

    LOCUST_REPORT="$REPORTS_DIR/locust_report_${TIMESTAMP}"

    echo -e "${YELLOW}テストシナリオ:${NC}"
    echo "  - ログイン → 検索 → 閲覧 (重み: 50)"
    echo "  - ナレッジ作成 (重み: 20)"
    echo "  - 承認操作 (重み: 15)"
    echo "  - 通知確認 (重み: 10)"
    echo "  - ダッシュボード更新 (重み: 5)"
    echo ""
    echo -e "${YELLOW}同時ユーザー数: 300${NC}"
    echo -e "${YELLOW}実行時間: 5分${NC}"
    echo ""

    # Locust実行（ヘッドレスモード）
    cd "$SCRIPT_DIR"
    locust -f locustfile.py \
        --headless \
        --users 300 \
        --spawn-rate 10 \
        --run-time 5m \
        --host http://localhost:5000 \
        --html "${LOCUST_REPORT}.html" \
        --csv "${LOCUST_REPORT}"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Locust負荷テスト完了${NC}"
        echo -e "${GREEN}  レポート: ${LOCUST_REPORT}.html${NC}"
    else
        echo -e "${RED}✗ Locust負荷テスト失敗${NC}"
    fi
}

# 3. ストレステスト実行
run_stress_test() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}3. ストレステスト${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""

    echo -e "${YELLOW}段階的負荷増加: 100 → 500ユーザー${NC}"
    echo ""

    python3 "$SCRIPT_DIR/stress_test.py"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ストレステスト完了${NC}"
    else
        echo -e "${RED}✗ ストレステスト失敗${NC}"
    fi
}

# 統合レポート生成
generate_report() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}4. 統合レポート生成${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""

    REPORT_FILE="$REPORTS_DIR/load_test_report_${TIMESTAMP}.md"

    cat > "$REPORT_FILE" << EOF
# 負荷テスト 統合レポート

実行日時: $(date '+%Y-%m-%d %H:%M:%S')

## 目標値

- 同時接続300ユーザー
- 主要画面3秒以内
- 検索2秒以内
- エラー率1%未満

## テスト結果

### 1. パフォーマンスベンチマーク

主要画面の応答時間を測定しました。

詳細は以下のファイルを参照してください:
- JSON: \`benchmark_${TIMESTAMP}.json\`
- CSV: \`benchmark_${TIMESTAMP}.csv\`

### 2. Locust負荷テスト

5つのユーザーシナリオで300ユーザーの同時負荷テストを実施しました。

詳細は以下のファイルを参照してください:
- HTML: \`locust_report_${TIMESTAMP}.html\`
- CSV: \`locust_report_${TIMESTAMP}_stats.csv\`

### 3. ストレステスト

段階的に負荷を増加させ、システムの限界値を測定しました。

詳細は以下のファイルを参照してください:
- JSON: \`stress_test_${TIMESTAMP}.json\`
- CSV: \`stress_test_${TIMESTAMP}.csv\`

## 推奨事項

テスト結果に基づいた推奨事項:

1. **応答時間の改善**
   - 遅いエンドポイントの最適化
   - データベースインデックスの追加
   - キャッシュの導入

2. **スケーラビリティ**
   - 水平スケーリングの検討
   - ロードバランサーの導入
   - データベース接続プールの調整

3. **監視とアラート**
   - 応答時間の継続的監視
   - エラー率のアラート設定
   - リソース使用率の監視

## 次のステップ

- [ ] ボトルネックの特定と改善
- [ ] データベースクエリの最適化
- [ ] キャッシュ戦略の実装
- [ ] 本番環境での負荷テスト実施

---

生成日時: $(date '+%Y-%m-%d %H:%M:%S')
EOF

    echo -e "${GREEN}✓ 統合レポートを生成しました${NC}"
    echo -e "${GREEN}  レポート: $REPORT_FILE${NC}"
}

# メイン処理
main() {
    # 前提条件チェック
    check_server
    check_locust
    check_dependencies

    # テストメニュー
    echo ""
    echo -e "${YELLOW}実行するテストを選択してください:${NC}"
    echo "  1) 全て実行"
    echo "  2) パフォーマンスベンチマークのみ"
    echo "  3) Locust負荷テストのみ"
    echo "  4) ストレステストのみ"
    echo ""
    read -p "選択 [1-4]: " choice

    case $choice in
        1)
            run_benchmark
            run_locust
            run_stress_test
            generate_report
            ;;
        2)
            run_benchmark
            ;;
        3)
            run_locust
            ;;
        4)
            run_stress_test
            ;;
        *)
            echo -e "${RED}無効な選択です${NC}"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${GREEN}負荷テスト完了${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo -e "レポートディレクトリ: ${YELLOW}$REPORTS_DIR${NC}"
    echo ""
}

# スクリプト実行
main
