# 監視システム セットアップ完了サマリー

## 作成されたファイル一覧

### 1. Prometheus設定
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/prometheus.yml`

- スクレイプ設定（15秒間隔）
- 以下のターゲットを監視:
  - Prometheus自身 (localhost:9090)
  - Node Exporter - システムメトリクス (localhost:9100)
  - アプリケーション - /api/v1/metrics (localhost:5000)
  - PostgreSQL Exporter (localhost:9187)
  - Redis Exporter (localhost:9121)
  - Nginx Exporter (localhost:9113)
- アラートルールファイルの読み込み
- 30日間のデータ保持

### 2. アラートルール設定
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/alert_rules.yml`

設定されたアラート:
- **システムアラート**:
  - CPU使用率 > 80% (警告) / > 95% (クリティカル)
  - メモリ使用率 > 90%
  - ディスク使用率 > 85% (警告) / > 95% (クリティカル)
  - ディスクI/O待機 > 20%

- **アプリケーションアラート**:
  - エラー率 > 5%
  - 応答時間(P95) > 3秒 (警告) / > 5秒 (クリティカル)
  - リクエスト数急増 > 100/秒
  - アクティブユーザー数急減

- **データベースアラート**:
  - DB接続数 > 80
  - DBダウン検出

- **可用性アラート**:
  - サービスダウン検出
  - 監視ターゲットダウン

- **ビジネスメトリクスアラート**:
  - ナレッジ作成数低下
  - ログイン失敗多発

### 3. Grafanaダッシュボード
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/grafana-dashboard.json`

ダッシュボード構成:
- **システム概要**: サービス稼働状態、アクティブユーザー、リクエスト数、エラー率
- **システムリソース**: CPU/メモリ/ディスク使用率グラフ
- **アプリケーションメトリクス**:
  - リクエスト数（RPS）
  - 応答時間（P50/P95/P99）
  - HTTPステータスコード分布
  - エンドポイント別応答時間
- **ユーザーアクティビティ**:
  - アクティブユーザー推移
  - ログイン成功/失敗
  - ユーザー別リクエスト数（Top 10）
  - セッション数推移
- **ナレッジ統計**:
  - 総ナレッジ数、作成数、検索数、閲覧数
  - カテゴリ別ナレッジ数（円グラフ）
- **データベースメトリクス**:
  - 接続数、クエリ実行時間

### 4. アプリケーションメトリクスエンドポイント
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/app_v2.py`

追加された機能:
- **新規エンドポイント**: `GET /api/v1/metrics`
  - Prometheus形式のテキスト出力
  - 認証不要（監視ツールからアクセス可能）

- **収集メトリクス**:
  - システムリソース（CPU、メモリ、ディスク）
  - HTTPリクエスト数（メソッド・エンドポイント・ステータス別）
  - 応答時間ヒストグラム（P50/P95/P99）
  - エラー数（ステータスコード別）
  - アクティブユーザー数（過去15分）
  - アクティブセッション数
  - ログイン試行（成功/失敗）
  - ナレッジ統計（総数、カテゴリ別）
  - アプリケーション稼働時間

- **自動メトリクス収集**:
  - `@app.before_request`: リクエスト開始時刻記録
  - `@app.after_request`: 応答時間・ステータス記録
  - インメモリストレージで集計

### 5. Docker Compose設定
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/docker-compose.monitoring.yml`

サービス構成:
- **prometheus**: メトリクス収集（ポート9090）
- **grafana**: 可視化ダッシュボード（ポート3000）
- **node-exporter**: システムメトリクス（ポート9100）
- **cadvisor**: コンテナメトリクス（ポート8080）
- **alertmanager**: アラート通知（ポート9093）

永続化ボリューム:
- prometheus_data: メトリクスデータ
- grafana_data: ダッシュボード設定
- alertmanager_data: アラート履歴

### 6. Alertmanager設定
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/alertmanager.yml`

通知設定:
- メール通知（SMTP設定）
- Slack通知（コメントアウト、設定可能）
- PagerDuty通知（コメントアウト、設定可能）
- 重要度別ルーティング（critical/warning）
- チーム別通知先（system/app/db）
- アラート抑制ルール

### 7. Grafana自動プロビジョニング
**ファイル**:
- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/grafana-provisioning/datasources/prometheus.yml`
- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/grafana-provisioning/dashboards/dashboard-provider.yml`

自動設定:
- Prometheusデータソースの自動追加
- ダッシュボードの自動ロード

### 8. セットアップスクリプト
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/setup_monitoring.sh`

機能:
- OS検出（Ubuntu/Debian/CentOS/RHEL対応）
- Prometheus v2.48.0 インストール
- Node Exporter v1.7.0 インストール
- Grafana インストール（APT/YUM）
- systemdサービス登録
- ファイアウォール設定（ufw/firewalld）
- 自動起動設定

### 9. クイックスタートスクリプト
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/quick-start.sh`

機能:
- Docker/Docker Compose環境チェック
- 監視スタックの一括起動
- ヘルスチェック
- 使用方法ガイド表示

### 10. ドキュメント
**ファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/README.md`

内容:
- セットアップ方法（Docker/ネイティブ）
- アクセスURL一覧
- 監視メトリクス詳細
- アラート設定ガイド
- ダッシュボード構成
- Prometheusクエリ例
- トラブルシューティング
- パフォーマンスチューニング
- セキュリティ設定
- バックアップ方法

## 使用開始手順

### クイックスタート（Docker使用）

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring
./quick-start.sh
```

### 手動セットアップ

```bash
# Docker Composeで起動
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# または、ネイティブインストール
sudo ./setup_monitoring.sh
```

### アプリケーション起動

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend

# psutilをインストール
pip install psutil

# アプリケーション起動
python app_v2.py
```

### アクセス

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **メトリクス**: http://localhost:5000/api/v1/metrics

## 追加の依存関係

以下のパッケージが `requirements.txt` に追加されました:
- `psutil==5.9.6` - システムメトリクス収集用

インストール:
```bash
pip install -r requirements.txt
```

## メトリクス例

```bash
# アプリケーションメトリクスを確認
curl http://localhost:5000/api/v1/metrics

# 出力例:
# app_info{version="2.0",name="mirai-knowledge-system"} 1
# app_uptime_seconds 123.45
# system_cpu_usage_percent 25.30
# system_memory_usage_percent 68.45
# active_users_count 5
# knowledge_total_count 150
# ...
```

## トラブルシューティング

### メトリクスが表示されない場合

1. アプリケーションが起動しているか確認
```bash
curl http://localhost:5000/api/v1/metrics
```

2. Prometheusターゲットの状態確認
http://localhost:9090/targets

### Grafanaに接続できない場合

```bash
# コンテナ状態確認
docker-compose -f docker-compose.monitoring.yml ps

# ログ確認
docker-compose -f docker-compose.monitoring.yml logs grafana
```

## セキュリティ注意事項

本番環境では以下を必ず設定してください:
1. Grafanaの管理者パスワード変更
2. Prometheus/Grafanaへの認証追加
3. ファイアウォール設定
4. HTTPS/TLS設定（リバースプロキシ経由）
5. アラート通知先の設定（メール/Slack）

## 次のステップ

1. Grafanaにログインしてパスワードを変更
2. アラート通知先を設定（alertmanager.yml）
3. カスタムダッシュボードの作成
4. 長期保存用のリモートストレージ設定（オプション）
5. バックアップ設定

---

**作成日時**: 2025-12-27
**対象システム**: 建設土木ナレッジシステム v2.0
**監視スタック**: Prometheus 2.48.0 + Grafana 10.2.2
