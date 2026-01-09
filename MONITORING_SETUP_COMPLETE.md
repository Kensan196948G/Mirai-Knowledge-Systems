# Prometheus/Grafana 監視アラート設定完了ガイド

**作成日**: 2026-01-09
**バージョン**: 1.0.0
**対象システム**: Mirai Knowledge Systems

---

## 📋 目次

1. [概要](#概要)
2. [実装された監視機能](#実装された監視機能)
3. [Prometheusアラートルール](#prometheusアラートルール)
4. [Alertmanager設定](#alertmanager設定)
5. [Grafanaダッシュボード](#grafanaダッシュボード)
6. [監視スクリプト](#監視スクリプト)
7. [セットアップ手順](#セットアップ手順)
8. [アラート通知先の追加方法](#アラート通知先の追加方法)
9. [トラブルシューティング](#トラブルシューティング)

---

## 概要

Mirai Knowledge SystemsのPrometheus/Grafana監視アラート設定が完了しました。本ドキュメントは、監視システムの構成、使い方、カスタマイズ方法を説明します。

### 主要コンポーネント

```
monitoring/
├── prometheus/
│   └── alerts.yml              # Prometheusアラートルール（30種類以上）
├── alertmanager/
│   └── alertmanager.yml        # Alertmanager設定（6種類のレシーバー）
└── grafana/
    └── dashboards/
        └── mirai-knowledge-dashboard.json  # Grafanaダッシュボード（11パネル）

scripts/
└── health-monitor.sh           # ヘルスチェックスクリプト
```

---

## 実装された監視機能

### 1. システムリソース監視

| メトリクス | 警告閾値 | 危機閾値 | 備考 |
|-----------|----------|----------|------|
| CPU使用率 | 80% | 90% | 10分間継続で警告 |
| メモリ使用率 | 90% | 95% | 5分間継続で警告 |
| ディスク使用率 | 85% | 95% | 5分間継続で警告 |

**アラート例**:
- `HighCPUUsage`: CPU使用率が80%を超えた
- `CriticalMemoryUsage`: メモリ使用率が95%を超えた
- `DiskSpaceCritical`: ディスク使用率が95%を超えた

### 2. アプリケーション監視

| メトリクス | 警告閾値 | 危機閾値 | 備考 |
|-----------|----------|----------|------|
| エラー発生率 | - | 0.1/秒 | 5分間の平均 |
| API応答時間(p95) | 2秒 | 5秒 | 95パーセンタイル |
| HTTP 5xxエラー率 | - | 5% | 全リクエストに対する割合 |
| HTTP 4xxエラー率 | 20% | - | 全リクエストに対する割合 |

**アラート例**:
- `HighErrorRate`: エラー発生率が0.1/秒を超えた
- `SlowAPIResponse`: API応答時間が2秒を超えた
- `HighHTTP5xxRate`: 5xxエラーが5%を超えた

### 3. データベース監視

| メトリクス | 警告閾値 | 危機閾値 | 備考 |
|-----------|----------|----------|------|
| 接続プール使用数 | 8/10 | 10/10 | 最大接続数 |
| クエリ時間(p95) | 1秒 | 3秒 | 95パーセンタイル |
| DB エラー率 | - | 0.05/秒 | 5分間の平均 |

**アラート例**:
- `DatabaseConnectionPoolHigh`: 接続数が8以上
- `DatabaseQuerySlow`: クエリ時間が1秒を超えた
- `HighDatabaseErrorRate`: DBエラーが0.05/秒を超えた

### 4. サービス稼働監視

| メトリクス | 警告閾値 | 危機閾値 | 備考 |
|-----------|----------|----------|------|
| サービスステータス | - | ダウン | 1分間応答なし |
| リクエスト数 | 100/分 | - | 情報アラート |
| リクエストなし | 10分間 | - | 異常検知 |

**アラート例**:
- `ServiceDown`: サービスが応答しない
- `HighRequestRate`: リクエスト数が通常より多い
- `NoRequestsReceived`: リクエストが受信されていない

### 5. セキュリティ監視

| メトリクス | 警告閾値 | 危機閾値 | 備考 |
|-----------|----------|----------|------|
| ログイン失敗率 | 5/秒 | 10/秒 | 5分間の平均 |
| CSRF失敗率 | 1/秒 | - | 5分間の平均 |

**アラート例**:
- `HighLoginFailureRate`: ログイン失敗が頻発
- `SuspiciousLoginAttempts`: 不審なログイン試行を検出
- `HighCSRFFailureRate`: CSRF検証失敗が多い

### 6. バックアップ監視

| メトリクス | 警告閾値 | 危機閾値 | 備考 |
|-----------|----------|----------|------|
| 最終バックアップ時刻 | 24時間 | - | 1時間継続で警告 |
| バックアップ失敗 | - | 1回以上 | 即座にアラート |

**アラート例**:
- `BackupNotRunning`: 24時間バックアップが実行されていない
- `BackupFailed`: バックアップが失敗した

---

## Prometheusアラートルール

### ファイル構造

```yaml
# monitoring/prometheus/alerts.yml
groups:
  - name: mirai_knowledge_system_alerts
    interval: 30s
    rules:
      - alert: HighMemoryUsage
        expr: mks_system_memory_percent > 90
        for: 5m
        labels:
          severity: warning
          component: system
          category: resource
        annotations:
          summary: "メモリ使用率が高い"
          description: "メモリ使用率が90%を超えています"
```

### アラートの重要度

| severity | 説明 | 通知先 | 例 |
|----------|------|--------|-----|
| **critical** | 即座に対応が必要 | Email + Webhook | ServiceDown, DiskSpaceCritical |
| **warning** | 早めの対応が推奨 | Email + Webhook | HighMemoryUsage, SlowAPIResponse |
| **info** | 情報提供のみ | Webhook | HighRequestRate, ServiceRestarted |

### カスタムラベル

- `component`: システムコンポーネント（system, application, database, security, backup）
- `category`: カテゴリー（resource, performance, reliability, availability, security）

---

## Alertmanager設定

### レシーバー一覧

| レシーバー | 対象 | 通知方法 | 再送間隔 |
|-----------|------|----------|----------|
| **default** | 全アラート | Webhook | 12時間 |
| **critical** | Critical | Email + Webhook | 4時間 |
| **warning** | Warning | Email + Webhook | 24時間 |
| **info** | Info | Webhook | 48時間 |
| **security** | セキュリティ | Email + Webhook | 6時間 |
| **database** | DB関連 | Email + Webhook | 8時間 |
| **backup** | バックアップ | Email + Webhook | 24時間 |

### 抑制ルール

アラートの重複を防ぐため、以下の抑制ルールが設定されています。

1. **Critical発火時にWarningを抑制**
   - `CriticalMemoryUsage` → `HighMemoryUsage` を抑制
   - `CriticalCPUUsage` → `HighCPUUsage` を抑制

2. **サービス停止時に他を抑制**
   - `ServiceDown` → 全てのアラートを抑制

3. **接続プール枯渇時にスロークエリを抑制**
   - `DatabaseConnectionPoolExhausted` → `DatabaseQuerySlow` を抑制

---

## Grafanaダッシュボード

### パネル構成

#### 1. システムリソース（3パネル）

- **CPU Usage** (Gauge): リアルタイムCPU使用率
- **Memory Usage** (Gauge): リアルタイムメモリ使用率
- **Disk Usage** (Gauge): リアルタイムディスク使用率

#### 2. アプリケーションメトリクス（4パネル）

- **Active Users** (Time Series): アクティブユーザー数の推移
- **HTTP Request Rate** (Time Series): エンドポイント別リクエスト数
- **Error Rate** (Time Series): エラー率、5xx率、4xx率
- **API Response Time** (Time Series): p50, p95, p99のレスポンスタイム

#### 3. データベースメトリクス（2パネル）

- **Database Connections** (Time Series): 接続数の推移
- **Database Query Time** (Time Series): p95クエリ時間

#### 4. その他（2パネル）

- **HTTP Requests by Status Code** (Bars): ステータスコード別リクエスト分布
- **Security Events** (Time Series): ログイン失敗、CSRF失敗の推移

### ダッシュボードの使い方

1. **Grafanaにログイン**
   ```
   http://localhost:3000
   ```

2. **ダッシュボードをインポート**
   - Dashboards → Import
   - `monitoring/grafana/dashboards/mirai-knowledge-dashboard.json` をアップロード

3. **リフレッシュ間隔の設定**
   - デフォルト: 10秒
   - 右上のドロップダウンで変更可能（5s, 30s, 1m, 5m, etc.）

4. **時間範囲の変更**
   - デフォルト: 過去1時間
   - 右上のピッカーで変更可能

---

## 監視スクリプト

### health-monitor.sh

**場所**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/health-monitor.sh`

**機能**:
- APIヘルスチェック
- データベース接続チェック
- ディスク容量チェック
- メモリ使用率チェック
- プロセス稼働チェック
- ログエラーチェック

**使用方法**:

```bash
# 手動実行
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems
./scripts/health-monitor.sh

# カスタム設定で実行
API_URL=http://localhost:5100 \
ALERTMANAGER_URL=http://localhost:9093 \
LOG_FILE=/var/log/mks/health-monitor.log \
./scripts/health-monitor.sh
```

**Cronで定期実行**:

```bash
# crontabを編集
crontab -e

# 5分ごとに実行
*/5 * * * * /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/health-monitor.sh >> /var/log/mks/health-monitor-cron.log 2>&1
```

**ログ出力例**:

```
[2026-01-09 15:30:00] ==========================================
[2026-01-09 15:30:00] Health Monitor Started
[2026-01-09 15:30:00] ==========================================
[2026-01-09 15:30:00] Starting health check...
[2026-01-09 15:30:00] Health status: healthy
[2026-01-09 15:30:00] Health check passed
[2026-01-09 15:30:01] Checking database connectivity...
[2026-01-09 15:30:01] Database status: connected
[2026-01-09 15:30:01] Database check passed
[2026-01-09 15:30:01] All health checks passed ✓
[2026-01-09 15:30:01] ==========================================
```

---

## セットアップ手順

### 前提条件

- Prometheus 2.x がインストール済み
- Alertmanager 0.24.x がインストール済み
- Grafana 8.x がインストール済み
- Mirai Knowledge Systems バックエンドが稼働中

### 1. Prometheusの設定

```bash
# アラートルールをコピー
sudo cp monitoring/prometheus/alerts.yml /etc/prometheus/

# prometheus.ymlにアラートルールを追加
sudo nano /etc/prometheus/prometheus.yml
```

**prometheus.yml に追加**:

```yaml
# Alert Rules
rule_files:
  - "alerts.yml"

# Alertmanager設定
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093
```

```bash
# 設定を検証
promtool check config /etc/prometheus/prometheus.yml

# Prometheusを再起動
sudo systemctl restart prometheus
```

### 2. Alertmanagerの設定

```bash
# Alertmanager設定をコピー
sudo cp monitoring/alertmanager/alertmanager.yml /etc/alertmanager/

# 設定を検証
amtool check-config /etc/alertmanager/alertmanager.yml

# Alertmanagerを再起動
sudo systemctl restart alertmanager
```

### 3. Grafanaの設定

```bash
# ダッシュボードディレクトリを作成
sudo mkdir -p /var/lib/grafana/dashboards

# ダッシュボード定義をコピー
sudo cp monitoring/grafana/dashboards/mirai-knowledge-dashboard.json \
    /var/lib/grafana/dashboards/

# 所有者を変更
sudo chown -R grafana:grafana /var/lib/grafana/dashboards
```

**または、Grafana UIでインポート**:

1. http://localhost:3000 にアクセス
2. Dashboards → Import
3. `mirai-knowledge-dashboard.json` をアップロード

### 4. ヘルスモニタースクリプトの設定

```bash
# スクリプトをシステムに配置
sudo cp scripts/health-monitor.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/health-monitor.sh

# ログディレクトリを作成
sudo mkdir -p /var/log/mks
sudo chown $USER:$USER /var/log/mks

# Cronジョブを追加
crontab -e

# 5分ごとに実行
*/5 * * * * /usr/local/bin/health-monitor.sh >> /var/log/mks/health-monitor-cron.log 2>&1
```

---

## アラート通知先の追加方法

### 1. メール通知の設定

**alertmanager.yml を編集**:

```yaml
receivers:
  - name: 'critical'
    email_configs:
      - to: 'admin@company.local,team@company.local'  # 複数の宛先
        from: 'alerts@company.local'
        smarthost: 'smtp.company.local:587'  # SMTP サーバー
        auth_username: 'alerts@company.local'
        auth_password: 'YOUR_PASSWORD'
        require_tls: true
```

### 2. Slack通知の追加

**Slack Webhookを取得**:
1. https://api.slack.com/apps にアクセス
2. "Create New App" → "Incoming Webhooks"
3. Webhook URLをコピー

**alertmanager.yml を編集**:

```yaml
receivers:
  - name: 'critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts-critical'
        title: '⚠️ CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          Summary: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
        color: 'danger'
```

### 3. PagerDuty通知の追加

**alertmanager.yml を編集**:

```yaml
receivers:
  - name: 'critical'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
        severity: 'critical'
        description: '{{ .GroupLabels.alertname }}'
```

### 4. Webhook通知のカスタマイズ

**バックエンドAPIでWebhookエンドポイントを実装**:

```python
# backend/app_v2.py に追加
@app.route('/api/v1/webhook/alerts', methods=['POST'])
def webhook_alerts():
    alerts = request.json
    for alert in alerts:
        # カスタム処理（ログ記録、通知、チケット作成など）
        logger.info(f"Alert received: {alert['labels']['alertname']}")
    return jsonify({"status": "received"}), 200
```

---

## トラブルシューティング

### 1. アラートが発火しない

**確認項目**:

```bash
# Prometheusでアラートルールを確認
curl http://localhost:9090/api/v1/rules

# アラートの状態を確認
curl http://localhost:9090/api/v1/alerts

# Prometheusログを確認
sudo journalctl -u prometheus -f
```

**一般的な原因**:
- メトリクスが収集されていない
- アラートルールの式が間違っている
- `for` 期間がまだ経過していない

### 2. アラート通知が届かない

**確認項目**:

```bash
# Alertmanagerの状態を確認
curl http://localhost:9093/api/v1/status

# アラート一覧を確認
curl http://localhost:9093/api/v1/alerts

# Alertmanagerログを確認
sudo journalctl -u alertmanager -f
```

**一般的な原因**:
- SMTP設定が間違っている
- Webhook URLが到達できない
- 抑制ルールが発動している

### 3. ダッシュボードにデータが表示されない

**確認項目**:

1. **Prometheusデータソースの確認**
   - Grafana → Configuration → Data Sources
   - Prometheus URLが正しいか確認（http://localhost:9090）

2. **メトリクスの確認**
   ```bash
   # メトリクスが存在するか確認
   curl http://localhost:9090/api/v1/query?query=mks_system_cpu_usage_percent
   ```

3. **時間範囲の確認**
   - ダッシュボード右上の時間ピッカーを調整

### 4. ヘルスモニタースクリプトが動作しない

**確認項目**:

```bash
# 実行権限を確認
ls -l /usr/local/bin/health-monitor.sh

# 手動実行してエラーを確認
/usr/local/bin/health-monitor.sh

# ログを確認
tail -f /var/log/mks/health-monitor.log
```

**一般的な原因**:
- 実行権限がない → `chmod +x` で付与
- API URLが間違っている → 環境変数で上書き
- curlがインストールされていない → `apt install curl`

---

## ベストプラクティス

### 1. アラート疲れを防ぐ

- **閾値の調整**: 環境に応じて警告閾値を調整
- **再送間隔の最適化**: 重要度に応じて `repeat_interval` を設定
- **抑制ルールの活用**: 関連アラートをグループ化

### 2. 定期的なメンテナンス

```bash
# 週次: アラート履歴を確認
curl http://localhost:9093/api/v1/alerts | jq '.data[] | select(.state=="active")'

# 月次: アラートルールの見直し
# - 発火頻度の高いアラートを調整
# - 不要なアラートを削除

# 四半期: ダッシュボードの改善
# - よく見るメトリクスをパネルに追加
# - 不要なパネルを削除
```

### 3. ドキュメント化

- **ランブック**: 各アラートの対応手順を文書化
- **ポストモーテム**: インシデント後に振り返りを実施
- **変更履歴**: アラートルールの変更を記録

---

## 参考リンク

- **Prometheus公式ドキュメント**: https://prometheus.io/docs/
- **Alertmanager公式ドキュメント**: https://prometheus.io/docs/alerting/latest/alertmanager/
- **Grafana公式ドキュメント**: https://grafana.com/docs/
- **Mirai Knowledge Systems**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/`

---

## サポート

問題が発生した場合:

1. **ログを確認**
   ```bash
   sudo journalctl -u prometheus -f
   sudo journalctl -u alertmanager -f
   sudo journalctl -u grafana-server -f
   tail -f /var/log/mks/health-monitor.log
   ```

2. **設定を検証**
   ```bash
   promtool check config /etc/prometheus/prometheus.yml
   amtool check-config /etc/alertmanager/alertmanager.yml
   ```

3. **システム管理者に連絡**
   - Email: admin@company.local
   - Slack: #mirai-knowledge-support

---

**監視アラート設定は完了しました。システムの健全性を継続的に監視し、問題を早期に発見しましょう。**
