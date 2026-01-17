# アラート設定 (Alert Configuration)

## 概要
システム監視とアラート通知の設定手順です。Prometheus + Alertmanager を使用した監視基盤を構築します。

## アラートレベル定義

| レベル | 説明 | 対応時間 | 通知先 |
|--------|------|----------|--------|
| Critical | サービス停止、データ損失 | 15分以内 | SRE + 管理職 |
| Warning | パフォーマンス低下、容量不足 | 1時間以内 | SREチーム |
| Info | 定期メンテナンス、情報通知 | 4時間以内 | 開発チーム |

## Prometheus設定

### prometheus.yml 設定
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'mks-backend'
    static_configs:
      - targets: ['localhost:5100']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:80']
    scrape_interval: 30s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:5432']
    scrape_interval: 30s
```

### rules.yml アラートルール
```yaml
groups:
  - name: mks.rules
    rules:
      # サービスダウン
      - alert: ServiceDown
        expr: up{job="mks-backend"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "MKS Backend service is down"
          description: "MKS Backend has been down for more than 5 minutes."

      # 高レスポンスタイム
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time > 5s for 10 minutes."

      # ディスク容量
      - alert: DiskSpaceLow
        expr: (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space low"
          description: "Disk usage > 90% for 5 minutes."

      # データベース接続
      - alert: DatabaseConnectionFailed
        expr: pg_stat_activity_count{state="active"} < 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failed"
          description: "No active database connections for 5 minutes."
```

## Alertmanager設定

### alertmanager.yml 設定
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@mks-system.com'
  smtp_auth_username: 'alerts@mks-system.com'
  smtp_auth_password: 'your-password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'team-sre'
  routes:
    - match:
        severity: critical
      receiver: 'team-sre-critical'

receivers:
  - name: 'team-sre'
    email_configs:
      - to: 'sre-team@mks-system.com'
        subject: '[{{ .GroupLabels.alertname }}] {{ .Annotations.summary }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Severity: {{ .Labels.severity }}
          {{ end }}

  - name: 'team-sre-critical'
    email_configs:
      - to: 'sre-team@mks-system.com,manager@mks-system.com'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts-critical'
        title: '[CRITICAL] {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          *Severity:* {{ .Labels.severity }}
          {{ end }}
```

## Grafanaダッシュボード

### 主要メトリクス
- **サービス可用性**: uptime, response time
- **リソース使用率**: CPU, Memory, Disk
- **アプリケーション**: request rate, error rate
- **データベース**: connection count, query performance

### ダッシュボード設定例
```json
{
  "dashboard": {
    "title": "MKS System Overview",
    "panels": [
      {
        "title": "Service Uptime",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"mks-backend\"}",
            "legendFormat": "Backend"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## ログ監視設定

### ELK Stack設定

#### Filebeat設定
```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/mks-backend/*.log
    fields:
      service: mks-backend
      level: error

  - type: log
    enabled: true
    paths:
      - /var/log/nginx/*.log
    fields:
      service: nginx

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "mks-%{+yyyy.MM.dd}"
```

#### Logstash設定
```ruby
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "mks-backend" {
    json {
      source => "message"
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "mks-%{+YYYY.MM.dd}"
  }
}
```

#### Kibana設定
- **インデックスパターン**: mks-*
- **可視化**: エラーレート、レスポンスタイム分布
- **アラート**: エラー率上昇時通知

## 自動対応設定

### 自動再起動スクリプト
```bash
#!/bin/bash
# scripts/auto-restart.sh

SERVICE="mks-backend"
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if systemctl is-active --quiet $SERVICE; then
        echo "$SERVICE is running"
        exit 0
    else
        echo "$SERVICE is down, restarting..."
        systemctl restart $SERVICE
        sleep 30
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

echo "Failed to restart $SERVICE after $MAX_RETRIES attempts"
# アラート送信
```

### ログローテーション自動化
```bash
# /etc/logrotate.d/mks-backend
/var/log/mks-backend/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 mks mks
    postrotate
        systemctl reload mks-backend
    endscript
}
```

## アラートテスト

### テスト手順
1. **アラートルールテスト**
   ```bash
   # Prometheusルールテスト
   promtool check rules rules.yml
   ```

2. **通知テスト**
   ```bash
   # Alertmanagerテスト
   curl -X POST http://localhost:9093/api/v1/alerts \
     -H "Content-Type: application/json" \
     -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test alert"}}]'
   ```

3. **統合テスト**
   ```bash
   # サービス停止テスト
   sudo systemctl stop mks-backend
   # アラート確認
   sleep 300
   sudo systemctl start mks-backend
   ```

## 監視メトリクス

### アプリケーション側メトリクス
```python
from prometheus_client import Counter, Histogram, Gauge

# リクエストカウンター
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])

# レスポンスタイム
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

# アクティブ接続数
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')
```

### インフラメトリクス
- **Node Exporter**: CPU, Memory, Disk, Network
- **PostgreSQL Exporter**: 接続数、クエリ性能
- **Nginx Exporter**: リクエスト数、エラーレート

## アラート運用

### 定期レビュー
- **毎週**: アラート精度確認、誤検知分析
- **毎月**: 閾値調整、アラートルール見直し
- **毎四半期**: 新しい監視項目追加

### アラート対応フロー
1. **アラート受信** → 2. **重大度判断** → 3. **担当者通知** → 4. **診断開始** → 5. **対応実行** → 6. **復旧確認** → 7. **事後レビュー**

### エスカレーションポリシー
- **Critical**: 15分以内に管理職へエスカレーション
- **Warning**: 1時間以内にチームリーダーへ報告
- **Info**: 通常業務時間内に確認</content>
<parameter name="filePath">docs/11_運用保守(Operations)/12_アラート設定(Alert-Configuration).md