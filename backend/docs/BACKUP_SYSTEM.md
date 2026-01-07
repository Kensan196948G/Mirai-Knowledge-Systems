# 自動バックアップシステムガイド

## 概要

Mirai Knowledge Systemは、データ損失を防ぐために**自動バックアップシステム**を提供しています。PostgreSQLデータベースとJSONファイルの両方を定期的にバックアップします。

## セットアップ状況

✅ バックアップスクリプト作成済み（`backend/scripts/backup.sh`）
✅ Cron設定スクリプト作成済み（`backend/scripts/setup-backup-cron.sh`）
✅ バックアップディレクトリ作成済み（`backend/backups/`）

## クイックスタート

### 1. 自動バックアップ設定（推奨）

```bash
# Cronジョブを自動設定（要root権限）
cd /path/to/Mirai-Knowledge-Systems
sudo ./backend/scripts/setup-backup-cron.sh
```

これにより、**毎日午前2時**に自動バックアップが実行されます。

### 2. 手動バックアップ実行

```bash
# 完全バックアップ（DB + JSON）
./backend/scripts/backup.sh

# データベースのみ
./backend/scripts/backup.sh --db-only

# JSONファイルのみ
./backend/scripts/backup.sh --json-only
```

## バックアップ種類

### 完全バックアップ（デフォルト）

| 項目 | 内容 |
|------|------|
| 含まれるもの | PostgreSQL + JSONファイル |
| 保存場所 | `backend/backups/full/` |
| 保持期間 | 14日間 |
| ファイル名形式 | `mirai_full_YYYYMMDD_HHMMSS.tar.gz` |
| 実行コマンド | `./backend/scripts/backup.sh` |

### データベースバックアップ

| 項目 | 内容 |
|------|------|
| 含まれるもの | PostgreSQLデータベース（全スキーマ） |
| 形式 | pg_dump カスタム形式（圧縮済み） |
| 保存場所 | `backend/backups/database/` |
| 保持期間 | 30日間 |
| ファイル名形式 | `mirai_db_YYYYMMDD_HHMMSS.sql.gz` |
| 実行コマンド | `./backend/scripts/backup.sh --db-only` |

### JSONファイルバックアップ

| 項目 | 内容 |
|------|------|
| 含まれるもの | `backend/data/` ディレクトリ全体 |
| 形式 | tar.gz圧縮アーカイブ |
| 保存場所 | `backend/backups/json/` |
| 保持期間 | 7日間 |
| ファイル名形式 | `mirai_json_YYYYMMDD_HHMMSS.tar.gz` |
| 実行コマンド | `./backend/scripts/backup.sh --json-only` |

## バックアップスケジュール

デフォルトのCron設定:

```bash
# 毎日午前2時: 完全バックアップ
0 2 * * * root /path/to/backup.sh >> /var/log/mirai-backup.log 2>&1
```

### カスタムスケジュール例

```bash
# 6時間ごとにデータベースバックアップ
0 */6 * * * root /path/to/backup.sh --db-only >> /var/log/mirai-backup.log 2>&1

# 12時間ごとに完全バックアップ
0 */12 * * * root /path/to/backup.sh >> /var/log/mirai-backup.log 2>&1

# 毎週日曜日0時に完全バックアップ
0 0 * * 0 root /path/to/backup.sh >> /var/log/mirai-backup.log 2>&1
```

## リストア（復元）手順

### PostgreSQLデータベースのリストア

```bash
# 1. バックアップファイル確認
ls -lh backend/backups/database/

# 2. バックアップファイルを解凍
gunzip backend/backups/database/mirai_db_YYYYMMDD_HHMMSS.sql.gz

# 3. データベースをリストア
# 注意: 既存のデータベースを削除して再作成
dropdb mirai_knowledge_db
createdb mirai_knowledge_db
pg_restore -d mirai_knowledge_db backend/backups/database/mirai_db_YYYYMMDD_HHMMSS.sql

# または、.envファイルの設定を使用
source backend/.env
pg_restore -d $DATABASE_URL backend/backups/database/mirai_db_YYYYMMDD_HHMMSS.sql
```

### JSONファイルのリストア

```bash
# 1. 現在のデータディレクトリをバックアップ（念のため）
mv backend/data backend/data.old

# 2. バックアップから復元
tar -xzf backend/backups/json/mirai_json_YYYYMMDD_HHMMSS.tar.gz -C backend/

# 3. 権限を確認
chown -R $USER:$USER backend/data
chmod -R 755 backend/data
```

### 完全リストア

```bash
# 1. 完全バックアップを展開
mkdir -p /tmp/mirai_restore
tar -xzf backend/backups/full/mirai_full_YYYYMMDD_HHMMSS.tar.gz -C /tmp/mirai_restore

# 2. データベースをリストア
gunzip /tmp/mirai_restore/database/mirai_db_*.sql.gz
pg_restore -d mirai_knowledge_db /tmp/mirai_restore/database/mirai_db_*.sql

# 3. JSONファイルをリストア
tar -xzf /tmp/mirai_restore/json/mirai_json_*.tar.gz -C backend/
```

## バックアップの確認

### 最新バックアップ情報

```bash
cat backend/backups/LATEST_BACKUP.txt
```

### バックアップ履歴

```bash
cat backend/backups/backup_metadata.log
```

### バックアップファイル一覧

```bash
# 最新5個の完全バックアップ
ls -lht backend/backups/full/ | head -6

# 最新10個のデータベースバックアップ
ls -lht backend/backups/database/ | head -11

# すべてのバックアップのサイズ
du -sh backend/backups/*
```

### バックアップログ

```bash
# 最新のバックアップログ
tail -50 /var/log/mirai-backup.log

# リアルタイムログ監視
tail -f /var/log/mirai-backup.log
```

## トラブルシューティング

### エラー: "pg_dump: command not found"

**原因**: PostgreSQLクライアントツールがインストールされていない

**解決策**:
```bash
sudo apt-get install postgresql-client  # Ubuntu/Debian
# または
sudo yum install postgresql              # CentOS/RHEL
```

### エラー: "connection to server failed"

**原因**: PostgreSQLサーバーが起動していない、または接続情報が間違っている

**解決策**:
```bash
# PostgreSQLサービス起動
sudo systemctl start postgresql
sudo systemctl status postgresql

# 接続情報確認
cat backend/.env | grep DATABASE_URL
```

### バックアップファイルが大きすぎる

**原因**: データベースやJSONファイルのサイズが増大

**解決策**:
1. 古いログやアーカイブデータを削除
2. データベースの`VACUUM FULL`を実行
3. 圧縮率を向上（既にgzipを使用）
4. 増分バックアップの検討（高度）

```bash
# データベースのサイズ確認
psql -d mirai_knowledge_db -c "SELECT pg_size_pretty(pg_database_size('mirai_knowledge_db'));"

# VACUUMを実行してサイズ削減
psql -d mirai_knowledge_db -c "VACUUM FULL;"
```

### ディスク容量不足

**原因**: バックアップが蓄積してディスクが満杯

**解決策**:
```bash
# バックアップディレクトリのサイズ確認
du -sh backend/backups/

# 古いバックアップを手動削除
find backend/backups/ -name "*.tar.gz" -mtime +30 -delete
find backend/backups/ -name "*.sql.gz" -mtime +60 -delete

# 保持期間を短縮（backup.shを編集）
```

## ベストプラクティス

1. **定期的なリストアテスト**: 月次でバックアップからのリストアをテスト環境で実施
2. **オフサイトバックアップ**: 重要なデータは外部ストレージ（S3、クラウドストレージ）にコピー
3. **バックアップ監視**: バックアップの成功/失敗をアラート（メール、Slack等）
4. **セキュリティ**: バックアップファイルは暗号化して保存（GPG等）
5. **ドキュメント化**: リストア手順を明文化し、チームで共有

## 高度な設定

### S3へのバックアップアップロード

```bash
# AWS CLIをインストール
sudo apt-get install awscli

# backup.sh の postrotate セクションに追加
aws s3 cp $DB_BACKUP_GZ s3://your-bucket/mirai-backups/database/
aws s3 cp $FULL_BACKUP_FILE s3://your-bucket/mirai-backups/full/
```

### GPG暗号化

```bash
# GPGキー生成
gpg --gen-key

# バックアップを暗号化
gpg --encrypt --recipient your-email@example.com mirai_full_*.tar.gz

# 復号化
gpg --decrypt mirai_full_*.tar.gz.gpg > mirai_full_*.tar.gz
```

### メール通知

```bash
# backup.sh の最後に追加
if [ $? -eq 0 ]; then
    echo "Backup completed successfully at $(date)" | mail -s "Mirai Backup Success" admin@example.com
else
    echo "Backup failed at $(date)" | mail -s "Mirai Backup FAILED" admin@example.com
fi
```

## 参考リンク

- [PostgreSQL Backup & Restore](https://www.postgresql.org/docs/current/backup.html)
- [Cron ジョブガイド](https://crontab.guru/)
- [tar コマンドリファレンス](https://www.gnu.org/software/tar/manual/)
