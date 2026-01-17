# 定期メンテナンス (Regular Maintenance)

## 概要
システムの安定稼働、セキュリティ、パフォーマンスを維持するための定期メンテナンス手順です。

## メンテナンス計画

### メンテナンスレベル
- **レベル1**: システム停止を伴わない軽微な作業
- **レベル2**: 短時間停止を伴う作業（5-15分）
- **レベル3**: 長時間停止を伴う作業（30分以上）

### メンテナンススケジュール
| 頻度 | 作業内容 | レベル | 所要時間 | 担当 |
|------|---------|--------|----------|------|
| 毎日 | バックアップ確認 | 1 | 5分 | 自動/SRE |
| 毎週 | システムチェック | 1 | 30分 | SRE |
| 毎月 | セキュリティ更新 | 2 | 1時間 | SRE |
| 毎四半期 | 包括的レビュー | 3 | 4時間 | 全チーム |

## 毎週メンテナンス

### 月曜日 02:00 - システムヘルスチェック
**目的**: システムの基本的な健全性を確認

#### 1. ログ管理
```bash
# ログディスク容量確認
df -h /var/log
LOG_USAGE=$(df /var/log | tail -1 | awk '{print $5}' | sed 's/%//')

if [ $LOG_USAGE -gt 80 ]; then
    echo "WARNING: Log disk usage is ${LOG_USAGE}%"
    # ログローテーション実行
    logrotate -f /etc/logrotate.d/mks-backend
fi

# ログファイルサイズ確認
find /var/log/mks-backend/ -name "*.log" -size +100M -exec ls -lh {} \;
```

#### 2. バックアップ確認
```bash
# バックアップファイル存在確認
BACKUP_DIR="/backup/mks"
LATEST_DB=$(find $BACKUP_DIR -name "db_*.dump" -mtime -1 | wc -l)
LATEST_UPLOADS=$(find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime -1 | wc -l)

if [ $LATEST_DB -eq 0 ] || [ $LATEST_UPLOADS -eq 0 ]; then
    echo "ERROR: Missing recent backup"
    # アラート送信
fi

# バックアップ整合性確認
pg_restore --list $BACKUP_DIR/$(ls -t $BACKUP_DIR/db_*.dump | head -1) > /dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Backup corruption detected"
fi
```

#### 3. SSL証明書管理
```bash
# 証明書期限確認
CERT_EXPIRY=$(openssl x509 -in /etc/letsencrypt/live/example.com/cert.pem -text | grep "Not After" | cut -d: -f2-)
EXPIRY_DATE=$(date -d "$CERT_EXPIRY" +%s)
CURRENT_DATE=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_DATE - $CURRENT_DATE) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "WARNING: SSL certificate expires in ${DAYS_LEFT} days"
    # 自動更新実行
    certbot renew --quiet
fi
```

#### 4. パフォーマンス監視
```bash
# CPU使用率確認
CPU_IDLE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/")
CPU_USAGE=$(echo "100 - $CPU_IDLE" | bc)

if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "WARNING: High CPU usage: ${CPU_USAGE}%"
fi

# メモリ使用率確認
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')

if [ $MEM_USAGE -gt 80 ]; then
    echo "WARNING: High memory usage: ${MEM_USAGE}%"
fi

# ディスクI/O確認
IOSTAT=$(iostat -x 1 5 | tail -1 | awk '{print $NF}')
if (( $(echo "$IOSTAT > 80" | bc -l) )); then
    echo "WARNING: High I/O wait: ${IOSTAT}%"
fi
```

### 水曜日 02:00 - セキュリティチェック
**目的**: セキュリティ脅威からの保護

#### 1. セキュリティパッチ適用
```bash
# 更新可能なパッケージ確認
apt update
SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c "security")

if [ $SECURITY_UPDATES -gt 0 ]; then
    echo "INFO: ${SECURITY_UPDATES} security updates available"
    # セキュリティ更新適用
    apt install --only-upgrade $(apt list --upgradable 2>/dev/null | grep "security" | cut -d/ -f1)
fi
```

#### 2. ファイアウォール確認
```bash
# UFWステータス確認
ufw status | grep -E "(Status|5100|80|443)"

# 不審な接続確認
netstat -tuln | grep LISTEN
ss -tuln | grep LISTEN
```

#### 3. アクセスログ監査
```bash
# ブルートフォース攻撃検知
AUTH_LOG="/var/log/nginx/access.log"
BRUTE_FORCE=$(grep "POST /api/v1/auth/login" $AUTH_LOG | grep " 401 " | wc -l)

if [ $BRUTE_FORCE -gt 10 ]; then
    echo "WARNING: Potential brute force attack detected: ${BRUTE_FORCE} failed login attempts"
fi

# 不審なIPアドレス確認
grep " 40[0-9] " $AUTH_LOG | cut -d' ' -f1 | sort | uniq -c | sort -nr | head -10
```

## 毎月メンテナンス

### 第1月曜日 03:00 - システム更新
**目的**: ソフトウェアの最新化と最適化

#### 1. パッケージ更新
```bash
# 全パッケージ更新
apt update && apt upgrade -y

# Pythonパッケージ更新
cd /opt/mks/backend
pip install --upgrade -r requirements.txt

# 再起動が必要なサービス確認
needs-restarting -s
```

#### 2. データベース最適化
```bash
# VACUUM ANALYZE実行
psql -U mks_user -d mks_db -c "VACUUM ANALYZE;"

# インデックス使用統計確認
psql -U mks_user -d mks_db -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC
LIMIT 10;
"

# 未使用インデックス確認
psql -U mks_user -d mks_db -c "
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname NOT IN (
    SELECT indexname
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public'
    AND idx_scan > 0
);
"
```

#### 3. ログローテーション設定確認
```bash
# logrotate設定確認
cat /etc/logrotate.d/mks-backend

# 手動実行テスト
logrotate -d /etc/logrotate.d/mks-backend

# 古いログ削除
find /var/log/mks-backend/ -name "*.log.*" -mtime +90 -delete
```

#### 4. バックアップテスト
```bash
# バックアップ実行
bash scripts/backup.sh

# リストアテスト（ステージング環境）
BACKUP_FILE=$(ls -t /backup/mks/db_*.dump | head -1)
pg_restore -U mks_user -d mks_test --clean --if-exists $BACKUP_FILE

# リストア成功確認
psql -U mks_user -d mks_test -c "SELECT COUNT(*) FROM projects;"
```

### 第3月曜日 03:00 - パフォーマンス最適化
**目的**: システムパフォーマンスの維持

#### 1. キャッシュクリア
```bash
# システムキャッシュクリア
sync; echo 3 > /proc/sys/vm/drop_caches

# アプリケーションキャッシュクリア
curl -X POST http://localhost:5100/api/v1/admin/cache/clear \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Redisキャッシュクリア（使用する場合）
redis-cli FLUSHALL
```

#### 2. 一時ファイルクリーンアップ
```bash
# 古い一時ファイル削除
find /tmp -name "mks_*" -mtime +7 -delete
find /var/tmp -name "mks_*" -mtime +30 -delete

# アップロード一時ファイル
find /opt/mks/uploads/temp/ -mtime +1 -delete

# セッションファイル
find /opt/mks/sessions/ -name "sess_*" -mtime +30 -delete
```

#### 3. プロセス最適化
```bash
# ゾンビプロセス確認
ps aux | awk '{print $8}' | grep -c "Z"

# メモリリーク確認
ps aux --sort=-%mem | head -10

# Gunicornワーカー数最適化
# /etc/systemd/system/mks-backend.service 確認
grep "workers" /etc/systemd/system/mks-backend.service
```

## 毎四半期メンテナンス

### 第1四半期 - 包括的レビュー
**目的**: システム全体の健全性評価

#### 1. DR（災害復旧）訓練
```bash
# フェイルオーバーテスト
# バックアップからの完全リストアテスト
# RTO/RPO測定

# テストシナリオ
echo "=== DR Test Scenario ==="
echo "1. Primary server failure simulation"
echo "2. Backup restoration"
echo "3. Service recovery"
echo "4. Data integrity check"
```

#### 2. アラート設定見直し
```bash
# アラートルール確認
cat /etc/prometheus/rules.yml

# 誤検知分析（過去3ヶ月）
# アラート発生数 vs 実際の障害数

# 新しいアラートルール追加
# - APIエラーレート上昇
# - データベース接続プール枯渇
# - メモリリーク検知
```

#### 3. Runbook更新
```bash
# 手順の正確性確認
# 過去インシデントからの学び反映
# 新シナリオ追加

# 更新内容
# - 新機能対応
# - ツール変更反映
# - プロセス改善
```

#### 4. セキュリティ監査
```bash
# 脆弱性スキャン
nmap -sV --script vuln localhost

# ファイル権限確認
find /opt/mks -type f -perm /o+w
find /etc/mks -type f -perm /o+r

# パスワードポリシー確認
chage -l mks_user

# 暗号化設定確認
grep "ssl" /etc/postgresql/13/main/postgresql.conf
```

### 第2四半期 - パフォーマンスレビュー
**目的**: 容量計画とスケーリング計画

#### 1. 容量計画見直し
```bash
# ディスク使用量トレンド
df -h
du -sh /opt/mks/uploads/
du -sh /var/log/mks-backend/

# CPU/メモリ使用量予測
# 過去6ヶ月のメトリクス分析

# スケーリング計画策定
# - 垂直スケーリング（リソース増強）
# - 水平スケーリング（サーバー増設）
```

#### 2. バックアップ戦略見直し
```bash
# バックアップ頻度調整
# 保存期間見直し
# バックアップ方式改善（増分バックアップ導入）

# バックアップ検証
# - リストア時間測定
# - データ整合性確認
# - バックアップサイズ最適化
```

### 第3四半期 - プロセス改善
**目的**: 運用プロセスの最適化

#### 1. インシデントレビュー
```bash
# 過去四半期のインシデント分析
# - 発生パターン
# - 対応時間
# - 再発防止策実施状況

# 統計分析
# - MTTR改善
# - インシデント率
# - 顧客影響度
```

#### 2. トレーニング実施
```bash
# 新人向け運用トレーニング
# - システム概要
# - 障害対応手順
# - ツール使用方法

# チームトレーニング
# - 障害シミュレーション
# - コミュニケーション演習
# - プロセス改善ワークショップ
```

### 第4四半期 - 年末調整
**目的**: 次年度の準備と総括

#### 1. 年間レポート作成
```bash
# 可用性レポート
# - アップタイム統計
# - 障害発生数/時間
# - SLA達成率

# インシデント統計
# - インシデント分類
# - 対応時間分布
# - 根本原因分析

# 改善施策まとめ
# - 実施した改善
# - 効果測定
# - 今後の計画
```

#### 2. 予算計画
```bash
# 次年度インフラ予算策定
# - ハードウェア更新
# - ソフトウェアライセンス
# - クラウドリソース

# トレーニング予算確保
# - 外部研修
# - ツール導入
# - チーム拡大
```

## メンテナンス自動化

### Cron設定
```bash
# /etc/cron.d/mks-maintenance
# 毎週月曜日 2:00 - 週次チェック
0 2 * * 1 root /opt/mks/scripts/weekly-check.sh

# 毎月第1月曜日 3:00 - 月次メンテナンス
0 3 1-7 * * root [ "$(date '+\%u')" = "1" ] && /opt/mks/scripts/monthly-maintenance.sh

# 毎日 2:00 - バックアップ
0 2 * * * root /opt/mks/scripts/backup.sh

# 毎週日曜日 3:00 - ログローテーション
0 3 * * 0 root /opt/mks/scripts/log-rotate.sh

# 毎月1日 4:00 - セキュリティ更新
0 4 1 * * root /opt/mks/scripts/security-update.sh
```

### 自動化スクリプト例
```bash
#!/bin/bash
# scripts/weekly-check.sh

LOG_FILE="/var/log/mks-maintenance.log"
echo "=== Weekly Check Started: $(date) ===" >> $LOG_FILE

# ディスク容量チェック
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage ${DISK_USAGE}%" >> $LOG_FILE
fi

# バックアップ確認
if ! find /backup/mks/ -name "*.dump" -mtime -1 | grep -q .; then
    echo "ERROR: No recent backup found" >> $LOG_FILE
fi

echo "=== Weekly Check Completed: $(date) ===" >> $LOG_FILE
```

## メンテナンス中の注意事項

### サービス停止時の対応
- **事前通知**: 影響を受けるユーザーに1週間前通知
- **代替手段**: メンテナンス中のアクセス制限
- **緊急連絡**: 緊急時の連絡先明記

### ロールバック準備
- **バックアップ取得**: メンテナンス前フルバックアップ
- **切り戻し手順確認**: ロールバック手順の検証
- **監視強化**: メンテナンス中は監視間隔短縮

### 完了確認
- **機能テスト**: 全主要機能の動作確認
- **パフォーマンステスト**: レスポンスタイム測定
- **監視再開**: 通常監視に戻す

### メンテナンス記録
**記録項目:**
- 実施日時
- 担当者
- 実施内容
- 結果
- 所要時間
- 特記事項

**記録例:**
```markdown
## 2024-01-08 週次メンテナンス
- **担当者**: SREチーム
- **内容**: ログローテーション、パフォーマンスチェック
- **結果**: 成功
- **所要時間**: 00:30
- **特記事項**: ディスク使用率85% → ログクリーンアップ実施
```</content>
<parameter name="filePath">docs/11_運用保守(Operations)/14_定期メンテナンス(Regular-Maintenance).md