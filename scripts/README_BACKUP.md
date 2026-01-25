# バックアップスクリプト - インストールガイド

## 概要

Mirai Knowledge Systemsのバックアップスクリプト一式です。PostgreSQLデータベースとアプリケーションデータの自動バックアップ、リストア、検証機能を提供します。

---

## ファイル一覧

| ファイル名 | 行数 | 説明 |
|-----------|------|------|
| backup-postgresql.sh | 162行 | PostgreSQLデータベースバックアップ |
| backup-appdata.sh | 252行 | アプリケーションデータバックアップ |
| restore-postgresql.sh | 295行 | データベースリストア |
| verify-backups.sh | 328行 | バックアップ整合性検証 |
| mirai-knowledge-backup.cron | - | cron自動実行設定 |

**合計**: 1,037行のバックアップシステム

---

## クイックスタート

### 1. スクリプトのインストール

```bash
# ルート権限でスクリプトをコピー
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/backup-postgresql.sh /opt/scripts/
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/backup-appdata.sh /opt/scripts/
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/restore-postgresql.sh /opt/scripts/
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/verify-backups.sh /opt/scripts/

# 実行権限を付与
sudo chmod +x /opt/scripts/backup-postgresql.sh
sudo chmod +x /opt/scripts/backup-appdata.sh
sudo chmod +x /opt/scripts/restore-postgresql.sh
sudo chmod +x /opt/scripts/verify-backups.sh
```

### 2. ディレクトリの作成

```bash
# バックアップディレクトリ
sudo mkdir -p /var/backups/mirai-knowledge/postgresql
sudo mkdir -p /var/backups/mirai-knowledge/appdata
sudo chmod 700 /var/backups/mirai-knowledge
sudo chmod 700 /var/backups/mirai-knowledge/postgresql
sudo chmod 700 /var/backups/mirai-knowledge/appdata

# ログディレクトリ
sudo mkdir -p /var/log/mirai-knowledge
sudo chmod 755 /var/log/mirai-knowledge
```

### 3. cron設定のインストール

```bash
# cron設定ファイルをコピー
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/mirai-knowledge-backup.cron /etc/cron.d/mirai-knowledge-backup
sudo chmod 644 /etc/cron.d/mirai-knowledge-backup

# cronサービスの再起動
sudo systemctl restart cron
```

### 4. 初回テスト

```bash
# PostgreSQLバックアップのテスト
sudo /opt/scripts/backup-postgresql.sh

# アプリケーションデータバックアップのテスト
sudo /opt/scripts/backup-appdata.sh

# バックアップ検証のテスト
sudo /opt/scripts/verify-backups.sh

# バックアップファイルの確認
ls -lh /var/backups/mirai-knowledge/postgresql/
ls -lh /var/backups/mirai-knowledge/appdata/
```

---

## 使用方法

### PostgreSQLバックアップの実行

```bash
sudo /opt/scripts/backup-postgresql.sh
```

**出力先**: `/var/backups/mirai-knowledge/postgresql/db_YYYYMMDD_HHMMSS.sql.gz`

### アプリケーションデータバックアップの実行

```bash
sudo /opt/scripts/backup-appdata.sh
```

**出力先**: `/var/backups/mirai-knowledge/appdata/` (複数ファイル)

### リストアの実行

```bash
# 利用可能なバックアップの確認
sudo /opt/scripts/restore-postgresql.sh

# 特定のバックアップからリストア
sudo /opt/scripts/restore-postgresql.sh db_20260109_083000.sql.gz
```

### バックアップ検証の実行

```bash
sudo /opt/scripts/verify-backups.sh
```

---

## 自動実行スケジュール

cronにより以下のスケジュールで自動実行されます:

| 時刻 | 頻度 | タスク |
|------|------|--------|
| 2:00 AM | 毎日 | PostgreSQLバックアップ |
| 2:30 AM | 毎日 | アプリケーションデータバックアップ |
| 3:00 AM | 毎週日曜 | バックアップ検証 |
| 4:00 AM | 毎日 | ログローテーション |

---

## ログファイル

- **バックアップログ**: `/var/log/mirai-knowledge/backup.log`
- **検証ログ**: `/var/log/mirai-knowledge/backup-verification.log`
- **リストアログ**: `/var/log/mirai-knowledge/restore.log`

```bash
# ログの確認
tail -f /var/log/mirai-knowledge/backup.log
```

---

## セキュリティ設定

### 重要: パスワード管理

本番環境では、スクリプト内のパスワードをハードコードせず、`.pgpass`ファイルを使用してください。

```bash
# /root/.pgpass ファイルを作成
echo "localhost:5432:mirai_knowledge_db:postgres:YOUR_PASSWORD" > /root/.pgpass
chmod 600 /root/.pgpass

# スクリプトのDB_PASSWORD設定をコメントアウト
sudo nano /opt/scripts/backup-postgresql.sh
# DB_PASSWORD="..." の行をコメントアウト
```

### ファイル権限の確認

```bash
# 正しい権限が設定されているか確認
ls -l /opt/scripts/backup*.sh /opt/scripts/restore*.sh /opt/scripts/verify*.sh
ls -ld /var/backups/mirai-knowledge
```

期待される権限:
- スクリプト: `rwxr-xr-x` (755)
- バックアップディレクトリ: `rwx------` (700)
- バックアップファイル: `rw-------` (600)

---

## トラブルシューティング

### cronが動作しない

```bash
# cronサービスの状態確認
sudo systemctl status cron

# cron設定の文法チェック
cat /etc/cron.d/mirai-knowledge-backup

# 手動実行でエラー確認
sudo /opt/scripts/backup-postgresql.sh
```

### ディスク容量不足

```bash
# ディスク使用状況の確認
df -h /var/backups

# 古いバックアップの削除
sudo find /var/backups/mirai-knowledge -type f -mtime +30 -delete
```

### PostgreSQL接続エラー

```bash
# PostgreSQLサービスの状態確認
sudo systemctl status postgresql

# 接続テスト
psql -U postgres -h localhost -d mirai_knowledge_db -c '\q'

# パスワード認証の確認
cat ~/.pgpass
```

---

## 推奨事項

1. **定期的なリストアテスト**: 月次でテスト環境へのリストアを実施
2. **外部保管**: 重要なバックアップをクラウドストレージやNASにコピー
3. **監視**: Prometheus/Grafanaでバックアップ成功/失敗を監視
4. **暗号化**: 機密性の高いデータの場合、GPG暗号化を実装
5. **ドキュメント**: バックアップ/リストア手順書を常に最新化

---

## 詳細ドキュメント

完全なドキュメントは以下を参照してください:

- [バックアップシステム完全ガイド](/mnt/LinuxHDD/Mirai-Knowledge-Systems/docs/BACKUP_COMPLETE.md)

---

## サポート

問題が発生した場合:

1. ログファイルを確認: `/var/log/mirai-knowledge/backup.log`
2. スクリプトを手動実行してエラーメッセージを確認
3. 完全ドキュメントのトラブルシューティングセクションを参照

---

**作成日**: 2026-01-09
**バージョン**: 1.0.0
