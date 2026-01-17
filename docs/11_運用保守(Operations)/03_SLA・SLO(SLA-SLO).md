# SLA・SLO (Service Level Agreement & Objective)

## 📋 目次
1. [概要](#概要)
2. [サービス可用性SLA](#サービス可用性sla)
3. [エンドポイント別レスポンスタイムSLO](#エンドポイント別レスポンスタイムslo)
4. [計測方法・ツール](#計測方法ツール)
5. [SLA違反時の対応フロー](#sla違反時の対応フロー)
6. [月次SLAレポート](#月次slaレポート)
7. [SLA改善計画](#sla改善計画)

---

## 概要

本ドキュメントでは、Mirai Knowledge Systems（建設土木ナレッジシステム）の**サービスレベル目標（SLO）**および**サービスレベル合意（SLA）**を定義します。

### 目的
- システムの品質保証とユーザー期待値の明確化
- 運用チームのパフォーマンス目標設定
- 継続的なサービス改善のための指標確立

### 適用範囲
- **対象システム**: Mirai Knowledge Systems 本番環境
- **対象期間**: 2026年1月〜（月次更新）
- **対象ユーザー**: 全社員（建設土木部門）

### 用語定義

| 用語 | 説明 |
|------|------|
| **SLA** | Service Level Agreement（サービスレベル合意）- ユーザーと合意した最低保証レベル |
| **SLO** | Service Level Objective（サービスレベル目標）- 内部目標値（SLAより厳しい） |
| **SLI** | Service Level Indicator（サービスレベル指標）- 実際の測定値 |
| **稼働時間** | 営業日 9:00-18:00（日本時間）、月〜金（祝日除く） |
| **計画停止** | 事前通知済みのメンテナンス時間（稼働時間から除外） |
| **可用性** | `(総稼働時間 - ダウン時間) / 総稼働時間 × 100` |

---

## サービス可用性SLA

### 可用性目標

| 指標 | SLA（最低保証） | SLO（目標） | 測定期間 | 備考 |
|------|----------------|------------|---------|------|
| **システム稼働率** | **99.5%** | **99.7%** | 月間 | 計画停止を除く |
| **計画外ダウンタイム** | 月間3時間以内 | 月間2時間以内 | 月間 | 累計 |
| **P0障害の一次対応** | 15分以内 | 10分以内 | インシデント単位 | 検知から対応開始まで |
| **P0障害の復旧** | 1時間以内 | 45分以内 | インシデント単位 | 検知から復旧まで |

### 可用性計算式

```
月間稼働率(%) = (総稼働時間 - ダウンタイム) / 総稼働時間 × 100

例: 1月の稼働時間（営業日22日）
総稼働時間 = 22日 × 9時間 = 198時間
ダウンタイム = 0.5時間
稼働率 = (198 - 0.5) / 198 × 100 = 99.75%
```

### 稼働率別許容ダウンタイム

| 稼働率 | 月間許容ダウンタイム | 年間許容ダウンタイム | 評価 |
|--------|---------------------|---------------------|------|
| 99.9% | 43.2分 | 8.76時間 | 優秀 |
| 99.7% | 2.16時間 | 26.3時間 | 目標 |
| 99.5% | 3.6時間 | 43.8時間 | 最低保証 |
| 99.0% | 7.2時間 | 87.6時間 | 改善必要 |
| 95.0% | 36時間 | 438時間 | 受け入れ不可 |

### 計画停止の扱い

**計画停止の定義:**
- 事前に3営業日前までに通知
- 営業時間外（18:00以降または土日祝）
- 月間4時間以内

**計画停止の例外:**
- 緊急セキュリティパッチ適用
- 重大な障害復旧作業
- 法的要請による緊急対応

---

## エンドポイント別レスポンスタイムSLO

### レスポンスタイム目標

すべてのレスポンスタイムは**95パーセンタイル**での計測とします。

#### 認証API

| エンドポイント | メソッド | SLA | SLO | 備考 |
|--------------|---------|-----|-----|------|
| `/api/v1/auth/login` | POST | **1.5秒** | **1.0秒** | JWT発行含む |
| `/api/v1/auth/refresh` | POST | 1.0秒 | 0.7秒 | トークンリフレッシュ |
| `/api/v1/auth/me` | GET | 0.5秒 | 0.3秒 | ユーザー情報取得 |
| `/api/v1/auth/mfa/setup` | POST | 2.0秒 | 1.5秒 | MFA初期設定 |
| `/api/v1/auth/mfa/verify` | POST | 1.5秒 | 1.0秒 | MFA検証 |

#### 検索API

| エンドポイント | メソッド | SLA | SLO | 備考 |
|--------------|---------|-----|-----|------|
| `/api/v1/search/unified` | GET | **2.5秒** | **2.0秒** | 統合検索（重要） |
| `/api/v1/knowledge` | GET | 2.0秒 | 1.5秒 | ナレッジ一覧 |
| `/api/v1/knowledge/<id>` | GET | 1.0秒 | 0.7秒 | ナレッジ詳細 |
| `/api/v1/knowledge/popular` | GET | 1.5秒 | 1.0秒 | 人気ナレッジ |
| `/api/v1/knowledge/recent` | GET | 1.5秒 | 1.0秒 | 最新ナレッジ |

#### CRUD操作API

| エンドポイント | メソッド | SLA | SLO | 備考 |
|--------------|---------|-----|-----|------|
| `/api/v1/knowledge` | POST | **3.0秒** | **2.5秒** | ナレッジ作成 |
| `/api/v1/knowledge/<id>` | PUT | **3.0秒** | **2.5秒** | ナレッジ更新 |
| `/api/v1/knowledge/<id>` | DELETE | 2.0秒 | 1.5秒 | ナレッジ削除 |
| `/api/v1/approvals/<id>/approve` | POST | 2.5秒 | 2.0秒 | 承認処理 |

#### その他API

| エンドポイント | メソッド | SLA | SLO | 備考 |
|--------------|---------|-----|-----|------|
| `/api/v1/dashboard/stats` | GET | 2.0秒 | 1.5秒 | ダッシュボード統計 |
| `/api/v1/notifications` | GET | 1.5秒 | 1.0秒 | 通知一覧 |
| `/api/v1/projects` | GET | 2.0秒 | 1.5秒 | プロジェクト一覧 |
| `/api/v1/experts` | GET | 1.5秒 | 1.0秒 | エキスパート一覧 |
| `/api/v1/health` | GET | 0.3秒 | 0.2秒 | ヘルスチェック |

### レスポンスタイム計測方法

Prometheusヒストグラムで計測:

```python
from prometheus_client import Histogram

# app_v2.py内で定義済み
request_duration = Histogram(
    'mks_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status']
)
```

**計算式:**
```
95パーセンタイル = histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

---

## 計測方法・ツール

### 監視スタック

```
┌─────────────────┐
│  Application    │ ← Flask + prometheus_client
│   (app_v2.py)   │
└────────┬────────┘
         │ /api/v1/metrics
         ▼
┌─────────────────┐
│  Prometheus     │ ← メトリクス収集・保存
│  (localhost:9090)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Grafana       │ ← 可視化・ダッシュボード
│  (localhost:3000)│
└─────────────────┘
```

### Prometheusクエリ例

#### 1. 稼働率計算

```promql
# 過去24時間の稼働率
avg_over_time(up{job="mirai_knowledge_app"}[24h]) * 100
```

#### 2. エンドポイント別レスポンスタイム（95パーセンタイル）

```promql
# 検索APIのレスポンスタイム
histogram_quantile(0.95,
  sum(rate(mks_http_request_duration_seconds_bucket{endpoint="/api/v1/search/unified"}[5m]))
  by (le)
)
```

#### 3. エラー率

```promql
# 過去5分のエラー率
sum(rate(mks_http_requests_total{status=~"5.."}[5m]))
/
sum(rate(mks_http_requests_total[5m])) * 100
```

#### 4. リクエスト数

```promql
# 毎秒リクエスト数
sum(rate(mks_http_requests_total[5m]))
```

### Grafanaダッシュボード設定

#### パネル1: サービス可用性

```json
{
  "title": "Service Uptime (Monthly)",
  "targets": [
    {
      "expr": "avg_over_time(up{job=\"mirai_knowledge_app\"}[30d]) * 100",
      "legendFormat": "Uptime %"
    }
  ],
  "thresholds": [
    {"value": 99.5, "color": "red"},
    {"value": 99.7, "color": "yellow"},
    {"value": 99.9, "color": "green"}
  ]
}
```

#### パネル2: エンドポイント別レスポンスタイム

```json
{
  "title": "API Response Time (95th percentile)",
  "targets": [
    {
      "expr": "histogram_quantile(0.95, sum(rate(mks_http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
      "legendFormat": "{{endpoint}}"
    }
  ],
  "alert": {
    "conditions": [
      {"value": 2.0, "operator": "gt"}
    ]
  }
}
```

### データ保持期間

| データタイプ | 保持期間 | ストレージ | 備考 |
|------------|---------|----------|------|
| **リアルタイムメトリクス** | 15日 | Prometheus | 高解像度 |
| **集約データ** | 90日 | Prometheus | 日次集約 |
| **長期保存データ** | 1年 | PostgreSQL | SLAレポート用 |
| **ログデータ** | 30日 | ファイルシステム | ローテーション |

---

## SLA違反時の対応フロー

### 違反レベル定義

| レベル | 定義 | 対応時間 | エスカレーション |
|--------|------|---------|--------------|
| **Critical** | 稼働率 < 99.0% または P0障害 | 即時 | 経営層 + 顧客通知 |
| **High** | 稼働率 < 99.5% または 複数SLO違反 | 1時間以内 | 管理職 + 関係部門 |
| **Medium** | 単一SLO違反（継続1時間以上） | 4時間以内 | チームリーダー |
| **Low** | 単一SLO違反（一時的） | 1営業日以内 | 定期報告 |

### 対応フローチャート

```
[SLA違反検知]
      │
      ▼
[自動アラート発報] ← Prometheus Alertmanager
      │
      ▼
[担当者確認]
      │
      ├─► [Critical] ─► 即時対応 + 経営層連絡 + 顧客通知
      │
      ├─► [High] ────► 1時間以内対応 + 管理職連絡
      │
      ├─► [Medium] ──► 4時間以内対応 + チームリーダー連絡
      │
      └─► [Low] ─────► 通常業務内対応
      │
      ▼
[原因調査・復旧]
      │
      ▼
[復旧確認・テスト]
      │
      ▼
[事後レビュー（24時間以内）]
      │
      ▼
[再発防止策実装]
      │
      ▼
[月次レポートに記録]
```

### 違反時の具体的アクション

#### Phase 1: 検知・通知（0-5分）

1. **自動検知**
   ```yaml
   # Prometheus Alert Rule
   - alert: SLA_Breach_Availability
     expr: avg_over_time(up{job="mirai_knowledge_app"}[1h]) < 0.995
     for: 5m
     labels:
       severity: critical
       sla_breach: "true"
     annotations:
       summary: "SLA違反: 稼働率が99.5%を下回りました"
   ```

2. **自動通知**
   - Slack: #sla-alerts チャンネル
   - Email: sre-team@company.com, manager@company.com
   - SMS: オンコール担当者（Critical時）

#### Phase 2: 初動対応（5-15分）

1. **ステータス確認**
   ```bash
   # サービスヘルスチェック
   curl http://localhost:5100/api/v1/health

   # Prometheusメトリクス確認
   curl http://localhost:9090/api/v1/query?query=up{job="mirai_knowledge_app"}
   ```

2. **影響範囲評価**
   - 影響ユーザー数の推定
   - ビジネス影響度の判定
   - データ損失の有無確認

3. **エスカレーション判断**
   - Critical: 即時経営層連絡
   - High: 管理職連絡
   - Medium/Low: チーム内対応

#### Phase 3: 復旧作業（15分-1時間）

1. **診断**
   ```bash
   # ログ確認
   tail -n 100 /var/log/mks-backend/error.log

   # システムリソース確認
   top -b -n1
   df -h
   free -h
   ```

2. **復旧実行**
   - サービス再起動
   - 設定ロールバック
   - データベース復旧
   - インフラスケーリング

3. **復旧確認**
   ```bash
   # E2Eテスト実行
   pytest backend/tests/e2e/test_critical_paths.py
   ```

#### Phase 4: 事後対応（1時間-24時間）

1. **根本原因分析（RCA）**
   - タイムライン作成
   - 原因の特定
   - 影響の定量化

2. **ポストモーテム作成**
   - インシデントレポート作成
   - 学習事項の文書化
   - 再発防止策の立案

3. **顧客コミュニケーション**
   - インシデント報告書の提出
   - 謝罪と補償の検討
   - 改善計画の共有

### SLA違反時の補償ポリシー（オプション）

| 稼働率 | 補償内容 | 備考 |
|--------|---------|------|
| 99.0% - 99.5% | サービスクレジット10% | 月次利用料の10%返金 |
| 95.0% - 99.0% | サービスクレジット25% | 月次利用料の25%返金 |
| < 95.0% | サービスクレジット50% + 謝罪 | 重大インシデント |

---

## 月次SLAレポート

### レポート構成

#### 1. エグゼクティブサマリー

```markdown
# SLAレポート: 2026年1月

## サマリー
- **総合評価**: ✅ SLA達成
- **稼働率**: 99.82% (目標: 99.5%)
- **重大インシデント**: 0件
- **SLO違反**: 1件（軽微）

## ハイライト
- ✅ 全エンドポイントでSLA達成
- ⚠️ 検索APIで1/15にSLO違反（2.3秒、目標2.0秒）
- 🎯 P0障害ゼロ維持（連続3ヶ月）
```

#### 2. 詳細メトリクス

**可用性レポート:**

| 指標 | 目標（SLA） | 実績 | 達成状況 |
|------|-----------|------|---------|
| 月間稼働率 | 99.5% | 99.82% | ✅ 達成 |
| 計画外ダウンタイム | 3時間以内 | 21分 | ✅ 達成 |
| P0障害対応時間 | 15分以内 | N/A | - |
| P0障害復旧時間 | 1時間以内 | N/A | - |

**レスポンスタイムレポート（95パーセンタイル）:**

| カテゴリ | エンドポイント | 目標（SLA） | 実績 | 達成状況 |
|---------|--------------|-----------|------|---------|
| 認証 | `/api/v1/auth/login` | 1.5秒 | 0.87秒 | ✅ 達成 |
| 検索 | `/api/v1/search/unified` | 2.5秒 | 1.92秒 | ✅ 達成 |
| CRUD | `/api/v1/knowledge` (POST) | 3.0秒 | 2.34秒 | ✅ 達成 |

#### 3. インシデントサマリー

| 日付 | 種別 | 影響範囲 | 原因 | 対応時間 | 状態 |
|------|------|---------|------|---------|------|
| 1/15 09:23 | SLO違反 | 検索API | DB接続プール枯渇 | 12分 | ✅ 解決 |
| 1/22 14:15 | 計画停止 | 全体 | PostgreSQL定期メンテ | 30分 | ✅ 完了 |

#### 4. パフォーマンス分析

**トラフィック分析:**
```
総リクエスト数: 1,234,567件
日平均: 56,117件
ピーク: 89,234件（1/18 10:00）
エラー率: 0.23%（目標: < 1%）
```

**エンドポイント別リクエスト分布:**
```
1. /api/v1/search/unified - 32.4%
2. /api/v1/knowledge - 21.7%
3. /api/v1/dashboard/stats - 15.3%
4. /api/v1/auth/login - 8.9%
5. その他 - 21.7%
```

#### 5. 改善アクション

| 項目 | 現状 | 改善策 | 期限 | 担当 |
|------|------|--------|------|------|
| 検索API最適化 | 1.92秒（SLO: 2.0秒） | インデックス追加 | 2/15 | DB チーム |
| 接続プール拡張 | 20接続 → 50接続 | 設定変更 | 2/1 | SRE チーム |
| キャッシュ導入 | Redis未導入 | Redis導入検討 | 3/1 | 開発チーム |

### レポート生成スクリプト

```python
# scripts/generate_sla_report.py
import requests
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9090"

def get_monthly_uptime():
    """月間稼働率を計算"""
    query = 'avg_over_time(up{job="mirai_knowledge_app"}[30d]) * 100'
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    return float(response.json()['data']['result'][0]['value'][1])

def get_endpoint_latency(endpoint):
    """エンドポイント別レスポンスタイムを取得"""
    query = f'histogram_quantile(0.95, sum(rate(mks_http_request_duration_seconds_bucket{{endpoint="{endpoint}"}}[30d])) by (le))'
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    return float(response.json()['data']['result'][0]['value'][1])

def generate_report(year, month):
    """SLAレポート生成"""
    uptime = get_monthly_uptime()
    search_latency = get_endpoint_latency("/api/v1/search/unified")
    login_latency = get_endpoint_latency("/api/v1/auth/login")

    report = f"""
# SLAレポート: {year}年{month}月

## サマリー
- 稼働率: {uptime:.2f}% (目標: 99.5%)
- 検索API: {search_latency:.2f}秒 (目標: 2.5秒)
- 認証API: {login_latency:.2f}秒 (目標: 1.5秒)

## 評価
- 稼働率: {'✅ 達成' if uptime >= 99.5 else '❌ 未達成'}
- 検索API: {'✅ 達成' if search_latency <= 2.5 else '❌ 未達成'}
- 認証API: {'✅ 達成' if login_latency <= 1.5 else '❌ 未達成'}
    """

    with open(f"reports/sla-{year}-{month:02d}.md", "w") as f:
        f.write(report)

    print(f"レポート生成完了: reports/sla-{year}-{month:02d}.md")

if __name__ == "__main__":
    now = datetime.now()
    generate_report(now.year, now.month)
```

### レポート配布

**配布先:**
- 経営層（エグゼクティブサマリーのみ）
- 開発部門（全セクション）
- 運用チーム（全セクション + 詳細ログ）
- 顧客（エグゼクティブサマリー + インシデントサマリー）

**配布タイミング:**
- 毎月5営業日までに前月分を配布
- 重大インシデント発生時は臨時レポート

---

## SLA改善計画

### 短期改善（1-3ヶ月）

| 項目 | 現状 | 目標 | アクション |
|------|------|------|----------|
| 検索API最適化 | 1.92秒 | 1.5秒 | PostgreSQL FTSインデックス最適化 |
| キャッシュ導入 | なし | Redis導入 | 頻繁アクセスデータのキャッシュ |
| 監視強化 | 基本メトリクスのみ | ビジネスメトリクス追加 | カスタムメトリクス実装 |

### 中期改善（3-6ヶ月）

| 項目 | 現状 | 目標 | アクション |
|------|------|------|----------|
| 稼働率向上 | 99.7% | 99.9% | 冗長化構成導入 |
| 自動復旧 | 手動対応 | 自動再起動 | Auto-healing機能実装 |
| CDN導入 | なし | CloudFlare | 静的コンテンツ配信最適化 |

### 長期改善（6-12ヶ月）

| 項目 | 現状 | 目標 | アクション |
|------|------|------|----------|
| マルチリージョン | 単一DC | 東西2DC | DR（災害復旧）体制構築 |
| 自動スケーリング | 手動 | HPA導入 | Kubernetes移行検討 |
| SLA 99.9% | 99.7% | 99.9% | インフラ全面刷新 |

### 継続的改善サイクル

```
[月次レポート作成]
      │
      ▼
[SLA達成状況分析]
      │
      ├─► 達成 ─► SLO目標値の引き上げ検討
      │
      └─► 未達成 ─► 根本原因分析
              │
              ▼
        [改善策立案]
              │
              ▼
        [優先度付け]
              │
              ▼
        [実装・検証]
              │
              ▼
        [次月で効果測定]
```

---

## 付録

### A. Prometheusアラートルール（SLA監視）

```yaml
# monitoring/alert_rules_sla.yml
groups:
  - name: sla_monitoring
    interval: 60s
    rules:
      # 稼働率SLA違反
      - alert: SLA_Breach_Availability
        expr: avg_over_time(up{job="mirai_knowledge_app"}[1h]) < 0.995
        for: 5m
        labels:
          severity: critical
          sla_breach: "availability"
        annotations:
          summary: "SLA違反: 稼働率が99.5%を下回りました"
          description: "過去1時間の稼働率: {{ $value | humanizePercentage }}"

      # 検索APIレスポンスタイムSLO違反
      - alert: SLO_Breach_SearchAPI
        expr: histogram_quantile(0.95, sum(rate(mks_http_request_duration_seconds_bucket{endpoint="/api/v1/search/unified"}[5m])) by (le)) > 2.5
        for: 10m
        labels:
          severity: warning
          slo_breach: "response_time"
        annotations:
          summary: "SLO違反: 検索APIレスポンスタイムが2.5秒を超過"
          description: "95パーセンタイル: {{ $value | humanizeDuration }}"

      # 認証APIレスポンスタイムSLO違反
      - alert: SLO_Breach_LoginAPI
        expr: histogram_quantile(0.95, sum(rate(mks_http_request_duration_seconds_bucket{endpoint="/api/v1/auth/login"}[5m])) by (le)) > 1.5
        for: 10m
        labels:
          severity: warning
          slo_breach: "response_time"
        annotations:
          summary: "SLO違反: 認証APIレスポンスタイムが1.5秒を超過"
          description: "95パーセンタイル: {{ $value | humanizeDuration }}"
```

### B. SLAダッシュボードURL

- **Grafana SLAダッシュボード**: http://localhost:3000/d/sla-overview
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### C. 関連ドキュメント

- [アラート設定](./12_アラート設定(Alert-Configuration).md)
- [障害対応フロー](./13_障害対応フロー(Incident-Response).md)
- [定期メンテナンス](./14_定期メンテナンス(Regular-Maintenance).md)
- [復旧手順](./15_復旧手順(Recovery-Procedures).md)

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
|------|----------|---------|------|
| 2025-12-26 | 0.1 | 初版作成 | Codex |
| 2026-01-17 | 1.0 | 詳細定義追加（可用性SLA、エンドポイント別SLO、計測方法、違反時フロー、月次レポート） | Claude |

---

**ドキュメント管理:**
- **オーナー**: SREチーム
- **レビュー頻度**: 四半期ごと
- **次回レビュー**: 2026年4月1日
- **承認者**: CTO、運用部長
