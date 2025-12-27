# 運用マニュアル

## 概要

このドキュメントは、建設土木ナレッジシステムの本番環境における日常的な運用、監視、バックアップ、障害対応の手順を包括的に説明する運用マニュアルです。

## 目次

1. [日常運用](#日常運用)
2. [監視とアラート](#監視とアラート)
3. [バックアップとリストア](#バックアップとリストア)
4. [障害対応](#障害対応)
5. [メンテナンス作業](#メンテナンス作業)
6. [セキュリティ運用](#セキュリティ運用)
7. [パフォーマンス最適化](#パフォーマンス最適化)

---

## 日常運用

### 起動・停止・再起動

#### アプリケーションの起動

```bash
cd /opt/mirai-knowledge-systems/backend
./run_production.sh start
```

#### アプリケーションの停止

```bash
./run_production.sh stop
```

#### アプリケーションの再起動

```bash
./run_production.sh restart
```

#### 状態確認

```bash
./run_production.sh status
```

出力例:
```
[INFO] サーバーは起動しています (PID: 12345)
[INFO] アクティブワーカー数: 4
[INFO] メモリ使用量 (マスター): 85.3MB
```

#### 設定のリロード（ダウンタイムなし）

```bash
./run_production.sh reload
```

#### Systemdサービス経由（サービス化している場合）

```bash
# 起動
sudo systemctl start mirai-knowledge-system

# 停止
sudo systemctl stop mirai-knowledge-system

# 再起動
sudo systemctl restart mirai-knowledge-system

# 状態確認
sudo systemctl status mirai-knowledge-system

# ログ表示
sudo journalctl -u mirai-knowledge-system -f
```

### ログの確認

#### アプリケーションログ

```bash
# リアルタイム監視
tail -f /var/log/mirai-knowledge-system/app.log

# エラーログのみ
tail -f /var/log/mirai-knowledge-system/app.log | grep ERROR

# 最新100行
tail -n 100 /var/log/mirai-knowledge-system/app.log
```

#### Gunicornログ

```bash
# アクセスログ
tail -f /opt/mirai-knowledge-systems/backend/logs/access.log

# エラーログ
tail -f /opt/mirai-knowledge-systems/backend/logs/error.log
```

#### Nginxログ

```bash
# アクセスログ
sudo tail -f /var/log/nginx/mirai-knowledge-system-access.log

# エラーログ
sudo tail -f /var/log/nginx/mirai-knowledge-system-error.log

# 特定のIPアドレスからのアクセス
sudo grep "192.168.1.100" /var/log/nginx/mirai-knowledge-system-access.log
```

#### システムログ

```bash
# 全体のシステムログ
sudo journalctl -xe

# 特定のサービスのログ
sudo journalctl -u nginx -f
sudo journalctl -u mirai-knowledge-system -f
```

### ログ分析

#### エラー発生件数の確認

```bash
# 過去1時間のエラー数
grep -c "ERROR" /var/log/mirai-knowledge-system/app.log

# 日時別のエラー集計
awk '/ERROR/ {print substr($1,1,13)}' /var/log/mirai-knowledge-system/app.log | sort | uniq -c
```

#### アクセス数の統計

```bash
# 1日のアクセス数
cat /var/log/nginx/mirai-knowledge-system-access.log | wc -l

# IPアドレス別アクセス数（上位10件）
awk '{print $1}' /var/log/nginx/mirai-knowledge-system-access.log | sort | uniq -c | sort -rn | head -10

# エンドポイント別アクセス数
awk '{print $7}' /var/log/nginx/mirai-knowledge-system-access.log | sort | uniq -c | sort -rn | head -10
```

---

## 監視とアラート

### 基本的なヘルスチェック

#### サービス稼働確認

```bash
# HTTPSエンドポイントの確認
curl -f https://api.example.com/ || echo "Service Down!"

# レスポンスタイム測定
time curl -s https://api.example.com/ > /dev/null
```

#### リソース使用状況の確認

```bash
# CPU使用率
top -b -n 1 | grep "Cpu(s)"

# メモリ使用状況
free -h

# ディスク使用状況
df -h

# プロセス別リソース使用状況
ps aux | grep gunicorn
```

### Cronによる定期監視

#### ヘルスチェックスクリプトの作成

```bash
sudo nano /opt/mirai-knowledge-systems/backend/scripts/health_check.sh
```

```bash
#!/bin/bash
# ヘルスチェックスクリプト

ENDPOINT="https://api.example.com/"
EMAIL="admin@example.com"
LOG_FILE="/var/log/mirai-knowledge-system/health_check.log"

# ヘルスチェック実行
if curl -f -s -o /dev/null -w "%{http_code}" "$ENDPOINT" | grep -q "200"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - OK: Service is running" >> "$LOG_FILE"
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Service is down" >> "$LOG_FILE"
    echo "Service health check failed at $(date)" | mail -s "API Service Down Alert" "$EMAIL"
    exit 1
fi
```

```bash
# 実行権限を付与
sudo chmod +x /opt/mirai-knowledge-systems/backend/scripts/health_check.sh
```

#### Cronジョブの設定

```bash
crontab -e
```

```bash
# 5分ごとにヘルスチェック
*/5 * * * * /opt/mirai-knowledge-systems/backend/scripts/health_check.sh

# 毎日午前9時にディスク使用量チェック
0 9 * * * df -h | grep -E '^/dev/' | awk '$5 > "80%" {print}' | mail -s "Disk Usage Alert" admin@example.com

# 毎週月曜日午前9時にSSL証明書有効期限チェック
0 9 * * 1 certbot certificates | grep -A2 "Expiry Date" | mail -s "SSL Certificate Status" admin@example.com

# 毎日午前3時にログローテーション後のクリーンアップ
0 3 * * * find /var/log/mirai-knowledge-system -name "*.gz" -mtime +30 -delete
```

### システムメトリクスの監視

#### リソース使用率のスクリプト

```bash
sudo nano /opt/mirai-knowledge-systems/backend/scripts/system_metrics.sh
```

```bash
#!/bin/bash
# システムメトリクス収集スクリプト

METRICS_FILE="/var/log/mirai-knowledge-system/metrics.log"

# CPU使用率
CPU_USAGE=$(top -b -n 1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

# メモリ使用率
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')

# ディスク使用率
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')

# ログに記録
echo "$(date '+%Y-%m-%d %H:%M:%S'),CPU:${CPU_USAGE},Memory:${MEMORY_USAGE},Disk:${DISK_USAGE}" >> "$METRICS_FILE"

# アラート条件チェック
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "High CPU usage: ${CPU_USAGE}%" | mail -s "CPU Alert" admin@example.com
fi

if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
    echo "High memory usage: ${MEMORY_USAGE}%" | mail -s "Memory Alert" admin@example.com
fi

if [ "$DISK_USAGE" -gt 85 ]; then
    echo "High disk usage: ${DISK_USAGE}%" | mail -s "Disk Alert" admin@example.com
fi
```

```bash
chmod +x /opt/mirai-knowledge-systems/backend/scripts/system_metrics.sh
```

Cronに追加:
```bash
# 10分ごとにメトリクス収集
*/10 * * * * /opt/mirai-knowledge-systems/backend/scripts/system_metrics.sh
```

---

## バックアップとリストア

### バックアップ戦略

#### バックアップ対象

1. **データファイル**: `/var/lib/mirai-knowledge-system/data`
2. **設定ファイル**: `.env.production`
3. **PostgreSQLデータベース**（使用している場合）
4. **SSL証明書**: `/etc/letsencrypt`（オプション）

#### バックアップスケジュール

- **日次バックアップ**: 毎日午前3時
- **週次バックアップ**: 毎週日曜日
- **保持期間**: 日次30日、週次12週、月次12ヶ月

### バックアップスクリプト

#### 包括的なバックアップスクリプト

```bash
sudo nano /opt/mirai-knowledge-systems/backend/scripts/backup.sh
```

```bash
#!/bin/bash
# ==========================================================
# 建設土木ナレッジシステム - バックアップスクリプト
# ==========================================================

set -e

# 設定
BACKUP_ROOT="/var/backups/mirai-knowledge-system"
DATA_DIR="/var/lib/mirai-knowledge-system/data"
CONFIG_DIR="/opt/mirai-knowledge-systems/backend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y%m%d)

# バックアップタイプ（daily/weekly/monthly）
BACKUP_TYPE="${1:-daily}"

# バックアップディレクトリ作成
BACKUP_DIR="$BACKUP_ROOT/$BACKUP_TYPE/$DATE"
mkdir -p "$BACKUP_DIR"

# ログ設定
LOG_FILE="$BACKUP_ROOT/backup.log"
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "========== バックアップ開始 ($BACKUP_TYPE) =========="

# 1. データディレクトリのバックアップ
log "データディレクトリをバックアップ中..."
if [ -d "$DATA_DIR" ]; then
    tar -czf "$BACKUP_DIR/data_$TIMESTAMP.tar.gz" -C "$DATA_DIR" .
    log "データディレクトリのバックアップ完了: data_$TIMESTAMP.tar.gz"
else
    log "警告: データディレクトリが見つかりません: $DATA_DIR"
fi

# 2. 設定ファイルのバックアップ
log "設定ファイルをバックアップ中..."
if [ -f "$CONFIG_DIR/.env.production" ]; then
    cp "$CONFIG_DIR/.env.production" "$BACKUP_DIR/env.production_$TIMESTAMP"
    log "設定ファイルのバックアップ完了"
else
    log "警告: .env.production が見つかりません"
fi

# 3. PostgreSQLデータベースのバックアップ（使用している場合）
if command -v pg_dump &> /dev/null; then
    log "PostgreSQLデータベースをバックアップ中..."
    # 環境変数から接続情報を取得
    if [ -f "$CONFIG_DIR/.env.production" ]; then
        source "$CONFIG_DIR/.env.production"
        if [ -n "$MKS_DATABASE_URL" ]; then
            # DATABASE_URLからデータベース名を抽出
            DB_NAME=$(echo "$MKS_DATABASE_URL" | sed -n 's|.*://.*/.*/\([^?]*\).*|\1|p')
            if [ -n "$DB_NAME" ]; then
                pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/database_$TIMESTAMP.sql.gz"
                log "データベースのバックアップ完了: database_$TIMESTAMP.sql.gz"
            fi
        fi
    fi
fi

# 4. SSL証明書のバックアップ（オプション）
if [ -d "/etc/letsencrypt" ]; then
    log "SSL証明書をバックアップ中..."
    sudo tar -czf "$BACKUP_DIR/letsencrypt_$TIMESTAMP.tar.gz" -C /etc letsencrypt
    log "SSL証明書のバックアップ完了"
fi

# 5. バックアップサイズの記録
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "バックアップサイズ: $TOTAL_SIZE"

# 6. 古いバックアップの削除
log "古いバックアップを削除中..."

# 日次バックアップは30日以前を削除
find "$BACKUP_ROOT/daily" -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true

# 週次バックアップは12週（84日）以前を削除
find "$BACKUP_ROOT/weekly" -type d -mtime +84 -exec rm -rf {} + 2>/dev/null || true

# 月次バックアップは12ヶ月（365日）以前を削除
find "$BACKUP_ROOT/monthly" -type d -mtime +365 -exec rm -rf {} + 2>/dev/null || true

log "========== バックアップ完了 =========="

# 7. バックアップ検証
log "バックアップを検証中..."
for file in "$BACKUP_DIR"/*.tar.gz; do
    if [ -f "$file" ]; then
        if tar -tzf "$file" > /dev/null 2>&1; then
            log "検証OK: $(basename $file)"
        else
            log "エラー: バックアップが破損しています: $(basename $file)"
            exit 1
        fi
    fi
done

log "すべてのバックアップが正常に完了しました"

# 8. バックアップ通知（オプション）
if [ -n "$BACKUP_EMAIL" ]; then
    echo "バックアップが正常に完了しました。サイズ: $TOTAL_SIZE" | \
        mail -s "Backup Success - $BACKUP_TYPE" "$BACKUP_EMAIL"
fi

exit 0
```

```bash
# 実行権限を付与
sudo chmod +x /opt/mirai-knowledge-systems/backend/scripts/backup.sh
```

#### バックアップのCron設定

```bash
sudo crontab -e
```

```bash
# 日次バックアップ（毎日午前3時）
0 3 * * * /opt/mirai-knowledge-systems/backend/scripts/backup.sh daily

# 週次バックアップ（毎週日曜日午前2時）
0 2 * * 0 /opt/mirai-knowledge-systems/backend/scripts/backup.sh weekly

# 月次バックアップ（毎月1日午前1時）
0 1 1 * * /opt/mirai-knowledge-systems/backend/scripts/backup.sh monthly
```

### リストア手順

#### データディレクトリのリストア

```bash
# 1. サービスを停止
cd /opt/mirai-knowledge-systems/backend
./run_production.sh stop

# 2. 現在のデータをバックアップ（念のため）
sudo mv /var/lib/mirai-knowledge-system/data /var/lib/mirai-knowledge-system/data.old

# 3. バックアップから復元
sudo mkdir -p /var/lib/mirai-knowledge-system/data
sudo tar -xzf /var/backups/mirai-knowledge-system/daily/20241227/data_*.tar.gz \
    -C /var/lib/mirai-knowledge-system/data

# 4. 権限を設定
sudo chown -R $USER:$USER /var/lib/mirai-knowledge-system/data

# 5. サービスを起動
./run_production.sh start

# 6. 動作確認
curl https://api.example.com/api/v1/knowledge
```

#### データベースのリストア

```bash
# 1. サービスを停止
./run_production.sh stop

# 2. データベースを削除して再作成
sudo -u postgres psql
DROP DATABASE mirai_knowledge;
CREATE DATABASE mirai_knowledge;
GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge TO mks_user;
\q

# 3. バックアップから復元
gunzip < /var/backups/mirai-knowledge-system/daily/20241227/database_*.sql.gz | \
    sudo -u postgres psql mirai_knowledge

# 4. サービスを起動
./run_production.sh start
```

#### 設定ファイルのリストア

```bash
# バックアップから設定ファイルを復元
sudo cp /var/backups/mirai-knowledge-system/daily/20241227/env.production_* \
    /opt/mirai-knowledge-systems/backend/.env.production

# 権限を設定
sudo chmod 600 /opt/mirai-knowledge-systems/backend/.env.production
```

---

## 障害対応

### 障害対応フローチャート

```
┌─────────────────┐
│  障害を検知     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. 影響範囲確認  │
│ 2. ログ確認      │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ 原因特定 │
    └───┬────┘
        │
   ┌────┴─────┐
   │          │
   ▼          ▼
┌──────┐  ┌────────┐
│即座に│  │調査が  │
│対応可│  │必要    │
└──┬───┘  └───┬────┘
   │          │
   ▼          ▼
┌──────┐  ┌────────┐
│対処  │  │エスカレ│
│実施  │  │ーション│
└──┬───┘  └───┬────┘
   │          │
   └────┬─────┘
        │
        ▼
   ┌─────────┐
   │動作確認  │
   └────┬────┘
        │
        ▼
   ┌─────────┐
   │報告書作成│
   └─────────┘
```

### よくある障害とその対処法

#### 1. サービスが起動しない

**症状**:
```bash
./run_production.sh start
# エラー: サーバーの起動に失敗しました
```

**確認手順**:

```bash
# 1. エラーログを確認
tail -f /opt/mirai-knowledge-systems/backend/logs/error.log

# 2. ポートの使用状況を確認
sudo lsof -i :8000

# 3. 環境変数を確認
./run_production.sh check

# 4. Pythonモジュールの確認
cd /opt/mirai-knowledge-systems/backend
source venv/bin/activate
python3 -c "from app_v2 import app; print('OK')"
```

**対処方法**:

a) ポートが既に使用されている場合:
```bash
# プロセスを特定
sudo lsof -i :8000
# プロセスを終了
sudo kill -9 {PID}
# 再起動
./run_production.sh start
```

b) 環境変数が不足している場合:
```bash
# .env.production を確認
cat .env.production | grep -E "SECRET_KEY|JWT_SECRET_KEY|CORS_ORIGINS"
# 不足している変数を追加
```

c) 依存関係の問題:
```bash
source venv/bin/activate
pip install -r requirements.txt
./run_production.sh restart
```

#### 2. 502 Bad Gateway

**症状**: ブラウザで `502 Bad Gateway` エラーが表示される

**確認手順**:

```bash
# 1. Gunicornが起動しているか確認
./run_production.sh status

# 2. Nginxのエラーログを確認
sudo tail -f /var/log/nginx/mirai-knowledge-system-error.log

# 3. ポート8000への接続を確認
curl http://127.0.0.1:8000
```

**対処方法**:

```bash
# Gunicornが停止している場合
./run_production.sh start

# Nginxの設定が間違っている場合
sudo nginx -t
sudo systemctl reload nginx

# タイムアウトの場合、Nginx設定を調整
# proxy_read_timeout を増やす
```

#### 3. SSL証明書エラー

**症状**: HTTPSアクセス時に証明書エラーが表示される

**確認手順**:

```bash
# 証明書の状態を確認
sudo certbot certificates

# 証明書の有効期限を確認
openssl x509 -in /etc/letsencrypt/live/api.example.com/cert.pem -noout -dates
```

**対処方法**:

```bash
# 証明書が期限切れの場合
sudo certbot renew

# 証明書の再取得
sudo certbot certonly --nginx -d api.example.com --force-renewal

# Nginxを再起動
sudo systemctl reload nginx
```

#### 4. メモリ不足

**症状**: サーバーの応答が遅い、または OOM (Out of Memory) エラーが発生

**確認手順**:

```bash
# メモリ使用状況を確認
free -h

# プロセス別メモリ使用量
ps aux --sort=-%mem | head -10

# システムログでOOMキラーを確認
sudo dmesg | grep -i "out of memory"
```

**対処方法**:

```bash
# 1. 不要なプロセスを終了

# 2. Gunicornのワーカー数を減らす
# .env.production を編集
MKS_GUNICORN_WORKERS=2

# 3. サービスを再起動
./run_production.sh restart

# 4. スワップ領域の追加（恒久的な対策が必要な場合）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 5. ディスク容量不足

**症状**: ログファイルが書き込めない、データベースエラー

**確認手順**:

```bash
# ディスク使用状況
df -h

# 大きなファイルを検索
sudo du -h /var/log | sort -rh | head -10
sudo du -h /var/lib/mirai-knowledge-system | sort -rh | head -10
```

**対処方法**:

```bash
# 1. 古いログファイルを削除
sudo find /var/log -name "*.log.*" -mtime +30 -delete
sudo find /var/log -name "*.gz" -mtime +30 -delete

# 2. ログローテーションを実行
sudo logrotate -f /etc/logrotate.conf

# 3. 古いバックアップを削除
sudo find /var/backups -type f -mtime +90 -delete

# 4. APTキャッシュをクリア
sudo apt clean
```

#### 6. 認証エラー（401 Unauthorized）

**症状**: APIリクエストで認証エラーが頻発する

**確認手順**:

```bash
# ログで認証エラーを確認
grep "401\|UNAUTHORIZED" /var/log/mirai-knowledge-system/app.log

# JWT設定を確認
grep JWT_SECRET_KEY .env.production
```

**対処方法**:

```bash
# 1. トークンの有効期限を確認
# クライアント側でトークンリフレッシュが正しく実装されているか確認

# 2. JWT_SECRET_KEYが変更された場合
# すべてのユーザーに再ログインを促す

# 3. システム時刻のずれを確認
timedatectl status
# 時刻がずれている場合は同期
sudo timedatectl set-ntp true
```

---

## メンテナンス作業

### 定期メンテナンス

#### 日次メンテナンス

- [ ] サービス稼働状況の確認
- [ ] エラーログの確認（ERROR件数）
- [ ] ディスク使用率の確認

#### 週次メンテナンス

- [ ] バックアップの動作確認
- [ ] SSL証明書の有効期限確認
- [ ] セキュリティアップデートの確認と適用
- [ ] アクセスログの分析

#### 月次メンテナンス

- [ ] システム全体のリソース使用状況レビュー
- [ ] パフォーマンスメトリクスの分析
- [ ] 不要なログファイルの削除
- [ ] バックアップリストアテスト

### アップデート手順

#### アプリケーションのアップデート

```bash
# 1. バックアップを作成
/opt/mirai-knowledge-systems/backend/scripts/backup.sh manual

# 2. 最新コードを取得
cd /opt/mirai-knowledge-systems
git fetch origin
git status

# 3. 変更内容を確認
git log --oneline HEAD..origin/main
git diff HEAD..origin/main

# 4. サービスを停止
cd backend
./run_production.sh stop

# 5. コードを更新
git pull origin main

# 6. 依存関係を更新
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 7. データベースマイグレーション（必要に応じて）
# python migrate.py

# 8. 設定チェック
./run_production.sh check

# 9. サービスを起動
./run_production.sh start

# 10. 動作確認
curl https://api.example.com/api/v1/knowledge

# 11. ログを監視
tail -f logs/error.log
```

#### OSセキュリティパッチの適用

```bash
# 1. 利用可能なアップデートを確認
sudo apt update
sudo apt list --upgradable

# 2. セキュリティアップデートのみ適用
sudo apt upgrade -y

# 3. システムの再起動が必要か確認
if [ -f /var/run/reboot-required ]; then
    echo "再起動が必要です"
    # 計画的に再起動を実施
fi

# 4. Nginxとアプリケーションの再起動
sudo systemctl restart nginx
./run_production.sh restart
```

#### Pythonパッケージの更新

```bash
cd /opt/mirai-knowledge-systems/backend
source venv/bin/activate

# 1. 現在のバージョンを確認
pip list

# 2. 古いパッケージを確認
pip list --outdated

# 3. 特定のパッケージを更新
pip install --upgrade flask

# 4. すべてのパッケージを更新（慎重に）
pip install --upgrade -r requirements.txt

# 5. requirements.txtを更新
pip freeze > requirements.txt

# 6. 動作テスト
python3 -c "from app_v2 import app; print('OK')"

# 7. サービスを再起動
./run_production.sh restart
```

---

## セキュリティ運用

### セキュリティチェックリスト

#### 日次チェック

- [ ] 異常なログイン試行の監視
- [ ] 不正なアクセスパターンの検出

```bash
# 失敗したログイン試行を確認
grep "Invalid username or password" /var/log/mirai-knowledge-system/app.log | tail -20

# 大量のリクエストがあるIPを確認
awk '{print $1}' /var/log/nginx/mirai-knowledge-system-access.log | sort | uniq -c | sort -rn | head -10
```

#### 週次チェック

- [ ] SSL証明書の有効期限確認
- [ ] ファイアウォールルールの確認
- [ ] 不要なポートが開いていないか確認

```bash
# SSL証明書の確認
sudo certbot certificates

# 開いているポートを確認
sudo ss -tuln

# ファイアウォールの状態確認
sudo ufw status verbose
```

#### 月次チェック

- [ ] セキュリティパッチの適用
- [ ] アクセス権限の見直し
- [ ] 不要なユーザーアカウントの削除
- [ ] パスワードポリシーの確認

### セキュリティインシデント対応

#### 不正アクセスが疑われる場合

1. **即座にアクセスをブロック**:
```bash
# 特定のIPアドレスをブロック
sudo ufw deny from 192.168.1.100

# Nginxでブロック
sudo nano /etc/nginx/sites-available/mirai-knowledge-system
# deny 192.168.1.100; を追加
sudo systemctl reload nginx
```

2. **ログを保全**:
```bash
# ログを別の場所にコピー
sudo cp -r /var/log/nginx /var/backups/incident_$(date +%Y%m%d)/
sudo cp -r /var/log/mirai-knowledge-system /var/backups/incident_$(date +%Y%m%d)/
```

3. **影響範囲を調査**:
```bash
# 該当IPからのアクセスを確認
grep "192.168.1.100" /var/log/nginx/mirai-knowledge-system-access.log

# アクセスされたエンドポイントを確認
grep "192.168.1.100" /var/log/nginx/mirai-knowledge-system-access.log | awk '{print $7}' | sort | uniq -c
```

4. **パスワードをリセット**:
```bash
# 影響を受けた可能性のあるユーザーのパスワードを強制的にリセット
# 管理画面またはCLIツールを使用
```

---

## パフォーマンス最適化

### パフォーマンス監視

#### レスポンスタイムの測定

```bash
# 平均レスポンスタイムを計算
awk '{print $10}' /var/log/nginx/mirai-knowledge-system-access.log | \
    awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'

# 遅いエンドポイントを特定
awk '$10 > 1000 {print $7, $10}' /var/log/nginx/mirai-knowledge-system-access.log | \
    sort | uniq -c | sort -rn | head -10
```

#### データベースパフォーマンス

PostgreSQL使用時:
```bash
# スロークエリの確認
sudo -u postgres psql -d mirai_knowledge -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### 最適化施策

#### 1. Gunicornワーカー数の調整

```bash
# 推奨: (CPUコア数 * 2) + 1
# 4コアの場合: 9ワーカー

# .env.production を編集
MKS_GUNICORN_WORKERS=9

./run_production.sh restart
```

#### 2. Nginxキャッシュの有効化

```nginx
# /etc/nginx/sites-available/mirai-knowledge-system

# キャッシュ設定を追加
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

server {
    # ...
    location /api/v1/knowledge {
        proxy_cache api_cache;
        proxy_cache_valid 200 5m;
        proxy_cache_use_stale error timeout updating;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

#### 3. データベース接続プーリング

PostgreSQL使用時、pgbouncerの導入を検討:

```bash
sudo apt install pgbouncer
# 設定はプロジェクトの要件に応じて調整
```

---

## まとめ

このマニュアルに従うことで、建設土木ナレッジシステムの安定した運用が可能になります。

### 重要なポイント

1. **定期的な監視**: ヘルスチェックとメトリクス収集を自動化
2. **確実なバックアップ**: 日次バックアップと定期的なリストアテスト
3. **迅速な障害対応**: 障害発生時のフローチャートに従って対応
4. **セキュリティ**: 定期的なパッチ適用とログ監視
5. **ドキュメント**: インシデント対応の記録と改善

### エスカレーション

解決できない問題が発生した場合:

1. ログを収集（アプリケーション、Nginx、システム）
2. 再現手順を記録
3. 開発チームまたはシステム管理者に連絡

---

## 関連ドキュメント

- [本番環境移行チェックリスト](../10_移行・展開(Deployment)/04_Production-Migration-Checklist.md)
- [HTTPS移行ガイド](../10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md)
- [API仕様書](../08_API連携(Integrations)/03_API-Reference-Complete.md)

---

**最終更新日**: 2024年12月27日
**バージョン**: 1.0.0
