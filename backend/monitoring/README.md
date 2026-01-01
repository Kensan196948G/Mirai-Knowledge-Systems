# Mirai Knowledge System - 監視システム

## クイックスタート

```bash
# 1. 監視システムを起動
cd monitoring
./setup-monitoring.sh

# 2. Flaskアプリケーションを起動（別ターミナル）
cd ..
python app_v2.py

# 3. アクセス
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin123)
# - Metrics: http://localhost:5100/metrics
```

## 実装内容

### 1. Flask アプリケーション (app_v2.py)

#### Prometheusメトリクス
- HTTPリクエストカウンター (`mks_http_requests_total`)
- レスポンスタイムヒストグラム (`mks_http_request_duration_seconds`)
- エラーカウンター (`mks_errors_total`)
- システムメトリクス (CPU, メモリ, ディスク)
- アプリケーションメトリクス (アクティブユーザー, ナレッジ総数)
- 認証メトリクス (`mks_auth_attempts_total`)
- レート制限メトリクス (`mks_rate_limit_hits_total`)

#### エンドポイント
- `/metrics` - Prometheus形式のメトリクス（認証不要）
- `/api/metrics/summary` - 人間が読みやすい形式のメトリクス（JWT認証必要）

#### デコレータ
- `@track_db_query(operation)` - データベースクエリのメトリクス記録

### 2. Prometheus設定

#### ファイル構成
```
prometheus/
├── prometheus.yml      # メイン設定
└── alert-rules.yml    # アラートルール
```

#### 主要設定
- スクレイプ間隔: 10秒
- データ保持期間: 15日
- 最大ストレージサイズ: 10GB

#### アラート
- CPU使用率: 80% (警告), 95% (緊急)
- メモリ使用率: 85% (警告), 95% (緊急)
- ディスク使用率: 90% (警告), 98% (緊急)
- エラー率: 5% (警告), 15% (緊急)
- APIレスポンスタイム: 2秒 (警告), 5秒 (緊急)

### 3. Grafana設定

#### ダッシュボード
1. **アプリケーション概要** (`app-overview.json`)
   - 総ナレッジ数、アクティブユーザー数
   - エラー率、レスポンスタイム
   - リクエスト数推移
   - 認証試行数

2. **APIパフォーマンス** (`api-performance.json`)
   - エンドポイント別リクエスト数
   - エンドポイント別レスポンスタイム
   - HTTPステータスコード分布
   - データベースクエリ時間

3. **システムリソース** (`system-resources.json`)
   - CPU/メモリ/ディスク使用率（ゲージ + グラフ）
   - アプリケーションメトリクス推移

#### 自動プロビジョニング
- データソース: Prometheus（自動登録）
- ダッシュボード: 起動時に自動インポート

### 4. Docker Compose

#### サービス
- **prometheus**: メトリクス収集・保存 (Port 9090)
- **grafana**: メトリクス可視化 (Port 3000)

#### ボリューム
- `mks-prometheus-data`: Prometheusデータ永続化
- `mks-grafana-data`: Grafanaデータ永続化

### 5. セットアップスクリプト

`setup-monitoring.sh` - 自動セットアップスクリプト
- Docker/Docker Composeの確認
- 設定ファイルの検証
- コンテナの起動
- ヘルスチェック
- アクセス情報の表示

## ディレクトリ構造

```
monitoring/
├── docker-compose.yml              # Docker Compose設定
├── setup-monitoring.sh             # セットアップスクリプト
├── MONITORING_SETUP.md             # 詳細ドキュメント
├── README.md                       # このファイル
├── prometheus/
│   ├── prometheus.yml              # Prometheus設定
│   └── alert-rules.yml             # アラートルール
└── grafana/
    ├── dashboards/
    │   ├── app-overview.json       # アプリケーション概要
    │   ├── api-performance.json    # APIパフォーマンス
    │   └── system-resources.json   # システムリソース
    └── provisioning/
        ├── datasources/
        │   └── prometheus.yml      # データソース設定
        └── dashboards/
            └── dashboards.yml      # ダッシュボード設定
```

## 主要コマンド

```bash
# 監視システムの起動
cd monitoring && ./setup-monitoring.sh

# 監視システムの停止
cd monitoring && docker-compose down

# 監視システムの再起動
cd monitoring && docker-compose restart

# ログの確認
cd monitoring && docker-compose logs -f

# 特定のサービスのログ
cd monitoring && docker-compose logs -f prometheus
cd monitoring && docker-compose logs -f grafana

# コンテナの状態確認
cd monitoring && docker-compose ps

# ボリュームの確認
docker volume ls | grep mks
```

## メトリクス確認方法

### 1. Prometheus形式（生データ）
```bash
curl http://localhost:5100/metrics
```

### 2. JSON形式（サマリー）
```bash
# JWT トークンを取得
TOKEN=$(curl -X POST http://localhost:5100/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# メトリクスサマリーを取得
curl -H "Authorization: Bearer $TOKEN" http://localhost:5100/api/metrics/summary
```

### 3. Prometheusクエリ
```bash
# Prometheusにアクセス: http://localhost:9090
# クエリ例:
# - rate(mks_http_requests_total[5m])
# - mks_system_cpu_usage_percent
# - histogram_quantile(0.95, rate(mks_http_request_duration_seconds_bucket[5m]))
```

### 4. Grafanaダッシュボード
```bash
# Grafanaにアクセス: http://localhost:3000
# ユーザー名: admin
# パスワード: admin123
```

## トラブルシューティング

### メトリクスが収集されない場合

```bash
# Flaskアプリケーションが起動しているか確認
curl http://localhost:5100/metrics

# Prometheusのターゲット状態を確認
# http://localhost:9090/targets
```

### ダッシュボードが表示されない場合

```bash
# Grafanaログを確認
docker logs mks-grafana

# プロビジョニングが正しく行われているか確認
docker exec mks-grafana ls -la /etc/grafana/provisioning/dashboards/
```

## 本番環境での推奨設定

1. **セキュリティ**
   - Grafana管理者パスワードの変更
   - Prometheusへの認証追加
   - HTTPS化（Nginx等のリバースプロキシ使用）

2. **パフォーマンス**
   - スクレイプ間隔の調整
   - データ保持期間の調整
   - ストレージサイズの調整

3. **可用性**
   - Prometheusデータの定期バックアップ
   - Grafanaダッシュボードのバージョン管理
   - アラート通知の設定（Email, Slack等）

## 詳細ドキュメント

詳細な設定方法やトラブルシューティングについては、以下を参照してください:
- [MONITORING_SETUP.md](./MONITORING_SETUP.md) - 完全なセットアップガイド

## サポート

問題が発生した場合:
1. ログを確認: `docker-compose logs`
2. ドキュメントを参照: `MONITORING_SETUP.md`
3. 設定を確認: `prometheus.yml`, `docker-compose.yml`

---

作成日: 2026-01-01
バージョン: 1.0.0
