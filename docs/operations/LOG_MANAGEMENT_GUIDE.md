# ログ管理ガイド

## 📋 概要

Mirai Knowledge Systemのログ管理とログローテーション設定に関するガイドです。

## 📁 ログファイルの場所

### 開発環境

```
/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/
├── app_restart.log      # アプリケーション再起動ログ
├── backup_db.log        # データベースバックアップログ
└── backup_json.log      # JSONバックアップログ
```

### 本番環境（gunicorn使用時）

```
/var/log/mirai-knowledge/
├── access.log           # アクセスログ（gunicorn）
├── error.log            # エラーログ（gunicorn）
└── app.log              # アプリケーションログ
```

## ⚙️ ログローテーション設定

### 設定状況

- ✅ logrotate設定ファイル作成済み: `/etc/logrotate.d/mirai-knowledge-system`
- ✅ cronジョブ設定済み: `/etc/cron.daily/logrotate`（毎日実行）
- ✅ セットアップスクリプト準備済み: `backend/scripts/setup-logrotate.sh`

### ローテーション設定詳細

| ログ種別 | 保持期間 | ローテーション | サイズ制限 | 圧縮 |
|---------|---------|-------------|----------|------|
| 通常ログ (*.log) | 7日間 | 日次 | なし | ○ |
| アクセスログ | 14日間 | 日次または100MB超過時 | 100MB | ○ |
| エラーログ | 30日間 | 日次 | なし | ○ |

### ローテーション機能

- **圧縮**: gzip圧縮（遅延圧縮: 最新ローテーション分は非圧縮）
- **日付形式**: `-YYYYMMDD` (例: `access.log-20260108.gz`)
- **Graceful reload**: ローテーション後にgunicorn/systemdへUSR1シグナル送信
- **エラー処理**: ファイル不在時もエラーにならない（missingok）

## 🚀 セットアップ手順

### 本番環境ログディレクトリ作成

```bash
# ログディレクトリ作成
sudo mkdir -p /var/log/mirai-knowledge

# 権限設定
sudo chown kensan:kensan /var/log/mirai-knowledge
sudo chmod 755 /var/log/mirai-knowledge
```

### logrotate設定の検証

```bash
# ドライラン（実際にはローテーションしない）
sudo logrotate -d /etc/logrotate.d/mirai-knowledge-system

# 強制実行（テスト用）
sudo logrotate -f /etc/logrotate.d/mirai-knowledge-system
```

### 既存設定の更新（必要な場合）

```bash
# セットアップスクリプトを実行
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems
sudo backend/scripts/setup-logrotate.sh
```

## 📊 ログ監視

### リアルタイムログ確認

```bash
# 開発環境
tail -f backend/logs/app_restart.log

# 本番環境（systemd経由）
sudo journalctl -u mirai-knowledge-prod -f

# 本番環境（gunicornログ）
tail -f /var/log/mirai-knowledge/access.log
tail -f /var/log/mirai-knowledge/error.log
```

### ログサイズ確認

```bash
# 開発環境
du -sh backend/logs/
ls -lh backend/logs/

# 本番環境
du -sh /var/log/mirai-knowledge/
ls -lh /var/log/mirai-knowledge/
```

### 古いログの確認

```bash
# 圧縮済みログを確認
ls -lh /var/log/mirai-knowledge/*.gz

# 圧縮ログの内容を表示
zcat /var/log/mirai-knowledge/access.log-20260108.gz | less
```

## 🔍 トラブルシューティング

### ログローテーションが動作しない

```bash
# logrotateの状態ファイル確認
cat /var/lib/logrotate/status | grep mirai

# 手動で実行してエラー確認
sudo logrotate -v /etc/logrotate.d/mirai-knowledge-system
```

### ディスク容量不足

```bash
# ディスク使用量確認
df -h

# 古いログを手動削除
sudo find /var/log/mirai-knowledge/ -name "*.gz" -mtime +30 -delete
```

### ログファイルの権限エラー

```bash
# 権限確認
ls -la /var/log/mirai-knowledge/

# 権限修正
sudo chown -R kensan:kensan /var/log/mirai-knowledge/
sudo chmod -R 644 /var/log/mirai-knowledge/*.log
```

## 📝 ログレベル設定

### gunicorn ログレベル変更

`backend/gunicorn.conf.py` を編集：

```python
# ログレベル: debug, info, warning, error, critical
loglevel = os.getenv("MKS_LOG_LEVEL", "info")
```

環境変数で変更：

```bash
# .envファイルに追加
MKS_LOG_LEVEL=debug

# またはsystemdサービスファイルに追加
Environment="MKS_LOG_LEVEL=warning"
```

### アプリケーションログレベル

`backend/.env` で設定：

```bash
MKS_LOG_LEVEL=INFO
MKS_DEBUG=false
```

## 🛡️ セキュリティ考慮事項

### 機密情報のログ出力

- ✅ パスワード、トークン、秘密鍵はログに出力しない
- ✅ ログファイルの権限は 644（所有者のみ書き込み可）
- ✅ ログディレクトリの権限は 755

### ログの保存期間

| データ種別 | 推奨保持期間 | 理由 |
|-----------|------------|------|
| アクセスログ | 14-30日 | セキュリティ監査、アクセス分析 |
| エラーログ | 30-90日 | デバッグ、トラブルシューティング |
| バックアップログ | 7-14日 | バックアップ検証 |

### GDPR/プライバシー対応

個人情報をログに含める場合：
- ログローテーション保持期間を短縮（7-14日）
- IPアドレスの匿名化を検討
- ログアクセスの監査証跡を記録

## 📈 パフォーマンス最適化

### 非同期ログ書き込み

gunicornでは、ログ書き込みは非ブロッキングで処理されます。

### ログ圧縮

- **遅延圧縮**: 最新のログファイルは圧縮しない（書き込み性能）
- **gzip圧縮**: 通常70-90%のサイズ削減

### バッファリング

Pythonログのバッファリング設定（`app_v2.py`）：

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', mode='a', buffering=8192)
    ]
)
```

## 🎯 次のステップ

1. ✅ logrotate設定完了
2. ⏭️ 本番環境ログディレクトリ作成（sudo権限必要）
3. ⏭️ ログ監視ツール導入（Grafana Loki, ELKスタック等）
4. ⏭️ アラート設定（エラー急増時の通知）

---

**作成日**: 2026-01-08
**バージョン**: 1.0.0
**最終更新**: 2026-01-08
