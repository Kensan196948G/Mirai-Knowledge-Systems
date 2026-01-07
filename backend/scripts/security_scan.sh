#!/bin/bash
# セキュリティスキャン自動化スクリプト
# Usage: ./scripts/security_scan.sh

set -e

echo "=========================================="
echo "Mirai Knowledge Systems - Security Scan"
echo "=========================================="

cd "$(dirname "$0")/.."

# レポートディレクトリ作成
mkdir -p tests/reports

echo ""
echo "[1/3] Running Bandit (Python Security Linter)..."
echo "----------------------------------------"
if bandit -r app_v2.py schemas.py password_policy.py -f json -o tests/reports/bandit_report.json 2>/dev/null; then
    echo "✅ Bandit: No issues found"
else
    echo "⚠️  Bandit: Issues found (see tests/reports/bandit_report.json)"
    # 重大度HIGHがなければ続行
    high_count=$(python3 -c "import json; d=json.load(open('tests/reports/bandit_report.json')); print(d['metrics']['_totals']['SEVERITY.HIGH'])" 2>/dev/null || echo "0")
    if [ "$high_count" != "0" ]; then
        echo "❌ CRITICAL: $high_count HIGH severity issues found!"
        exit 1
    fi
fi

echo ""
echo "[2/3] Running Safety (Dependency Vulnerability Check)..."
echo "----------------------------------------"
if safety check --output json > tests/reports/safety_report.json 2>&1; then
    echo "✅ Safety: No vulnerable dependencies found"
else
    echo "⚠️  Safety: Check tests/reports/safety_report.json for details"
fi

echo ""
echo "[3/3] Generating Security Summary..."
echo "----------------------------------------"

# サマリー生成
python3 << 'EOF'
import json
from datetime import datetime

print(f"Scan completed at: {datetime.now().isoformat()}")
print()

# Bandit結果
try:
    with open('tests/reports/bandit_report.json') as f:
        bandit = json.load(f)
    totals = bandit['metrics']['_totals']
    print("Bandit Results:")
    print(f"  - HIGH severity:   {totals['SEVERITY.HIGH']}")
    print(f"  - MEDIUM severity: {totals['SEVERITY.MEDIUM']}")
    print(f"  - LOW severity:    {totals['SEVERITY.LOW']}")
    print(f"  - Lines of code:   {totals['loc']}")
except Exception as e:
    print(f"Bandit: Error reading report - {e}")

print()

# Safety結果
try:
    with open('tests/reports/safety_report.json') as f:
        content = f.read()
        if 'vulnerabilities' in content:
            safety = json.loads(content)
            vuln_count = len(safety.get('vulnerabilities', []))
            print(f"Safety Results: {vuln_count} vulnerabilities found")
        else:
            print("Safety Results: No vulnerabilities found")
except Exception as e:
    print(f"Safety: Check report manually - {e}")

print()
print("========================================")
print("Security scan complete!")
print("Reports saved to: tests/reports/")
print("========================================")
EOF

echo ""
echo "Done!"
