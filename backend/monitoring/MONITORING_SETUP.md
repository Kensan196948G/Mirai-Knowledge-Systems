# Mirai Knowledge System 監視システムセットアップガイド

## 概要

このドキュメントは、Mirai Knowledge System の完全な監視システム（Prometheus + Grafana）のセットアップと運用ガイドです。

## 目次

1. [システム構成](#システム構成)
2. [前提条件](#前提条件)
3. [クイックスタート](#クイックスタート)
4. [詳細セットアップ](#詳細セットアップ)
5. [メトリクス一覧](#メトリクス一覧)
6. [ダッシュボード](#ダッシュボード)
7. [アラート設定](#アラート設定)
8. [トラブルシューティング](#トラブルシューティング)
9. [運用ガイド](#運用ガイド)

## システム構成

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                  Mirai Knowledge System                     │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │  Flask App   │────────>│  Prometheus  │                │
│  │  (app_v2.py) │ metrics │   :9090      │                │
│  │              │ /metrics│              │                │
│  └──────────────┘         └──────┬───────┘                │
│         │                         │                         │
│         │                         v                         │
│         │                 ┌──────────────┐                 │
│         │                 │   Grafana    │                 │
│         └────────────────>│    :3000     │                 │
│           JWT Auth        │              │                 │
│           /api/metrics    └──────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### コンポーネント

1. **Flask Application** (app_v2.py)
   - Prometheusメトリクスエンドポイント: `/metrics`
   - メトリクスサマリーAPI: `/api/metrics/summary` (認証必要)
   - カスタムメトリクス収集

2. **Prometheus** (Port 9090)
   - メトリクス収集・保存
   - アラートルール評価
   - 15日間のデータ保持

3. **Grafana** (Port 3000)
   - メトリクス可視化
   - ダッシュボード
   - アラート通知

## 前提条件

### 必須要件

- Docker: 20.10.0 以上
- Docker Compose: 2.0.0 以上
- Python: 3.9 以上
- ディスク空き容量: 最低 10GB

### 推奨環境

- CPU: 2コア以上
- メモリ: 4GB以上
- OS: Linux (Ubuntu 20.04+), macOS, Windows (WSL2)

## クイックスタート

### 1. 依存パッケージのインストール

```bash
# バックエンドディレクトリに移動
cd /path/to/Mirai-Knowledge-Systems/backend

# Pythonパッケージのインストール
pip install -r requirements.txt
```

### 2. 監視システムの起動

```bash
# monitoringディレクトリに移動
cd monitoring

# セットアップスクリプトを実行
./setup-monitoring.sh
```

### 3. アクセス確認

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
  - ユーザー名: `admin`
  - パスワード: `admin123`

### 4. Flaskアプリケーションの起動

```bash
# バックエンドディレクトリに戻る
cd ..

# Flaskアプリケーションを起動
python app_v2.py
```

### 5. メトリクスの確認

ブラウザで以下のURLにアクセス:
- http://localhost:5100/metrics (Prometheus形式のメトリクス)

## 詳細セットアップ

### Flaskアプリケーションの設定

#### 1. prometheus-clientのインストール

`requirements.txt` に以下が含まれていることを確認:

```
prometheus-client==0.19.0
```

#### 2. メトリクスエンドポイントの確認

`app_v2.py` には以下のメトリクスが実装されています:

```python
# HTTPリクエストメトリクス
REQUEST_COUNT = Counter('mks_http_requests_total', ...)
REQUEST_DURATION = Histogram('mks_http_request_duration_seconds', ...)

# エラーメトリクス
ERROR_COUNT = Counter('mks_errors_total', ...)

# システムメトリクス
SYSTEM_CPU_USAGE = Gauge('mks_system_cpu_usage_percent', ...)
SYSTEM_MEMORY_USAGE = Gauge('mks_system_memory_usage_percent', ...)
SYSTEM_DISK_USAGE = Gauge('mks_system_disk_usage_percent', ...)

# アプリケーションメトリクス
ACTIVE_USERS = Gauge('mks_active_users', ...)
KNOWLEDGE_TOTAL = Gauge('mks_knowledge_total', ...)
```

### Prometheusの設定

#### prometheus.yml の主要設定

```yaml
global:
  scrape_interval: 15s      # メトリクス収集間隔
  evaluation_interval: 15s  # アラート評価間隔

scrape_configs:
  - job_name: 'mks-backend'
    scrape_interval: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['host.docker.internal:5100']
```

#### アラートルールの設定

`prometheus/alert-rules.yml` に以下のアラートが定義されています:

- CPU使用率: 80%以上で警告、95%以上で緊急
- メモリ使用率: 85%以上で警告、95%以上で緊急
- ディスク使用率: 90%以上で警告、98%以上で緊急
- エラー率: 5%以上で警告、15%以上で緊急
- APIレスポンスタイム: 2秒以上で警告、5秒以上で緊急

### Grafanaの設定

#### 自動プロビジョニング

Grafanaは起動時に以下を自動的にセットアップします:

1. **データソース**: Prometheus (http://prometheus:9090)
2. **ダッシュボード**:
   - アプリケーション概要
   - APIパフォーマンス
   - システムリソース

#### ダッシュボードのカスタマイズ

1. Grafanaにログイン (http://localhost:3000)
2. 左サイドバーから「Dashboards」を選択
3. 「Mirai」フォルダー内のダッシュボードを選択
4. 右上の「Settings」からカスタマイズ可能

## メトリクス一覧

### HTTPリクエストメトリクス

| メトリクス名 | タイプ | 説明 | ラベル |
|------------|--------|------|--------|
| `mks_http_requests_total` | Counter | 総HTTPリクエスト数 | method, endpoint, status |
| `mks_http_request_duration_seconds` | Histogram | HTTPリクエスト処理時間 | method, endpoint |
| `mks_api_calls_total` | Counter | API呼び出し数 | endpoint, method |

### エラーメトリクス

| メトリクス名 | タイプ | 説明 | ラベル |
|------------|--------|------|--------|
| `mks_errors_total` | Counter | 総エラー数 | type, endpoint |

### システムメトリクス

| メトリクス名 | タイプ | 説明 |
|------------|--------|------|
| `mks_system_cpu_usage_percent` | Gauge | CPU使用率 (%) |
| `mks_system_memory_usage_percent` | Gauge | メモリ使用率 (%) |
| `mks_system_disk_usage_percent` | Gauge | ディスク使用率 (%) |

### データベースメトリクス

| メトリクス名 | タイプ | 説明 | ラベル |
|------------|--------|------|--------|
| `mks_database_query_duration_seconds` | Histogram | DBクエリ実行時間 | operation |
| `mks_database_connections` | Gauge | DB接続数 | - |

### アプリケーションメトリクス

| メトリクス名 | タイプ | 説明 |
|------------|--------|------|
| `mks_active_users` | Gauge | アクティブユーザー数 |
| `mks_knowledge_total` | Gauge | ナレッジ総数 |

### 認証メトリクス

| メトリクス名 | タイプ | 説明 | ラベル |
|------------|--------|------|--------|
| `mks_auth_attempts_total` | Counter | 認証試行数 | status |
| `mks_rate_limit_hits_total` | Counter | レート制限ヒット数 | endpoint |

## ダッシュボード

### 1. アプリケーション概要ダッシュボード

**ファイル**: `grafana/dashboards/app-overview.json`

**表示内容**:
- 総ナレッジ数
- アクティブユーザー数
- エラー率
- 平均レスポンスタイム
- リクエスト数（ステータス別）
- レスポンスタイム（パーセンタイル）
- 認証試行数
- エラー発生数（タイプ別）

### 2. APIパフォーマンスダッシュボード

**ファイル**: `grafana/dashboards/api-performance.json`

**表示内容**:
- APIエンドポイント別リクエスト数
- エンドポイント別レスポンスタイム
- HTTPメソッド別リクエスト数
- HTTPステータスコード分布
- データベースクエリ時間
- レート制限ヒット数

### 3. システムリソースダッシュボード

**ファイル**: `grafana/dashboards/system-resources.json`

**表示内容**:
- CPU使用率（ゲージ + グラフ）
- メモリ使用率（ゲージ + グラフ）
- ディスク使用率（ゲージ + グラフ）
- アプリケーションメトリクス

## アラート設定

### アラートグループ

#### 1. システムリソースアラート

```yaml
- alert: HighCPUUsage
  expr: mks_system_cpu_usage_percent > 80
  for: 5m
  labels:
    severity: warning

- alert: HighMemoryUsage
  expr: mks_system_memory_usage_percent > 85
  for: 5m
  labels:
    severity: warning

- alert: HighDiskUsage
  expr: mks_system_disk_usage_percent > 90
  for: 10m
  labels:
    severity: warning
```

#### 2. アプリケーションパフォーマンスアラート

```yaml
- alert: SlowAPIResponse
  expr: histogram_quantile(0.95, rate(mks_http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: warning

- alert: HighErrorRate
  expr: sum(rate(mks_http_requests_total{status=~"5.."}[5m])) / sum(rate(mks_http_requests_total[5m])) * 100 > 5
  for: 3m
  labels:
    severity: warning
```

### アラート確認方法

1. Prometheusにアクセス: http://localhost:9090
2. 上部メニューから「Alerts」を選択
3. アクティブなアラートを確認

### アラート通知の設定（オプション）

Grafanaでアラート通知を設定する場合:

1. Grafanaにログイン
2. 左サイドバーから「Alerting」→「Contact points」を選択
3. 「New contact point」をクリック
4. Email、Slack、Webhookなどを設定

## トラブルシューティング

### 問題: Prometheusがメトリクスを収集できない

**症状**: Prometheusのターゲットが「DOWN」状態

**解決策**:
```bash
# Flaskアプリケーションが起動しているか確認
curl http://localhost:5100/metrics

# Docker内からホストにアクセスできるか確認
docker exec mks-prometheus ping host.docker.internal

# prometheus.ymlのターゲット設定を確認
cat monitoring/prometheus/prometheus.yml
```

### 問題: Grafanaダッシュボードが表示されない

**症状**: ダッシュボードが空、またはデータが表示されない

**解決策**:
```bash
# Prometheusデータソースが正しく設定されているか確認
# Grafana → Configuration → Data sources → Prometheus

# プロビジョニングログを確認
docker logs mks-grafana | grep -i provision

# ダッシュボードファイルを手動でインポート
# Grafana → + → Import dashboard → Upload JSON file
```

### 問題: メトリクスが更新されない

**症状**: Grafanaのグラフが更新されない

**解決策**:
```bash
# Prometheusのスクレイプ間隔を確認
# デフォルトは15秒

# リフレッシュ間隔を確認
# Grafanaダッシュボード右上のリフレッシュアイコン

# ブラウザのキャッシュをクリア
```

### 問題: アラートが発火しない

**症状**: 条件を満たしてもアラートが発火しない

**解決策**:
```bash
# アラートルールの構文を確認
docker exec mks-prometheus promtool check rules /etc/prometheus/alert-rules.yml

# アラート評価間隔を確認（デフォルト15秒）
# prometheus.yml の evaluation_interval

# Prometheusログを確認
docker logs mks-prometheus | grep -i alert
```

## 運用ガイド

### 日次運用

1. **ダッシュボード確認**
   - 毎朝、Grafanaダッシュボードを確認
   - 異常な値やトレンドをチェック

2. **アラート確認**
   - Prometheusのアラート画面を確認
   - 発火したアラートの原因を調査

### 週次運用

1. **パフォーマンスレビュー**
   - 週次でAPIパフォーマンスダッシュボードを確認
   - レスポンスタイムの傾向を分析

2. **リソース使用状況**
   - システムリソースダッシュボードで使用率を確認
   - 必要に応じてスケールアップを検討

### 月次運用

1. **データ保持の確認**
   - Prometheusのデータサイズを確認
   - 必要に応じて保持期間を調整

2. **ダッシュボードの最適化**
   - 不要なパネルの削除
   - 新しいメトリクスの追加

### バックアップ

#### Prometheusデータのバックアップ

```bash
# データボリュームのバックアップ
docker run --rm -v mks-prometheus-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup-$(date +%Y%m%d).tar.gz -C /data .
```

#### Grafanaダッシュボードのバックアップ

```bash
# ダッシュボードJSONファイルは既にバージョン管理されている
# 追加のバックアップが必要な場合:
docker run --rm -v mks-grafana-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup-$(date +%Y%m%d).tar.gz -C /data .
```

### スケーリング

#### Prometheusのスケーリング

データ量が増加した場合:

1. **保持期間の調整**
   ```yaml
   # docker-compose.yml
   command:
     - '--storage.tsdb.retention.time=30d'  # 15d → 30d
   ```

2. **ストレージサイズの増加**
   ```yaml
   # docker-compose.yml
   command:
     - '--storage.tsdb.retention.size=20GB'  # 10GB → 20GB
   ```

#### Grafanaのスケーリング

同時アクセスユーザーが増加した場合:

```yaml
# docker-compose.yml
grafana:
  environment:
    - GF_DATABASE_TYPE=postgres  # SQLiteからPostgreSQLに変更
    - GF_DATABASE_HOST=postgres:5432
```

### セキュリティ

#### 本番環境での推奨設定

1. **Grafana管理者パスワードの変更**
   ```bash
   # 初回ログイン後、必ずパスワードを変更
   ```

2. **Prometheusの認証追加**
   ```yaml
   # prometheus.yml
   basic_auth:
     username: admin
     password: secure_password
   ```

3. **HTTPS化**
   ```yaml
   # Nginx等のリバースプロキシを使用してHTTPS化
   ```

4. **ファイアウォール設定**
   ```bash
   # 必要なポートのみ開放
   # 9090, 3000は内部ネットワークのみアクセス可能に設定
   ```

### パフォーマンスチューニング

#### Prometheusのチューニング

```yaml
# prometheus.yml
global:
  scrape_interval: 30s  # メトリクス収集間隔を調整
  scrape_timeout: 10s   # タイムアウトを調整
```

#### Grafanaのチューニング

```yaml
# docker-compose.yml
grafana:
  environment:
    - GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/etc/grafana/provisioning/dashboards/app-overview.json
    - GF_USERS_ALLOW_SIGN_UP=false  # サインアップを無効化
```

## 参考リンク

- [Prometheus公式ドキュメント](https://prometheus.io/docs/)
- [Grafana公式ドキュメント](https://grafana.com/docs/)
- [prometheus-client (Python)](https://github.com/prometheus/client_python)

## サポート

問題が発生した場合は、以下を確認してください:

1. ログファイルの確認
   ```bash
   docker logs mks-prometheus
   docker logs mks-grafana
   ```

2. コンテナの状態確認
   ```bash
   docker ps -a
   ```

3. ネットワーク接続の確認
   ```bash
   docker network inspect mks-monitoring
   ```

---

最終更新日: 2026-01-01
バージョン: 1.0.0
