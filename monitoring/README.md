# 建設土木ナレッジシステム - 監視システム

Prometheus + Grafana による包括的な監視システム（Phase C完了版）

## 概要

このディレクトリには、建設土木ナレッジシステムの監視に必要なすべての設定ファイルが含まれています。

**最終更新**: 2026-01-09
**バージョン**: 2.0.0 (Phase C - 監視アラート設定完了)

### 監視コンポーネント

- **Prometheus**: メトリクス収集・保存 + アラートルール（30種類以上）
- **Grafana**: メトリクス可視化ダッシュボード（11パネル）
- **Alertmanager**: アラート通知管理（6種類のレシーバー）
- **Node Exporter**: システムリソースメトリクス
- **Health Monitor Script**: ヘルスチェック自動化スクリプト

## ファイル構成

```
monitoring/
├── prometheus/
│   └── alerts.yml              # Prometheusアラートルール（30種類以上）
├── alertmanager/
│   └── alertmanager.yml        # Alertmanager設定（6種類のレシーバー）
├── grafana/
│   └── dashboards/
│       └── mirai-knowledge-dashboard.json  # メインダッシュボード（11パネル）
├── prometheus.yml              # Prometheus基本設定（旧版）
├── alert_rules.yml             # アラートルール定義（旧版）
├── alertmanager.yml            # Alertmanager設定（旧版）
├── grafana-dashboard.json      # Grafanaダッシュボード定義（旧版）
├── docker-compose.monitoring.yml  # Docker Compose設定
├── setup_monitoring.sh         # セットアップスクリプト
└── README.md                   # このファイル

scripts/
└── health-monitor.sh           # ヘルスチェックスクリプト（Phase C新規追加）
```

### Phase C で追加された新機能

1. **包括的なアラートルール** (`prometheus/alerts.yml`)
   - システムリソース監視（CPU, メモリ, ディスク）
   - アプリケーション監視（エラー率, 応答時間, HTTP状態）
   - データベース監視（接続プール, クエリパフォーマンス）
   - セキュリティ監視（ログイン失敗, CSRF）
   - バックアップ監視（実行状態, 失敗検知）

2. **高度なアラート通知** (`alertmanager/alertmanager.yml`)
   - 重要度別レシーバー（critical, warning, info）
   - コンポーネント別レシーバー（security, database, backup）
   - 抑制ルール（アラート重複防止）
   - カスタム通知テンプレート

3. **改善されたGrafanaダッシュボード** (`grafana/dashboards/mirai-knowledge-dashboard.json`)
   - 11種類のパネル（システム、アプリ、DB、セキュリティ）
   - パーセンタイル表示（p50, p95, p99）
   - 自動リフレッシュ（10秒間隔）

4. **ヘルスチェック自動化** (`../scripts/health-monitor.sh`)
   - 6種類のヘルスチェック
   - Alertmanager連携
   - Cron対応

## セットアップ方法

### Phase C 推奨セットアップ

```bash
# 1. Prometheus Alert Rules をインストール
sudo cp prometheus/alerts.yml /etc/prometheus/

# 2. Alertmanager設定をインストール
sudo cp alertmanager/alertmanager.yml /etc/alertmanager/

# 3. Prometheus設定にアラートルールを追加
sudo nano /etc/prometheus/prometheus.yml
# 以下を追加:
# rule_files:
#   - "alerts.yml"
# alerting:
#   alertmanagers:
#     - static_configs:
#         - targets: ['localhost:9093']

# 4. サービスを再起動
sudo systemctl restart prometheus
sudo systemctl restart alertmanager

# 5. Grafanaダッシュボードをインポート
# http://localhost:3000 → Dashboards → Import
# grafana/dashboards/mirai-knowledge-dashboard.json をアップロード

# 6. ヘルスモニタースクリプトを設定
chmod +x ../scripts/health-monitor.sh
sudo cp ../scripts/health-monitor.sh /usr/local/bin/

# 7. Cronで自動実行（5分ごと）
crontab -e
# 以下を追加:
# */5 * * * * /usr/local/bin/health-monitor.sh >> /var/log/mks/health-monitor-cron.log 2>&1
```

詳細なセットアップ手順は [MONITORING_SETUP_COMPLETE.md](../MONITORING_SETUP_COMPLETE.md) を参照してください。

### 方法1: Dockerを使用（旧版）

```bash
# 監視スタックを起動
cd /path/to/Mirai-Knowledge-Systems/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# ログ確認
docker-compose -f docker-compose.monitoring.yml logs -f

# 停止
docker-compose -f docker-compose.monitoring.yml down
```

### 方法2: ネイティブインストール（旧版）

```bash
# セットアップスクリプトを実行（root権限必要）
sudo ./setup_monitoring.sh
```

## アクセスURL

セットアップ完了後、以下のURLにアクセスできます：

- **Grafana**: http://localhost:3000
  - 初期ログイン: `admin` / `admin`
  - 初回ログイン後、パスワード変更を求められます

- **Prometheus**: http://localhost:9090
  - メトリクスクエリとアラート確認

- **Alertmanager**: http://localhost:9093
  - アラート管理と通知設定

- **Node Exporter**: http://localhost:9100/metrics
  - システムメトリクス

- **cAdvisor**: http://localhost:8080
  - コンテナメトリクス

- **アプリケーションメトリクス**: http://localhost:5000/api/v1/metrics
  - ナレッジシステムのメトリクス

## 監視メトリクス

### システムリソース

- **CPU使用率**: `system_cpu_usage_percent`
- **メモリ使用率**: `system_memory_usage_percent`
- **ディスク使用率**: `system_disk_usage_percent`
- **ディスクI/O**: `node_disk_io_time_seconds_total`
- **ネットワークトラフィック**: `node_network_receive_bytes_total`

### アプリケーションメトリクス

- **HTTPリクエスト数**: `http_requests_total{method, endpoint, status}`
- **応答時間**: `http_request_duration_seconds{endpoint, quantile}`
- **エラー率**: `http_errors_total{code}`
- **アクティブユーザー数**: `active_users_count`
- **アクティブセッション数**: `active_sessions_count`

### ビジネスメトリクス

- **総ナレッジ数**: `knowledge_total_count`
- **カテゴリ別ナレッジ数**: `knowledge_by_category{category}`
- **ナレッジ作成数**: `knowledge_created_total`
- **検索実行数**: `knowledge_searches_total`
- **閲覧数**: `knowledge_views_total`
- **ログイン試行**: `login_attempts_total{status}`

## アラート設定

### 設定されているアラート

#### システムアラート
- CPU使用率 > 80% (5分間)
- メモリ使用率 > 90% (5分間)
- ディスク使用率 > 85% (10分間)
- ディスクI/O待機 > 20% (5分間)

#### アプリケーションアラート
- エラー率 > 5% (5分間)
- 応答時間(P95) > 3秒 (5分間)
- リクエスト数急増 > 100/秒 (3分間)

#### 可用性アラート
- サービスダウン (2分間)
- データベースダウン (1分間)

### アラート通知設定

`alertmanager.yml` を編集して通知先を設定します：

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
```

**Slack通知も設定可能**:

```yaml
receivers:
  - name: 'slack-alerts'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
```

## Grafanaダッシュボード

### ダッシュボードの構成

1. **システム概要**
   - サービス稼働状態
   - アクティブユーザー数
   - リクエスト数
   - エラー率

2. **システムリソース**
   - CPU/メモリ/ディスク使用率グラフ

3. **アプリケーションメトリクス**
   - リクエスト数（RPS）
   - 応答時間（P50/P95/P99）
   - HTTPステータスコード分布
   - エンドポイント別応答時間

4. **ユーザーアクティビティ**
   - アクティブユーザー推移
   - ログイン成功/失敗
   - ユーザー別リクエスト数（Top 10）
   - セッション数推移

5. **ナレッジ統計**
   - 総ナレッジ数
   - ナレッジ作成数
   - 検索数/閲覧数
   - カテゴリ別ナレッジ数

### カスタムダッシュボード追加

Grafana UIから新しいダッシュボードを作成し、JSONエクスポートして保存できます。

## メトリクスクエリ例

### Prometheusクエリ

#### CPU使用率（過去5分平均）
```promql
100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

#### エラー率
```promql
(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100
```

#### 応答時間P95
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
```

#### アクティブユーザー数
```promql
active_users_count
```

## トラブルシューティング

### Prometheusが起動しない

```bash
# 設定ファイルの検証
promtool check config prometheus.yml

# ログ確認
docker logs mirai-prometheus
# または
journalctl -u prometheus -f
```

### メトリクスが収集されない

1. ターゲットの状態確認
   - Prometheus UI: http://localhost:9090/targets

2. アプリケーションが起動しているか確認
   ```bash
   curl http://localhost:5000/api/v1/metrics
   ```

3. ファイアウォール設定確認
   ```bash
   sudo ufw status
   ```

### Grafanaにデータが表示されない

1. データソース接続確認
   - Grafana → Configuration → Data Sources → Prometheus → Test

2. Prometheusクエリが正しいか確認
   - ダッシュボードパネルの編集モードでクエリを確認

### アラートが通知されない

1. Alertmanager UI確認: http://localhost:9093

2. Alertmanager設定確認
   ```bash
   amtool check-config alertmanager.yml
   ```

3. SMTP設定が正しいか確認

## パフォーマンスチューニング

### データ保持期間の調整

`prometheus.yml` または起動コマンドで設定:

```bash
--storage.tsdb.retention.time=30d
```

### スクレイプ間隔の調整

頻繁な監視が必要ない場合は間隔を長くします:

```yaml
global:
  scrape_interval: 30s  # デフォルト15s
```

### メトリクスの削減

不要なメトリクスを除外:

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'node_network_.*'
        action: drop
```

## セキュリティ

### Basic認証の追加

`prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'mirai_knowledge_app'
    basic_auth:
      username: 'prometheus'
      password: 'secure-password'
```

### TLS/HTTPS設定

本番環境ではリバースプロキシ（Nginx）経由でHTTPS化を推奨します。

## バックアップ

### Prometheusデータのバックアップ

```bash
# スナップショット作成
curl -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot

# データディレクトリのバックアップ
tar -czf prometheus-backup-$(date +%Y%m%d).tar.gz /var/lib/prometheus/
```

### Grafanaダッシュボードのバックアップ

```bash
# ダッシュボードJSONをエクスポート
curl -H "Authorization: Bearer YOUR-API-KEY" \
  http://localhost:3000/api/dashboards/db/dashboard-slug \
  > dashboard-backup.json
```

## 参考リンク

- [Prometheus公式ドキュメント](https://prometheus.io/docs/)
- [Grafana公式ドキュメント](https://grafana.com/docs/)
- [PromQLチートシート](https://promlabs.com/promql-cheat-sheet/)
- [Node Exporter](https://github.com/prometheus/node_exporter)

## サポート

問題が発生した場合は、以下を確認してください：

1. ログファイル
2. サービス状態: `systemctl status <service>`
3. ネットワーク接続
4. ディスク容量

---

**注意**: 本番環境では、必ずセキュリティ設定（認証、TLS、ファイアウォール）を適切に設定してください。
