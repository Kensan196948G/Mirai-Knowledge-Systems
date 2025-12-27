# 監視システム セットアップ検証チェックリスト

## ファイル作成確認

- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/prometheus.yml` - Prometheus設定
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/alert_rules.yml` - アラートルール
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/alertmanager.yml` - Alertmanager設定
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/grafana-dashboard.json` - Grafanaダッシュボード
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/docker-compose.monitoring.yml` - Docker Compose設定
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/setup_monitoring.sh` - セットアップスクリプト
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/quick-start.sh` - クイックスタートスクリプト
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/README.md` - ドキュメント
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/grafana-provisioning/datasources/prometheus.yml` - データソース自動設定
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/grafana-provisioning/dashboards/dashboard-provider.yml` - ダッシュボード自動設定
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/app_v2.py` - メトリクスエンドポイント追加
- [x] `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/requirements.txt` - psutil追加

## コード検証

### app_v2.py 変更内容

```bash
# 構文チェック
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
python3 -m py_compile app_v2.py
```

**追加された内容**:
1. インポート追加:
   - `import time`
   - `import psutil`
   - `from collections import defaultdict, Counter`

2. メトリクス収集ミドルウェア:
   - `@app.before_request` - リクエスト開始時刻記録
   - `@app.after_request` - 応答時間・ステータス記録
   - グローバル `metrics_storage` 辞書

3. メトリクスエンドポイント:
   - `GET /api/v1/metrics` - Prometheus形式のメトリクス出力

## 起動前チェックリスト

### 1. 依存関係インストール

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
pip install psutil
# または
pip install -r requirements.txt
```

### 2. Docker環境確認（Docker使用の場合）

```bash
# Docker起動確認
docker --version
docker-compose --version

# または
docker compose version
```

### 3. ポート使用状況確認

以下のポートが空いていることを確認:
- 3000: Grafana
- 8080: cAdvisor
- 9090: Prometheus
- 9093: Alertmanager
- 9100: Node Exporter

```bash
# ポート確認
sudo netstat -tuln | grep -E ':(3000|8080|9090|9093|9100)'
# または
sudo ss -tuln | grep -E ':(3000|8080|9090|9093|9100)'
```

## 起動手順

### オプション1: Docker Compose（推奨）

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring

# クイックスタート
./quick-start.sh

# または手動起動
docker-compose -f docker-compose.monitoring.yml up -d

# ログ確認
docker-compose -f docker-compose.monitoring.yml logs -f
```

### オプション2: ネイティブインストール

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring

# セットアップスクリプト実行（root権限必要）
sudo ./setup_monitoring.sh
```

### アプリケーション起動

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend

# 環境変数設定（オプション）
export MKS_DEBUG=true
export MKS_ENV=development

# アプリケーション起動
python app_v2.py
```

## 動作確認チェックリスト

### 1. アプリケーションメトリクス確認

```bash
# メトリクスエンドポイントにアクセス
curl http://localhost:5000/api/v1/metrics

# 期待される出力（一部）:
# app_info{version="2.0",name="mirai-knowledge-system"} 1
# system_cpu_usage_percent XX.XX
# system_memory_usage_percent XX.XX
# active_users_count X
# knowledge_total_count X
```

- [ ] メトリクスエンドポイントが200 OKを返す
- [ ] Prometheus形式のテキストが出力される
- [ ] システムメトリクス（CPU/メモリ）が含まれる
- [ ] アプリケーションメトリクスが含まれる

### 2. Prometheus確認

ブラウザで http://localhost:9090 にアクセス

- [ ] Prometheus UIが表示される
- [ ] Status > Targets で全ターゲットが UP 状態
- [ ] Graph で `up` クエリを実行して結果が表示される
- [ ] Graph で `system_cpu_usage_percent` クエリを実行して結果が表示される

### 3. Grafana確認

ブラウザで http://localhost:3000 にアクセス

- [ ] ログインページが表示される
- [ ] admin/admin でログイン成功
- [ ] パスワード変更画面が表示される（スキップ可）
- [ ] Configuration > Data Sources に Prometheus が表示される
- [ ] Prometheus データソースで "Test" が成功する
- [ ] Dashboards でダッシュボードが表示される（または手動インポート）

### 4. アラート確認

ブラウザで http://localhost:9090/alerts にアクセス

- [ ] アラートルールが表示される
- [ ] 各アラートの状態が確認できる

### 5. Alertmanager確認

ブラウザで http://localhost:9093 にアクセス

- [ ] Alertmanager UIが表示される
- [ ] Status でAlertmanager設定が確認できる

### 6. Node Exporter確認

```bash
# Node Exporterメトリクス確認
curl http://localhost:9100/metrics | head -20
```

- [ ] システムメトリクスが出力される
- [ ] node_cpu_*, node_memory_* などのメトリクスが含まれる

## Grafanaダッシュボード設定

### 手動インポート（自動プロビジョニングが動作しない場合）

1. Grafana にログイン
2. 左メニュー > Dashboards > Import
3. "Upload JSON file" をクリック
4. `/mnt/LinuxHDD/Mirai-Knowledge-Systems/monitoring/grafana-dashboard.json` を選択
5. "Load" をクリック
6. Prometheus データソースを選択
7. "Import" をクリック

- [ ] ダッシュボードが正常にインポートされる
- [ ] パネルにデータが表示される

## メトリクス収集確認

### 実際にアプリケーションを使用して確認

```bash
# ログインして各種操作を実行
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# メトリクスを再確認
curl http://localhost:5000/api/v1/metrics
```

確認項目:
- [ ] `http_requests_total` が増加している
- [ ] `http_request_duration_seconds` に値が記録されている
- [ ] `login_attempts_total` が記録されている
- [ ] `active_users_count` が増加している

### Prometheusでメトリクスを確認

Prometheus UI (http://localhost:9090) で以下のクエリを実行:

```promql
# リクエスト数の推移
rate(http_requests_total[5m])

# 応答時間P95
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# CPU使用率
system_cpu_usage_percent

# アクティブユーザー数
active_users_count
```

- [ ] 各クエリで正常にデータが取得できる
- [ ] グラフが表示される

## トラブルシューティング

### メトリクスエンドポイントが動作しない

```bash
# アプリケーションログ確認
# エラーメッセージを確認

# psutilがインストールされているか確認
python3 -c "import psutil; print(psutil.__version__)"
```

### Prometheusがターゲットに接続できない

```bash
# Prometheusコンテナからアプリケーションに接続確認
docker exec mirai-prometheus wget -O- http://host.docker.internal:5000/api/v1/metrics

# または、prometheus.ymlでlocalhostの代わりにホストIPを使用
```

### Grafanaにデータが表示されない

1. データソース接続確認
2. クエリが正しいか確認
3. 時間範囲が適切か確認
4. Prometheusにデータがあるか確認

## 完了確認

すべてのチェック項目が完了したら、監視システムのセットアップは完了です。

- [ ] すべてのサービスが起動している
- [ ] メトリクスが収集されている
- [ ] Grafanaダッシュボードにデータが表示されている
- [ ] アラートルールが設定されている
- [ ] ドキュメントを確認した

## 次のステップ

1. **セキュリティ設定**
   - Grafana管理者パスワード変更
   - 認証・認可の設定
   - ファイアウォール設定

2. **アラート通知設定**
   - alertmanager.yml でメール/Slack設定
   - テストアラート送信

3. **カスタマイズ**
   - 独自のダッシュボード作成
   - 追加メトリクスの実装
   - アラートルールの調整

4. **バックアップ設定**
   - Prometheusデータのバックアップ
   - Grafanaダッシュボードのエクスポート

---

**検証日時**: ____________
**検証者**: ____________
**結果**: ⬜ 成功 / ⬜ 失敗（理由: ________________）
