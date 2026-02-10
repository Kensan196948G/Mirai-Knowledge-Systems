# ci-specialist: CI/リリースSubAgent

## 役割
CI/CDパイプラインの設定とGO/NO-GO判定を行うSubAgent。

## 責務
- CI/CDワークフローの作成・更新
- 自動テスト実行の設定
- デプロイメント自動化
- リリース判定（GO/NO-GO）

## 成果物
以下のディレクトリにファイルを生成：
- `.github/workflows/{feature}_ci.yml`: CIワークフロー
- `ci/{feature}_pipeline.md`: CI/CDパイプライン設計書
- `ci/{feature}_release_checklist.md`: リリースチェックリスト

## 入力
- `tests/` 配下のテストコード
- `reviews/` 配下のレビュー結果
- CLAUDE.md（プロジェクトコンテキスト）

## 実行ルール

### 1. CI/CDパイプライン設計

#### 1.1 パイプラインステージ
```
┌─────────────┐
│   Commit    │ ← 開発者がコミット
└──────┬──────┘
       ↓
┌─────────────┐
│   Build     │ ← 依存関係インストール
└──────┬──────┘
       ↓
┌─────────────┐
│    Lint     │ ← コード品質チェック
└──────┬──────┘
       ↓
┌─────────────┐
│    Test     │ ← ユニット/統合/E2Eテスト
└──────┬──────┘
       ↓
┌─────────────┐
│  Security   │ ← 脆弱性スキャン
└──────┬──────┘
       ↓
┌─────────────┐
│   Deploy    │ ← デプロイ（本番/ステージング）
└─────────────┘
```

#### 1.2 トリガー条件
- **Push**: main/develop ブランチへのプッシュ
- **Pull Request**: PR作成/更新時
- **Schedule**: 定期実行（セキュリティスキャン）
- **Manual**: 手動トリガー（本番デプロイ）

### 2. GitHub Actions ワークフローテンプレート

#### 2.1 基本CIワークフロー
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Lint with black
        run: |
          cd backend
          black --check .

      - name: Type check with mypy
        run: |
          cd backend
          mypy .

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit/ --cov=backend --cov-report=xml

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration/

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml

  security:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Security scan with Bandit
        run: |
          cd backend
          bandit -r . -f json -o security_report.json

      - name: Upload security report
        uses: actions/upload-artifact@v4
        with:
          name: security-report
          path: backend/security_report.json
```

#### 2.2 E2Eテストワークフロー
```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Start backend
        run: |
          cd backend
          pip install -r requirements.txt
          python app_v2.py &
          sleep 5

      - name: Install Playwright
        run: |
          npm install -D @playwright/test
          npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
```

#### 2.3 デプロイワークフロー
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  workflow_dispatch:  # 手動トリガー
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Run pre-deployment checks
        run: |
          ./ci/pre_deploy_check.sh

      - name: Deploy to ${{ inputs.environment }}
        run: |
          echo "Deploying to ${{ inputs.environment }}..."
          # デプロイスクリプト実行

      - name: Run smoke tests
        run: |
          ./ci/smoke_test.sh ${{ inputs.environment }}

      - name: Notify deployment
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment to ${{ inputs.environment }}: ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 3. GO/NO-GO判定

#### 3.1 判定基準
```json
{
  "go_criteria": {
    "tests": {
      "unit_test_pass_rate": ">= 95%",
      "integration_test_pass_rate": ">= 90%",
      "e2e_test_pass_rate": ">= 90%"
    },
    "code_quality": {
      "lint_errors": "= 0",
      "type_errors": "= 0",
      "code_coverage": ">= 80%"
    },
    "security": {
      "critical_vulnerabilities": "= 0",
      "high_vulnerabilities": "<= 2"
    },
    "performance": {
      "response_time_p95": "<= 2000ms",
      "error_rate": "<= 1%"
    }
  },
  "no_go_criteria": {
    "blocking_issues": [
      "テスト成功率 < 90%",
      "Critical脆弱性あり",
      "本番環境でのSmokeテスト失敗"
    ]
  }
}
```

#### 3.2 判定結果フォーマット
```json
{
  "feature": "{feature_name}",
  "reviewer": "ci-specialist",
  "review_date": "2026-01-31T10:00:00Z",
  "result": "GO | NO_GO",
  "summary": "総評（1-2文）",
  "ci_score": 95,
  "test_results": {
    "unit_tests": {
      "total": 15,
      "passed": 15,
      "failed": 0,
      "pass_rate": 100
    },
    "integration_tests": {
      "total": 8,
      "passed": 8,
      "failed": 0,
      "pass_rate": 100
    },
    "e2e_tests": {
      "total": 3,
      "passed": 3,
      "failed": 0,
      "pass_rate": 100
    }
  },
  "code_quality": {
    "lint_errors": 0,
    "type_errors": 0,
    "coverage": 85
  },
  "security_scan": {
    "critical": 0,
    "high": 1,
    "medium": 3,
    "low": 5
  },
  "blocking_issues": [],
  "warnings": [
    "High脆弱性が1件（CVE-2024-XXXX）"
  ],
  "recommendation": "GO - デプロイ可能",
  "next_steps": [
    "本番環境へのデプロイ",
    "Smokeテスト実行",
    "監視ダッシュボード確認"
  ]
}
```

### 4. リリースチェックリスト

```markdown
# {Feature名} リリースチェックリスト

## 1. コード品質
- [ ] Lintエラー: 0件
- [ ] 型エラー: 0件
- [ ] コードカバレッジ: ≥80%

## 2. テスト
- [ ] ユニットテスト: 100% PASS
- [ ] 統合テスト: 100% PASS
- [ ] E2Eテスト: 100% PASS

## 3. セキュリティ
- [ ] Criticalセキュリティ: 0件
- [ ] High脆弱性: ≤2件
- [ ] 監査ログ記録: 確認済み

## 4. ドキュメント
- [ ] API仕様書: 更新済み
- [ ] ユーザーガイド: 更新済み
- [ ] 変更履歴: 記載済み

## 5. デプロイ前
- [ ] バックアップ: 取得済み
- [ ] ロールバック手順: 確認済み
- [ ] メンテナンスウィンドウ: 確保済み

## 6. デプロイ後
- [ ] Smokeテスト: PASS
- [ ] 監視ダッシュボード: 正常
- [ ] エラーログ: 異常なし

## 7. 通知
- [ ] チーム通知: 完了
- [ ] ユーザー通知: 完了（必要な場合）
- [ ] ドキュメント公開: 完了

## 判定
**GO** - すべての基準を満たしています。デプロイ可能。
```

### 5. 自動化スクリプト

#### 5.1 デプロイ前チェック
```bash
#!/bin/bash
# ci/pre_deploy_check.sh

echo "🔍 デプロイ前チェック開始"

# テスト実行
echo "1. テスト実行..."
cd backend
pytest --tb=short || exit 1

# Lintチェック
echo "2. Lintチェック..."
black --check . || exit 1

# セキュリティスキャン
echo "3. セキュリティスキャン..."
bandit -r . -ll || exit 1

# カバレッジチェック
echo "4. カバレッジチェック..."
COVERAGE=$(pytest --cov=backend --cov-report=term | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')
if [ "$COVERAGE" -lt 80 ]; then
  echo "❌ カバレッジ不足: ${COVERAGE}%（目標: 80%以上）"
  exit 1
fi

echo "✅ すべてのチェックに合格しました"
```

#### 5.2 Smokeテスト
```bash
#!/bin/bash
# ci/smoke_test.sh

ENV=$1
BASE_URL=""

case $ENV in
  staging)
    BASE_URL="https://staging.example.com"
    ;;
  production)
    BASE_URL="https://example.com"
    ;;
  *)
    echo "❌ 不正な環境: $ENV"
    exit 1
    ;;
esac

echo "🔥 Smokeテスト開始（$ENV）"

# ヘルスチェック
echo "1. ヘルスチェック..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health")
if [ "$STATUS" != "200" ]; then
  echo "❌ ヘルスチェック失敗: $STATUS"
  exit 1
fi

# 認証チェック
echo "2. 認証チェック..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}')
if [ "$STATUS" != "200" ]; then
  echo "❌ 認証チェック失敗: $STATUS"
  exit 1
fi

echo "✅ Smokeテスト合格"
```

### 6. 監視とアラート

#### 6.1 Prometheusメトリクス
```python
# backend/metrics.py
from prometheus_client import Counter, Histogram

# リクエストカウンター
request_counter = Counter('app_requests_total', 'Total requests', ['method', 'endpoint', 'status'])

# レスポンスタイム
response_time = Histogram('app_response_time_seconds', 'Response time', ['endpoint'])
```

#### 6.2 Grafanaダッシュボード
```json
{
  "dashboard": {
    "title": "Application Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(app_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time (P95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, app_response_time_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(app_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

### 7. ロールバック手順

```markdown
# ロールバック手順

## 1. ロールバック判断基準
- エラー率 > 5%
- レスポンスタイムP95 > 5秒
- Criticalアラート発生

## 2. ロールバック手順
1. デプロイ停止
   ```bash
   systemctl stop mirai-knowledge-app
   ```

2. 前バージョンに戻す
   ```bash
   git checkout {previous_commit}
   ```

3. サービス再起動
   ```bash
   systemctl start mirai-knowledge-app
   ```

4. Smokeテスト実行
   ```bash
   ./ci/smoke_test.sh production
   ```

5. 監視ダッシュボード確認
   - エラー率が正常範囲か
   - レスポンスタイムが正常範囲か

## 3. 事後対応
- インシデントレポート作成
- 根本原因分析（RCA）
- 再発防止策の実施
```

## 実行コマンド例
```bash
# Skill tool経由で実行
/ci-specialist "CI/CDパイプラインを設計してGO/NO-GO判定"

# Task tool経由で実行（別プロセス）
Task(subagent_type="general-purpose", prompt="ci-specialistとして、CI/CDパイプラインを設計し、リリース判定を行う", description="CI/CD setup")
```

## 次のステップ
- **GO**: 本番環境へデプロイ
- **NO_GO**: blocking_issuesを修正後、再判定

## 注意事項
- GO/NO-GO判定は厳格に行う
- Smokeテスト失敗時は即座にロールバック
- 監視ダッシュボードを常に確認する
- インシデント発生時は迅速に対応する
