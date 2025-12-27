#!/bin/bash

################################################################################
# セキュリティスキャン実行スクリプト
#
# 目的:
#   - bandit（静的解析）を実行してコードの脆弱性をスキャン
#   - safety（依存関係脆弱性チェック）を実行
#   - セキュリティテストを一括実行
#   - 包括的なセキュリティレポートを生成
#
# 使用方法:
#   chmod +x run_security_scan.sh
#   ./run_security_scan.sh
#
# 参照: docs/09_品質保証(QA)/03_Final-Acceptance-Test-Plan.md
#       セクション 5. セキュリティテスト
################################################################################

set -e  # エラー時に即座に終了

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ディレクトリ設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_DIR="$BACKEND_DIR/tests/reports/security"

# レポートディレクトリ作成
mkdir -p "$REPORT_DIR"

# タイムスタンプ
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  セキュリティスキャン開始${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

################################################################################
# 1. 環境確認
################################################################################

echo -e "${YELLOW}[1/6] 環境確認中...${NC}"

cd "$BACKEND_DIR"

# Python仮想環境の確認
if [ ! -d "venv" ]; then
    echo -e "${RED}エラー: Python仮想環境が見つかりません${NC}"
    echo "venv を作成してください: python3 -m venv venv"
    exit 1
fi

# 仮想環境を有効化
source venv/bin/activate

# 必要なツールのインストール確認
echo "必要なセキュリティツールを確認中..."

if ! pip show bandit &> /dev/null; then
    echo "bandit をインストール中..."
    pip install bandit[toml] -q
fi

if ! pip show safety &> /dev/null; then
    echo "safety をインストール中..."
    pip install safety -q
fi

if ! pip show pytest &> /dev/null; then
    echo "pytest をインストール中..."
    pip install pytest pytest-cov -q
fi

echo -e "${GREEN}✓ 環境確認完了${NC}"
echo ""

################################################################################
# 2. Bandit（静的セキュリティ解析）実行
################################################################################

echo -e "${YELLOW}[2/6] Bandit 静的セキュリティ解析実行中...${NC}"

BANDIT_REPORT="$REPORT_DIR/bandit_report_${TIMESTAMP}.txt"
BANDIT_JSON="$REPORT_DIR/bandit_report_${TIMESTAMP}.json"

# Banditを実行（JSONとテキスト両方出力）
bandit -r . \
    -f txt \
    -o "$BANDIT_REPORT" \
    --exclude ./venv,./tests,./htmlcov,./.git \
    --severity-level low \
    || true  # エラーでも続行

bandit -r . \
    -f json \
    -o "$BANDIT_JSON" \
    --exclude ./venv,./tests,./htmlcov,./.git \
    --severity-level low \
    || true

# 結果の表示
if [ -f "$BANDIT_REPORT" ]; then
    echo -e "${GREEN}✓ Bandit解析完了${NC}"
    echo "レポート: $BANDIT_REPORT"

    # 重要度別の問題数をカウント
    HIGH_COUNT=$(grep -c "Severity: High" "$BANDIT_REPORT" || echo "0")
    MEDIUM_COUNT=$(grep -c "Severity: Medium" "$BANDIT_REPORT" || echo "0")
    LOW_COUNT=$(grep -c "Severity: Low" "$BANDIT_REPORT" || echo "0")

    echo ""
    echo "検出された問題:"
    echo -e "  ${RED}High:   $HIGH_COUNT${NC}"
    echo -e "  ${YELLOW}Medium: $MEDIUM_COUNT${NC}"
    echo "  Low:    $LOW_COUNT"

    if [ "$HIGH_COUNT" -gt 0 ]; then
        echo -e "${RED}警告: 重大な脆弱性が検出されました！${NC}"
    fi
else
    echo -e "${RED}✗ Bandit解析に失敗しました${NC}"
fi

echo ""

################################################################################
# 3. Safety（依存関係脆弱性チェック）実行
################################################################################

echo -e "${YELLOW}[3/6] Safety 依存関係脆弱性チェック実行中...${NC}"

SAFETY_REPORT="$REPORT_DIR/safety_report_${TIMESTAMP}.txt"

# requirements.txtを一時的に生成
pip freeze > /tmp/requirements_temp.txt

# Safetyを実行
safety check --file=/tmp/requirements_temp.txt \
    --output text > "$SAFETY_REPORT" 2>&1 || true

# 一時ファイル削除
rm /tmp/requirements_temp.txt

# 結果の表示
if [ -f "$SAFETY_REPORT" ]; then
    echo -e "${GREEN}✓ Safety チェック完了${NC}"
    echo "レポート: $SAFETY_REPORT"

    # 脆弱性の数をカウント
    VULN_COUNT=$(grep -c "vulnerability found" "$SAFETY_REPORT" || echo "0")

    if [ "$VULN_COUNT" -gt 0 ]; then
        echo -e "${RED}警告: $VULN_COUNT 件の依存関係脆弱性が検出されました${NC}"
    else
        echo -e "${GREEN}脆弱性は検出されませんでした${NC}"
    fi
else
    echo -e "${RED}✗ Safety チェックに失敗しました${NC}"
fi

echo ""

################################################################################
# 4. セキュリティテスト実行
################################################################################

echo -e "${YELLOW}[4/6] セキュリティテスト実行中...${NC}"

PYTEST_REPORT="$REPORT_DIR/pytest_security_${TIMESTAMP}.xml"
PYTEST_HTML="$REPORT_DIR/pytest_security_${TIMESTAMP}.html"
PYTEST_COV="$REPORT_DIR/coverage_security_${TIMESTAMP}.txt"

# pytestでセキュリティテストを実行
pytest tests/security/ \
    --verbose \
    --tb=short \
    --junitxml="$PYTEST_REPORT" \
    --cov=. \
    --cov-report=term \
    --cov-report=html:tests/reports/security/coverage_html_${TIMESTAMP} \
    > "$PYTEST_COV" 2>&1 || true

if [ -f "$PYTEST_REPORT" ]; then
    echo -e "${GREEN}✓ セキュリティテスト完了${NC}"
    echo "レポート: $PYTEST_REPORT"
    echo "カバレッジ: $PYTEST_COV"

    # テスト結果のサマリーを表示
    if grep -q "passed" "$PYTEST_COV"; then
        PASSED=$(grep -oP '\d+(?= passed)' "$PYTEST_COV" | tail -1 || echo "0")
        FAILED=$(grep -oP '\d+(?= failed)' "$PYTEST_COV" | tail -1 || echo "0")

        echo ""
        echo "テスト結果:"
        echo -e "  ${GREEN}成功: $PASSED${NC}"

        if [ "$FAILED" -gt 0 ]; then
            echo -e "  ${RED}失敗: $FAILED${NC}"
        fi
    fi
else
    echo -e "${RED}✗ セキュリティテストの実行に失敗しました${NC}"
fi

echo ""

################################################################################
# 5. 総合レポート生成
################################################################################

echo -e "${YELLOW}[5/6] 総合セキュリティレポート生成中...${NC}"

SUMMARY_REPORT="$REPORT_DIR/security_summary_${TIMESTAMP}.txt"

cat > "$SUMMARY_REPORT" << EOF
================================================================================
セキュリティスキャン総合レポート
================================================================================

実行日時: $(date '+%Y-%m-%d %H:%M:%S')
プロジェクト: Mirai Knowledge Systems
対象: Backend Application

================================================================================
1. Bandit 静的セキュリティ解析
================================================================================

EOF

if [ -f "$BANDIT_REPORT" ]; then
    cat "$BANDIT_REPORT" >> "$SUMMARY_REPORT"
else
    echo "解析結果なし" >> "$SUMMARY_REPORT"
fi

cat >> "$SUMMARY_REPORT" << EOF

================================================================================
2. Safety 依存関係脆弱性チェック
================================================================================

EOF

if [ -f "$SAFETY_REPORT" ]; then
    cat "$SAFETY_REPORT" >> "$SUMMARY_REPORT"
else
    echo "チェック結果なし" >> "$SUMMARY_REPORT"
fi

cat >> "$SUMMARY_REPORT" << EOF

================================================================================
3. セキュリティテスト結果
================================================================================

EOF

if [ -f "$PYTEST_COV" ]; then
    cat "$PYTEST_COV" >> "$SUMMARY_REPORT"
else
    echo "テスト結果なし" >> "$SUMMARY_REPORT"
fi

cat >> "$SUMMARY_REPORT" << EOF

================================================================================
4. 総合評価
================================================================================

EOF

# 総合評価を生成
TOTAL_ISSUES=0
CRITICAL_ISSUES=0

if [ -f "$BANDIT_REPORT" ]; then
    BANDIT_HIGH=$(grep -c "Severity: High" "$BANDIT_REPORT" || echo "0")
    TOTAL_ISSUES=$((TOTAL_ISSUES + BANDIT_HIGH))
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + BANDIT_HIGH))
fi

if [ -f "$SAFETY_REPORT" ]; then
    SAFETY_VULNS=$(grep -c "vulnerability found" "$SAFETY_REPORT" || echo "0")
    TOTAL_ISSUES=$((TOTAL_ISSUES + SAFETY_VULNS))
fi

cat >> "$SUMMARY_REPORT" << EOF
検出された問題の総数: $TOTAL_ISSUES
うち重大な問題: $CRITICAL_ISSUES

推奨アクション:
EOF

if [ "$CRITICAL_ISSUES" -gt 0 ]; then
    cat >> "$SUMMARY_REPORT" << EOF
  [緊急] 重大な脆弱性が検出されました。即座に対応してください。
EOF
fi

if [ "$TOTAL_ISSUES" -eq 0 ]; then
    cat >> "$SUMMARY_REPORT" << EOF
  [OK] 重大な問題は検出されませんでした。
EOF
else
    cat >> "$SUMMARY_REPORT" << EOF
  - Banditレポートを確認し、コードの脆弱性を修正してください
  - Safetyレポートを確認し、依存関係を更新してください
  - セキュリティテストの失敗を修正してください
EOF
fi

cat >> "$SUMMARY_REPORT" << EOF

================================================================================
詳細レポート
================================================================================

Bandit JSON:     $BANDIT_JSON
Bandit テキスト: $BANDIT_REPORT
Safety:          $SAFETY_REPORT
Pytest XML:      $PYTEST_REPORT
カバレッジ:      $PYTEST_COV

================================================================================
EOF

echo -e "${GREEN}✓ 総合レポート生成完了${NC}"
echo "レポート: $SUMMARY_REPORT"
echo ""

################################################################################
# 6. サマリー表示
################################################################################

echo -e "${YELLOW}[6/6] サマリー表示${NC}"
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  セキュリティスキャン完了${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# サマリーを表示
if [ "$CRITICAL_ISSUES" -gt 0 ]; then
    echo -e "${RED}✗ 重大な問題が検出されました！${NC}"
    echo -e "${RED}  重大な問題: $CRITICAL_ISSUES 件${NC}"
    echo -e "${RED}  総問題数: $TOTAL_ISSUES 件${NC}"
    EXIT_CODE=1
elif [ "$TOTAL_ISSUES" -gt 0 ]; then
    echo -e "${YELLOW}⚠ 問題が検出されました${NC}"
    echo -e "${YELLOW}  総問題数: $TOTAL_ISSUES 件${NC}"
    EXIT_CODE=0
else
    echo -e "${GREEN}✓ セキュリティスキャン合格${NC}"
    echo -e "${GREEN}  重大な問題は検出されませんでした${NC}"
    EXIT_CODE=0
fi

echo ""
echo "詳細は以下のレポートを参照してください:"
echo "  $SUMMARY_REPORT"
echo ""

################################################################################
# レポートの場所を表示
################################################################################

echo -e "${BLUE}生成されたレポート:${NC}"
echo "  - 総合レポート: $SUMMARY_REPORT"
echo "  - Bandit: $BANDIT_REPORT"
echo "  - Safety: $SAFETY_REPORT"
echo "  - Pytest: $PYTEST_REPORT"
echo ""

# 重要な問題がある場合は内容を表示
if [ "$CRITICAL_ISSUES" -gt 0 ] && [ -f "$BANDIT_REPORT" ]; then
    echo -e "${RED}重大な問題の詳細:${NC}"
    echo ""
    grep -A 5 "Severity: High" "$BANDIT_REPORT" | head -20 || true
    echo ""
fi

echo -e "${BLUE}セキュリティスキャンを終了します${NC}"

exit $EXIT_CODE
