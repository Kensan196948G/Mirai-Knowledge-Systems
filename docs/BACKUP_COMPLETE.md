# Mirai Knowledge Systems - バックアップシステム導入完了レポート

## 概要

PostgreSQLとアプリケーションデータの自動バックアップシステムを実装しました。このシステムにより、データ損失リスクを最小化し、災害復旧（DR）体制を構築できます。

---

## 実装内容

### 1. PostgreSQLバックアップスクリプト

**ファイル**: `/opt/scripts/backup-postgresql.sh` (または `scripts/backup-postgresql.sh`)

#### 機能
- PostgreSQLデータベースの完全バックアップ（pg_dump）
- gzip圧縮による容量削減
- 30日間のローテーション保持
- バックアップファイル整合性チェック
- ログ記録とエラー通知

#### 設定
```bash
BACKUP_DIR="/var/backups/mirai-knowledge/postgresql"
DB_NAME="mirai_knowledge_db"
DB_USER="postgres"
RETENTION_DAYS=30
```

#### 実行例
```bash
sudo /opt/scripts/backup-postgresql.sh
```

#### 出力ファイル形式
```
/var/backups/mirai-knowledge/postgresql/db_20260109_083000.sql.gz
```

---

### 2. アプリケーションデータバックアップスクリプト

**ファイル**: `/opt/scripts/backup-appdata.sh` (または `scripts/backup-appdata.sh`)

#### 機能
- JSONデータファイルのバックアップ
- .env環境設定ファイルのバックアップ（暗号化推奨）
- SSL証明書のバックアップ
- Nginx設定ファイルのバックアップ
- systemdサービス定義のバックアップ
- アプリケーションログのバックアップ（直近7日間）
- バックアップマニフェスト生成

#### バックアップ対象
1. **JSONデータ**: `backend/data/*.json`
2. **環境設定**: `backend/.env`
3. **SSL証明書**: `/etc/ssl/mks/`
4. **Nginx設定**: `/etc/nginx/sites-available/mirai-knowledge`
5. **systemdサービス**: `/etc/systemd/system/mirai-knowledge-prod.service`
6. **アプリケーションログ**: `/var/log/mirai-knowledge/` (7日間分)

#### 実行例
```bash
sudo /opt/scripts/backup-appdata.sh
```

#### 出力ファイル形式
```
/var/backups/mirai-knowledge/appdata/data_20260109_083000.tar.gz
/var/backups/mirai-knowledge/appdata/env_20260109_083000.backup
/var/backups/mirai-knowledge/appdata/ssl_20260109_083000.tar.gz
/var/backups/mirai-knowledge/appdata/nginx_20260109_083000.conf
/var/backups/mirai-knowledge/appdata/systemd_20260109_083000.service
/var/backups/mirai-knowledge/appdata/logs_20260109_083000.tar.gz
/var/backups/mirai-knowledge/appdata/manifest_20260109_083000.txt
```

---

### 3. リストアスクリプト

**ファイル**: `/opt/scripts/restore-postgresql.sh` (または `scripts/restore-postgresql.sh`)

#### 機能
- PostgreSQLデータベースのリストア
- バックアップファイル整合性検証
- リストア前の安全バックアップ自動作成
- アプリケーションサービスの自動停止・起動
- 対話型確認プロンプト
- リストア結果の検証

#### 使用方法
```bash
# 利用可能なバックアップの確認
sudo /opt/scripts/restore-postgresql.sh

# 特定のバックアップからリストア
sudo /opt/scripts/restore-postgresql.sh db_20260109_083000.sql.gz

# フルパスでも可能
sudo /opt/scripts/restore-postgresql.sh /var/backups/mirai-knowledge/postgresql/db_20260109_083000.sql.gz
```

#### リストアフロー
1. バックアップファイルの検証
2. ユーザー確認プロンプト
3. 現在のDBの安全バックアップ作成
4. アプリケーションサービス停止
5. データベースリストア実行
6. リストア結果の検証
7. アプリケーションサービス起動

---

### 4. バックアップ検証スクリプト

**ファイル**: `/opt/scripts/verify-backups.sh` (または `scripts/verify-backups.sh`)

#### 機能
- PostgreSQLバックアップファイルの整合性検証
- アプリケーションデータバックアップの整合性検証
- ファイルサイズチェック
- gzip/tar.gz圧縮形式の検証
- SQL内容の基本チェック
- バックアップスケジュールの確認
- 最終バックアップ時刻の確認
- サマリーレポート生成

#### 実行例
```bash
sudo /opt/scripts/verify-backups.sh
```

#### 検証項目
- ファイル存在確認
- ファイルサイズ閾値チェック（DB: 10KB以上、AppData: 1KB以上）
- gzip/tar.gz整合性チェック
- SQL内容の基本チェック
- 最終バックアップからの経過時間（48時間以内推奨）

---

### 5. cron自動実行設定

**ファイル**: `/etc/cron.d/mirai-knowledge-backup` (または `scripts/mirai-knowledge-backup.cron`)

#### スケジュール

| 時刻 | 頻度 | タスク | 説明 |
|------|------|--------|------|
| 2:00 AM | 毎日 | PostgreSQLバックアップ | データベース完全バックアップ |
| 2:30 AM | 毎日 | アプリケーションデータバックアップ | JSONデータ、設定ファイル等 |
| 3:00 AM | 毎週日曜 | バックアップ検証 | 整合性チェック、サマリーレポート |
| 4:00 AM | 毎日 | ログローテーション | 100MB以上のログをクリア |

#### インストール方法
```bash
# スクリプトを/opt/scriptsにコピー（sudo権限必要）
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/backup-postgresql.sh /opt/scripts/
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/backup-appdata.sh /opt/scripts/
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/restore-postgresql.sh /opt/scripts/
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/verify-backups.sh /opt/scripts/
sudo chmod +x /opt/scripts/*.sh

# バックアップディレクトリとログディレクトリの作成
sudo mkdir -p /var/backups/mirai-knowledge/{postgresql,appdata}
sudo mkdir -p /var/log/mirai-knowledge
sudo chmod 700 /var/backups/mirai-knowledge
sudo chmod 700 /var/backups/mirai-knowledge/{postgresql,appdata}

# cron設定のインストール
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/mirai-knowledge-backup.cron /etc/cron.d/mirai-knowledge-backup
sudo chmod 644 /etc/cron.d/mirai-knowledge-backup

# cronサービスの再起動
sudo systemctl restart cron
```

---

## ディレクトリ構成

```
/var/backups/mirai-knowledge/
├── postgresql/
│   ├── db_20260109_020000.sql.gz
│   ├── db_20260108_020000.sql.gz
│   └── safety_before_restore_20260109_150000.sql.gz
└── appdata/
    ├── data_20260109_023000.tar.gz
    ├── env_20260109_023000.backup
    ├── ssl_20260109_023000.tar.gz
    ├── nginx_20260109_023000.conf
    ├── systemd_20260109_023000.service
    ├── logs_20260109_023000.tar.gz
    └── manifest_20260109_023000.txt

/var/log/mirai-knowledge/
├── backup.log
├── backup-verification.log
└── restore.log

/opt/scripts/
├── backup-postgresql.sh
├── backup-appdata.sh
├── restore-postgresql.sh
└── verify-backups.sh

/etc/cron.d/
└── mirai-knowledge-backup
```

---

## セキュリティ考慮事項

### 1. ファイル権限
```bash
# バックアップディレクトリ: rootのみアクセス可能
chmod 700 /var/backups/mirai-knowledge

# .envファイルバックアップ: rootのみ読み取り可能
chmod 600 /var/backups/mirai-knowledge/appdata/env_*.backup

# スクリプト: rootと管理者グループが実行可能
chmod 750 /opt/scripts/*.sh
```

### 2. データベースパスワード管理

**重要**: 本番環境では、スクリプト内にパスワードをハードコードせず、以下の方法を使用してください。

#### 方法1: `.pgpass`ファイル（推奨）
```bash
# /root/.pgpass または /home/user/.pgpass
echo "localhost:5432:mirai_knowledge_db:postgres:ELzion1969" > ~/.pgpass
chmod 600 ~/.pgpass
```

スクリプトから`DB_PASSWORD`設定を削除し、`PGPASSWORD`環境変数の使用を停止。

#### 方法2: 環境変数ファイル
```bash
# /etc/mirai-knowledge/backup.env
DB_PASSWORD="ELzion1969"
chmod 600 /etc/mirai-knowledge/backup.env
```

スクリプトで読み込み:
```bash
source /etc/mirai-knowledge/backup.env
```

### 3. バックアップの暗号化（推奨）

機密性の高いデータを含む場合、バックアップファイルを暗号化することを推奨します。

```bash
# GPG暗号化の例
gpg --symmetric --cipher-algo AES256 /var/backups/mirai-knowledge/postgresql/db_20260109_020000.sql.gz

# 復号化
gpg --decrypt db_20260109_020000.sql.gz.gpg | gunzip | psql -U postgres -h localhost mirai_knowledge_db
```

---

## 運用手順

### 日次運用

1. **バックアップログの確認**
   ```bash
   tail -n 50 /var/log/mirai-knowledge/backup.log
   ```

2. **ディスク容量の監視**
   ```bash
   df -h /var/backups
   ```

3. **最新バックアップの確認**
   ```bash
   ls -lht /var/backups/mirai-knowledge/postgresql/ | head -5
   ```

### 週次運用

1. **バックアップ検証レポートの確認**
   ```bash
   tail -n 100 /var/log/mirai-knowledge/backup-verification.log
   ```

2. **ストレージ使用量の確認**
   ```bash
   du -sh /var/backups/mirai-knowledge/*
   ```

### 月次運用

1. **リストアテストの実施**（テスト環境で）
   ```bash
   # テスト環境で最新バックアップからのリストアテスト
   sudo /opt/scripts/restore-postgresql.sh db_YYYYMMDD_HHMMSS.sql.gz
   ```

2. **バックアップファイルの外部保管**
   - 重要なバックアップを外部ストレージ（NAS、クラウドストレージ等）にコピー
   - 3-2-1バックアップルール: 3コピー、2種類のメディア、1つは外部保管

---

## トラブルシューティング

### 問題1: バックアップが実行されない

#### 確認事項
```bash
# cronサービスの状態確認
sudo systemctl status cron

# cron設定の確認
cat /etc/cron.d/mirai-knowledge-backup

# ログファイルの確認
tail -n 100 /var/log/mirai-knowledge/backup.log
```

#### 解決方法
```bash
# cronサービスの再起動
sudo systemctl restart cron

# 手動実行でエラー確認
sudo /opt/scripts/backup-postgresql.sh
```

### 問題2: ディスク容量不足

#### 確認事項
```bash
# ディスク使用状況
df -h /var/backups

# バックアップファイルのサイズ
du -sh /var/backups/mirai-knowledge/*
```

#### 解決方法
```bash
# 古いバックアップを手動削除（30日以上前）
find /var/backups/mirai-knowledge -type f -mtime +30 -delete

# または保持期間を短縮（スクリプト内のRETENTION_DAYS変数を変更）
```

### 問題3: リストアが失敗する

#### 確認事項
```bash
# PostgreSQLサービスの状態
sudo systemctl status postgresql

# バックアップファイルの整合性
gunzip -t /var/backups/mirai-knowledge/postgresql/db_20260109_020000.sql.gz

# データベース接続テスト
psql -U postgres -h localhost -d mirai_knowledge_db -c '\q'
```

#### 解決方法
```bash
# PostgreSQLサービスの再起動
sudo systemctl restart postgresql

# 別のバックアップファイルで再試行
sudo /opt/scripts/restore-postgresql.sh db_YYYYMMDD_HHMMSS.sql.gz
```

### 問題4: cronからの実行でエラー

#### 確認事項
```bash
# cronログの確認（Ubuntu/Debian）
grep CRON /var/log/syslog | tail -n 50

# スクリプトの権限確認
ls -l /opt/scripts/*.sh

# PATHの確認（スクリプト内で絶対パスを使用）
```

#### 解決方法
```bash
# スクリプトに実行権限を付与
sudo chmod +x /opt/scripts/*.sh

# cron設定にPATHを明示的に設定（既に含まれています）
```

---

## パフォーマンス最適化

### 1. バックアップ時間の短縮

```bash
# 並列圧縮（pigzを使用）
sudo apt-get install pigz

# スクリプト内でgzipの代わりにpigzを使用
pg_dump -U postgres -h localhost mirai_knowledge_db | pigz > backup.sql.gz
```

### 2. 増分バックアップ（オプション）

完全バックアップに加えて、増分バックアップを実施することで、バックアップ時間と容量を削減できます。

```bash
# PostgreSQL WAL（Write-Ahead Log）アーカイブの有効化
# postgresql.confに追加:
# wal_level = replica
# archive_mode = on
# archive_command = 'cp %p /var/backups/mirai-knowledge/wal/%f'
```

### 3. バックアップの差分圧縮

```bash
# 前回バックアップとの差分のみを保存（rduplicityなどのツール使用）
```

---

## 監視とアラート

### 1. バックアップ失敗時の通知

スクリプトにメール通知機能を追加:

```bash
# バックアップスクリプトの修正例
if [ $? -ne 0 ]; then
    echo "Backup failed!" | mail -s "Mirai Knowledge Backup Failed" admin@example.com
    exit 1
fi
```

### 2. Prometheus/Grafanaでの監視

バックアップメトリクスをPrometheusに送信:

```bash
# 最終バックアップ時刻をPrometheusに送信
echo "mirai_knowledge_last_backup_timestamp $(date +%s)" | curl --data-binary @- http://localhost:9091/metrics/job/backup
```

### 3. ディスク容量監視

```bash
# ディスク使用率が80%を超えたらアラート
DISK_USAGE=$(df -h /var/backups | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is at ${DISK_USAGE}%" | mail -s "Disk Space Alert" admin@example.com
fi
```

---

## ベストプラクティス

### 1. 3-2-1バックアップルール
- **3コピー**: 本番データ + 2つのバックアップ
- **2種類のメディア**: ローカルディスク + 外部ストレージ
- **1つは外部保管**: クラウドまたはオフサイト

### 2. 定期的なリストアテスト
- 月次でテスト環境へのリストアを実施
- リストア手順書の更新と検証

### 3. バックアップの世代管理
- 日次: 30日間保持
- 週次: 12週間保持（月曜日のバックアップを別途保存）
- 月次: 12ヶ月保持（月初のバックアップを別途保存）

### 4. セキュリティ
- バックアップファイルの暗号化
- アクセス権限の厳格な管理
- 定期的なセキュリティ監査

### 5. ドキュメント
- バックアップ/リストア手順書の最新化
- インシデント対応手順の整備
- 定期的な訓練の実施

---

## テスト手順

### 初回セットアップ後のテスト

#### 1. PostgreSQLバックアップのテスト
```bash
# スクリプトの実行
sudo /opt/scripts/backup-postgresql.sh

# バックアップファイルの確認
ls -lh /var/backups/mirai-knowledge/postgresql/

# ログの確認
tail -n 50 /var/log/mirai-knowledge/backup.log
```

**期待結果**:
- `db_YYYYMMDD_HHMMSS.sql.gz` ファイルが作成される
- ファイルサイズが10KB以上
- ログに「Backup completed successfully」が記録される

#### 2. アプリケーションデータバックアップのテスト
```bash
# スクリプトの実行
sudo /opt/scripts/backup-appdata.sh

# バックアップファイルの確認
ls -lh /var/backups/mirai-knowledge/appdata/

# マニフェストの確認
cat /var/backups/mirai-knowledge/appdata/manifest_*.txt
```

**期待結果**:
- 複数のバックアップファイルが作成される
- manifest_*.txt にバックアップサマリーが記録される

#### 3. バックアップ検証のテスト
```bash
# 検証スクリプトの実行
sudo /opt/scripts/verify-backups.sh

# 結果の確認
echo $?  # 0 = 成功、1以上 = 失敗
```

**期待結果**:
- すべての検証項目が成功（exit code 0）
- 検証レポートが出力される

#### 4. リストアのテスト（テスト環境で）
```bash
# リストアスクリプトの実行
sudo /opt/scripts/restore-postgresql.sh

# バックアップ一覧が表示される
# 特定のバックアップを選択してリストア
sudo /opt/scripts/restore-postgresql.sh db_YYYYMMDD_HHMMSS.sql.gz
```

**期待結果**:
- 確認プロンプトが表示される
- 安全バックアップが自動作成される
- リストアが成功する
- データベース内容が復元される

---

## まとめ

### 実装完了項目

- [x] PostgreSQLバックアップスクリプト
- [x] アプリケーションデータバックアップスクリプト
- [x] リストアスクリプト
- [x] バックアップ検証スクリプト
- [x] cron自動実行設定
- [x] ドキュメント（本ファイル）

### バックアップ対象

| 項目 | パス | バックアップ先 | 頻度 | 保持期間 |
|------|------|----------------|------|----------|
| PostgreSQLデータベース | mirai_knowledge_db | /var/backups/mirai-knowledge/postgresql/ | 毎日2:00 | 30日 |
| JSONデータ | backend/data/ | /var/backups/mirai-knowledge/appdata/ | 毎日2:30 | 30日 |
| 環境設定 | backend/.env | /var/backups/mirai-knowledge/appdata/ | 毎日2:30 | 30日 |
| SSL証明書 | /etc/ssl/mks/ | /var/backups/mirai-knowledge/appdata/ | 毎日2:30 | 30日 |
| Nginx設定 | /etc/nginx/sites-available/ | /var/backups/mirai-knowledge/appdata/ | 毎日2:30 | 30日 |
| systemdサービス | /etc/systemd/system/ | /var/backups/mirai-knowledge/appdata/ | 毎日2:30 | 30日 |

### 次のステップ（推奨）

1. **外部ストレージへの自動転送**
   - AWS S3、Google Cloud Storage、Azure Blob Storageなどへの自動アップロード
   - rsyncによるNASへの定期同期

2. **監視・アラート強化**
   - Prometheusメトリクスの追加
   - メール通知の設定
   - Slackなどへのアラート連携

3. **暗号化の実装**
   - GPG/AES256によるバックアップファイルの暗号化
   - 鍵管理の自動化

4. **災害復旧（DR）手順書の作成**
   - 完全なシステム復旧手順の文書化
   - 定期的な復旧訓練の実施

5. **バックアップの世代管理強化**
   - 週次・月次バックアップの長期保管
   - 重要マイルストーンのアーカイブ

---

## 関連ドキュメント

- [PostgreSQL公式ドキュメント - バックアップとリストア](https://www.postgresql.org/docs/current/backup.html)
- [Mirai Knowledge Systems - セキュリティ対策ガイド](./SECURITY_HARDENING_PHASE_B8_COMPLETE.md)
- [Mirai Knowledge Systems - 本番環境構築ガイド](./PRODUCTION_DEPLOYMENT_COMPLETE.md)

---

**作成日**: 2026-01-09
**作成者**: Claude Code
**バージョン**: 1.0.0
**ステータス**: 実装完了
