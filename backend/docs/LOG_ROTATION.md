# ログローテーション設定ガイド

## 概要

Mirai Knowledge Systemのログファイルは時間とともに肥大化するため、**logrotate**を使用して定期的にローテーション（アーカイブ・削除）を行います。

## セットアップ状況

✅ ログディレクトリ作成済み（`backend/logs/`）
✅ ログローテーション設定ファイル作成済み（`backend/logrotate.d/mirai-knowledge-system`）
✅ 自動セットアップスクリプト作成済み（`backend/scripts/setup-logrotate.sh`）

## クイックスタート

### 自動セットアップ（推奨）

```bash
cd /path/to/Mirai-Knowledge-Systems
sudo ./backend/scripts/setup-logrotate.sh
```

このスクリプトは以下を自動的に実行します：
1. ログディレクトリの作成
2. logrotateのインストール確認
3. 設定ファイルのコピー（`/etc/logrotate.d/`へ）
4. 設定の検証

### 手動セットアップ

```bash
# 1. logrotateがインストールされているか確認
which logrotate

# インストールされていない場合
sudo apt-get install logrotate  # Ubuntu/Debian
# または
sudo yum install logrotate       # CentOS/RHEL

# 2. 設定ファイルをコピー
sudo cp backend/logrotate.d/mirai-knowledge-system /etc/logrotate.d/

# 3. パーミッション設定
sudo chmod 644 /etc/logrotate.d/mirai-knowledge-system

# 4. 設定の検証
sudo logrotate -d /etc/logrotate.d/mirai-knowledge-system
```

## ローテーション設定

### 通常ログ（`*.log`）

| 設定項目 | 値 |
|----------|-----|
| ローテーション頻度 | 日次（daily） |
| 保持期間 | 7日間 |
| 圧縮 | 有効（gzip） |
| 圧縮遅延 | 1日（最新ログは非圧縮） |
| 日付形式 | `-YYYYMMDD` |

### アクセスログ（`access.log`）

| 設定項目 | 値 |
|----------|-----|
| ローテーション頻度 | 日次または100MB超過時 |
| 保持期間 | 14日間 |
| 圧縮 | 有効 |
| サイズ制限 | 100MB |

### エラーログ（`error.log`）

| 設定項目 | 値 |
|----------|-----|
| ローテーション頻度 | 日次 |
| 保持期間 | **30日間**（デバッグ用に長期保持） |
| 圧縮 | 有効 |

## 使用方法

### ローテーションの手動実行

テスト（実際には実行しない）:
```bash
sudo logrotate -d /etc/logrotate.d/mirai-knowledge-system
```

強制実行:
```bash
sudo logrotate -f /etc/logrotate.d/mirai-knowledge-system
```

### ログファイルの確認

```bash
# ログディレクトリの内容を表示
ls -lh /path/to/Mirai-Knowledge-Systems/backend/logs/

# ローテーション済みログの確認
ls -lh /path/to/Mirai-Knowledge-Systems/backend/logs/*.gz
```

**出力例**:
```
-rw-r--r-- 1 user user  1.2M Jan  1 10:00 app.log
-rw-r--r-- 1 user user  850K Dec 31 23:59 app.log-20231231.gz
-rw-r--r-- 1 user user  2.5M Jan  1 10:00 access.log
-rw-r--r-- 1 user user  120K Jan  1 10:00 error.log
```

### 自動実行の確認

logrotateは通常、cronによって日次で自動実行されます：

```bash
# cron設定を確認
cat /etc/cron.daily/logrotate

# logrotateの状態ファイルを確認
cat /var/lib/logrotate/status
```

## ログファイル構造

```
backend/logs/
├── app.log                    # 現在のアプリケーションログ
├── app.log-20240101.gz        # 昨日のログ（圧縮済み）
├── app.log-20231231.gz        # 2日前のログ
├── access.log                 # 現在のアクセスログ
├── access.log-20240101.gz     # アーカイブ
├── error.log                  # 現在のエラーログ
└── error.log-20240101.gz      # アーカイブ
```

## トラブルシューティング

### ローテーションが実行されない

**原因**: cron設定の問題、またはlogrotate設定エラー

**確認方法**:
```bash
# logrotateのステータス確認
sudo systemctl status cron    # Ubuntu/Debian
sudo systemctl status crond   # CentOS/RHEL

# 設定エラーをチェック
sudo logrotate -d /etc/logrotate.d/mirai-knowledge-system
```

### 圧縮されたログが見つからない

**原因**: ログファイルが存在しない、またはローテーション条件を満たしていない

**確認方法**:
```bash
# ログディレクトリを確認
ls -la /path/to/Mirai-Knowledge-Systems/backend/logs/

# 強制ローテーションを実行
sudo logrotate -f /etc/logrotate.d/mirai-knowledge-system
```

### アプリケーションがローテーション後もlogファイルに書き込まない

**原因**: アプリケーションがログファイルハンドルを再オープンしていない

**解決策**:
```bash
# Gunicornプロセスを再起動
sudo systemctl reload mirai-knowledge-production.service

# または、Gunicornに直接シグナル送信
sudo kill -USR1 $(cat /var/run/gunicorn-mirai.pid)
```

### ディスク容量不足

**原因**: ログが蓄積しすぎている

**解決策**:
```bash
# 古いログファイルを手動削除
find /path/to/Mirai-Knowledge-Systems/backend/logs/ -name "*.gz" -mtime +30 -delete

# またはディスク使用量を確認
du -sh /path/to/Mirai-Knowledge-Systems/backend/logs/
```

## ベストプラクティス

1. **定期監視**: 週次でログディレクトリのサイズを確認
2. **保持期間調整**: 本番環境の要件に応じて保持期間を調整
3. **アラート設定**: ディスク使用率が80%を超えたら通知
4. **ログ集約**: 大規模システムではELKスタック等の導入を検討

## 高度な設定

### カスタムローテーション条件

サイズベースのローテーション:
```bash
# 50MBを超えたらローテーション
size 50M
```

時間ベースのローテーション:
```bash
# 毎週日曜日
weekly

# 毎月1日
monthly
```

### 圧縮方法の変更

```bash
# bzip2で圧縮（より高圧縮）
compresscmd /bin/bzip2
compressoptions -9
compressext .bz2
uncompresscmd /bin/bunzip2
```

### ローテーション後のカスタムスクリプト

```bash
postrotate
    # S3にアップロード
    /usr/local/bin/upload-to-s3.sh $1 2>/dev/null || true

    # メール通知
    echo "Log rotated: $1" | mail -s "Log Rotation" admin@example.com
endscript
```

## 参考リンク

- [logrotate公式マニュアル](https://linux.die.net/man/8/logrotate)
- [Gunicornログ設定](https://docs.gunicorn.org/en/stable/settings.html#logging)
- [systemdジャーナルログ](https://www.freedesktop.org/software/systemd/man/journalctl.html)
