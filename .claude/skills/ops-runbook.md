# ops-runbook: 運用手順書作成SubAgent

## 役割
本番運用手順書とトラブルシューティングガイドを作成するSubAgent。

## 責務
- 運用手順書の作成
- トラブルシューティングガイドの作成
- インシデント対応手順の文書化
- 定期メンテナンス手順の作成

## 成果物
以下のディレクトリにファイルを生成：
- `runbook/{feature}_operations.md`: 運用手順書
- `runbook/{feature}_troubleshooting.md`: トラブルシューティングガイド
- `docs/operations/{feature}_maintenance.md`: メンテナンス手順書

## 入力
- 実装コード（backend/**, webui/**）
- 設計書（design/**）
- CI/CD設定（.github/workflows/**）
- CLAUDE.md（プロジェクトコンテキスト）

## 実行ルール

### 1. 運用手順書テンプレート

```markdown
# {Feature名} 運用手順書

## 1. 概要
- 機能名: {feature_name}
- 担当者: {owner}
- 最終更新: 2026-01-31
- バージョン: 1.0

## 2. アーキテクチャ概要
### 2.1 システム構成
```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │ HTTPS
┌──────▼───────┐
│    Nginx     │ ← リバースプロキシ
└──────┬───────┘
       │
┌──────▼───────┐
│   Gunicorn   │ ← WSGIサーバー
└──────┬───────┘
       │
┌──────▼───────┐
│  Flask App   │ ← アプリケーション
└──────┬───────┘
       │
┌──────▼───────┐
│  PostgreSQL  │ ← データベース
└──────────────┘
```

### 2.2 主要コンポーネント
- **Web Server**: Nginx 1.24+
- **App Server**: Gunicorn 21.2+
- **Framework**: Flask 3.1.2
- **Database**: PostgreSQL 16.11
- **Cache**: Redis 7.0+ (オプション)

## 3. デプロイ手順

### 3.1 事前チェック
```bash
# 1. ディスク容量確認
df -h /opt/mirai-knowledge-systems

# 2. メモリ使用量確認
free -h

# 3. データベース接続確認
psql -h localhost -U mks_user -d mks_db -c "SELECT version();"

# 4. バックアップ確認
ls -lh /backups/mks/
```

### 3.2 デプロイ実行
```bash
# 1. 最新コードを取得
cd /opt/mirai-knowledge-systems
git pull origin main

# 2. 依存関係更新
cd backend
pip install -r requirements.txt

# 3. データベースマイグレーション
flask db upgrade

# 4. サービス再起動
sudo systemctl restart mirai-knowledge-app

# 5. ヘルスチェック
curl -f http://localhost:9100/api/health || echo "❌ ヘルスチェック失敗"
```

### 3.3 事後確認
```bash
# 1. サービス状態確認
sudo systemctl status mirai-knowledge-app

# 2. ログ確認
sudo journalctl -u mirai-knowledge-app -n 50 --no-pager

# 3. エラーログ確認
tail -n 50 /var/log/mirai-knowledge-systems/error.log

# 4. Smokeテスト実行
./ci/smoke_test.sh production
```

## 4. 起動・停止手順

### 4.1 サービス起動
```bash
# 本番環境
sudo systemctl start mirai-knowledge-app

# 開発環境
sudo systemctl start mirai-knowledge-app-dev
```

### 4.2 サービス停止
```bash
# 本番環境
sudo systemctl stop mirai-knowledge-app

# 開発環境
sudo systemctl stop mirai-knowledge-app-dev
```

### 4.3 サービス再起動
```bash
# 本番環境（グレースフルリスタート）
sudo systemctl reload mirai-knowledge-app

# 開発環境
sudo systemctl restart mirai-knowledge-app-dev
```

### 4.4 ステータス確認
```bash
# サービス状態確認
sudo systemctl status mirai-knowledge-app

# ログ確認（最新50行）
sudo journalctl -u mirai-knowledge-app -n 50 --no-pager

# リアルタイムログ監視
sudo journalctl -u mirai-knowledge-app -f
```

## 5. 監視項目

### 5.1 システムリソース
| 項目 | 正常範囲 | 警告 | 危険 |
|------|---------|------|------|
| CPU使用率 | < 70% | 70-85% | > 85% |
| メモリ使用率 | < 75% | 75-90% | > 90% |
| ディスク使用率 | < 80% | 80-90% | > 90% |

### 5.2 アプリケーションメトリクス
| 項目 | 正常範囲 | 警告 | 危険 |
|------|---------|------|------|
| レスポンスタイムP95 | < 2秒 | 2-5秒 | > 5秒 |
| エラー率 | < 1% | 1-5% | > 5% |
| リクエスト数 | - | - | > 1000 req/s |

### 5.3 データベース
| 項目 | 正常範囲 | 警告 | 危険 |
|------|---------|------|------|
| 接続数 | < 50 | 50-80 | > 80 |
| クエリ時間P95 | < 100ms | 100-500ms | > 500ms |
| デッドロック | 0 | 1-3/日 | > 3/日 |

## 6. バックアップ・リストア

### 6.1 バックアップ手順
```bash
# 1. データベースバックアップ
pg_dump -h localhost -U mks_user -d mks_db -F c \
  -f /backups/mks/mks_db_$(date +%Y%m%d_%H%M%S).dump

# 2. ファイルバックアップ
tar -czf /backups/mks/files_$(date +%Y%m%d_%H%M%S).tar.gz \
  /opt/mirai-knowledge-systems/backend/data/

# 3. 設定ファイルバックアップ
cp /opt/mirai-knowledge-systems/backend/.env \
  /backups/mks/.env_$(date +%Y%m%d_%H%M%S)
```

### 6.2 リストア手順
```bash
# 1. サービス停止
sudo systemctl stop mirai-knowledge-app

# 2. データベースリストア
pg_restore -h localhost -U mks_user -d mks_db \
  -c /backups/mks/mks_db_YYYYMMDD_HHMMSS.dump

# 3. ファイルリストア
tar -xzf /backups/mks/files_YYYYMMDD_HHMMSS.tar.gz -C /

# 4. サービス起動
sudo systemctl start mirai-knowledge-app

# 5. 動作確認
curl -f http://localhost:9100/api/health
```

## 7. ログ管理

### 7.1 ログファイル一覧
| ログ | パス | 用途 |
|------|------|------|
| アプリケーションログ | /var/log/mirai-knowledge-systems/app.log | 一般ログ |
| エラーログ | /var/log/mirai-knowledge-systems/error.log | エラー専用 |
| アクセスログ | /var/log/nginx/access.log | Nginxアクセス |
| 監査ログ | /var/log/mirai-knowledge-systems/audit.log | 監査証跡 |

### 7.2 ログローテーション
```bash
# /etc/logrotate.d/mirai-knowledge-systems
/var/log/mirai-knowledge-systems/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 mks mks
    sharedscripts
    postrotate
        systemctl reload mirai-knowledge-app
    endscript
}
```

## 8. 定期メンテナンス

### 8.1 日次タスク
```bash
# 1. バックアップ実行（自動: cron）
/opt/mirai-knowledge-systems/scripts/daily_backup.sh

# 2. ログ確認
grep -i error /var/log/mirai-knowledge-systems/error.log
```

### 8.2 週次タスク
```bash
# 1. セキュリティスキャン（自動: cron）
/etc/cron.weekly/security-scan.sh

# 2. ディスク使用量確認
df -h

# 3. データベース統計更新
psql -U mks_user -d mks_db -c "VACUUM ANALYZE;"
```

### 8.3 月次タスク
```bash
# 1. SSL証明書有効期限確認
openssl x509 -in /etc/ssl/mks/cert.pem -noout -enddate

# 2. 依存ライブラリ更新チェック
pip list --outdated

# 3. データベースバキューム
psql -U mks_user -d mks_db -c "VACUUM FULL;"
```

## 9. アラート対応

### 9.1 アラート一覧
| アラート名 | 重要度 | 対応時間 | 対応者 |
|-----------|--------|---------|--------|
| Critical Error | P0 | 即座 | オンコールエンジニア |
| High CPU | P1 | 1時間以内 | システム管理者 |
| Disk Full | P1 | 1時間以内 | システム管理者 |
| Slow Query | P2 | 1営業日以内 | DBA |

### 9.2 アラート対応フロー
```
┌─────────────┐
│ アラート発生 │
└──────┬──────┘
       ↓
┌──────▼──────┐
│ 重要度判定   │
└──────┬──────┘
       ↓
┌──────▼──────┐    NO    ┌─────────────┐
│ P0/P1?     ├─────────→│ チケット登録 │
└──────┬──────┘          └─────────────┘
       │ YES
       ↓
┌──────▼──────┐
│ 初期対応     │ ← トラブルシューティング
└──────┬──────┘
       ↓
┌──────▼──────┐
│ 根本対応     │
└──────┬──────┘
       ↓
┌──────▼──────┐
│ 事後報告     │
└─────────────┘
```

## 10. 連絡先

### 10.1 エスカレーションパス
1. **L1サポート**: support@example.com
2. **L2エンジニア**: engineer@example.com
3. **L3アーキテクト**: architect@example.com

### 10.2 緊急連絡先
- **オンコール**: +81-XX-XXXX-XXXX
- **Slackチャンネル**: #mirai-knowledge-systems-ops
```

### 2. トラブルシューティングガイドテンプレート

```markdown
# {Feature名} トラブルシューティングガイド

## 1. サービス起動失敗

### 症状
```bash
$ sudo systemctl start mirai-knowledge-app
Job for mirai-knowledge-app.service failed.
```

### 原因
1. ポート競合（9100が使用中）
2. 依存関係不足
3. 設定ファイルエラー
4. データベース接続失敗

### 診断
```bash
# 1. ポート確認
sudo lsof -i :9100

# 2. 依存関係確認
pip check

# 3. 設定ファイル確認
cd /opt/mirai-knowledge-systems/backend
python -c "from config import Config; print(Config.validate())"

# 4. データベース接続確認
psql -h localhost -U mks_user -d mks_db -c "SELECT 1;"
```

### 対処法
```bash
# ポート競合の場合
sudo kill $(sudo lsof -t -i:9100)

# 依存関係不足の場合
pip install -r requirements.txt

# 設定ファイルエラーの場合
vi backend/.env  # 修正

# データベース接続失敗の場合
sudo systemctl start postgresql
```

## 2. 高CPU使用率

### 症状
- CPU使用率が85%以上
- レスポンスタイムが遅延

### 原因
1. 無限ループ
2. N+1クエリ
3. 大量リクエスト

### 診断
```bash
# 1. プロセス確認
top -H -p $(pgrep -f gunicorn)

# 2. スタックトレース確認
sudo kill -USR1 $(pgrep -f gunicorn)

# 3. スロークエリ確認
psql -U mks_user -d mks_db -c "
SELECT query, state, wait_event_type, wait_event
FROM pg_stat_activity
WHERE state != 'idle' AND query_start < NOW() - INTERVAL '5 seconds';
"
```

### 対処法
```bash
# 1. グレースフルリスタート
sudo systemctl reload mirai-knowledge-app

# 2. 問題のあるクエリをキャンセル
psql -U mks_user -d mks_db -c "SELECT pg_cancel_backend(PID);"

# 3. ワーカープロセス数を削減（一時的）
vi /etc/systemd/system/mirai-knowledge-app.service
# ExecStart=/usr/local/bin/gunicorn --workers 2 ...
sudo systemctl daemon-reload
sudo systemctl restart mirai-knowledge-app
```

## 3. データベース接続エラー

### 症状
```
OperationalError: could not connect to server
```

### 原因
1. PostgreSQLサービス停止
2. 接続数上限
3. ネットワーク問題

### 診断
```bash
# 1. PostgreSQL状態確認
sudo systemctl status postgresql

# 2. 接続数確認
psql -U mks_user -d mks_db -c "
SELECT count(*) FROM pg_stat_activity;
"

# 3. ネットワーク確認
ping -c 3 localhost
```

### 対処法
```bash
# 1. PostgreSQL起動
sudo systemctl start postgresql

# 2. 接続数上限増加（/etc/postgresql/16/main/postgresql.conf）
max_connections = 150  # デフォルト: 100

# 3. 接続プールサイズ調整（backend/config.py）
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
```

## 4. ディスク容量不足

### 症状
```
OSError: [Errno 28] No space left on device
```

### 診断
```bash
# 1. ディスク使用量確認
df -h

# 2. 大きなファイル検索
find /opt/mirai-knowledge-systems -type f -size +100M

# 3. ログサイズ確認
du -sh /var/log/mirai-knowledge-systems/
```

### 対処法
```bash
# 1. 古いログ削除
find /var/log/mirai-knowledge-systems/ -name "*.log.*" -mtime +30 -delete

# 2. 古いバックアップ削除
find /backups/mks/ -name "*.dump" -mtime +90 -delete

# 3. 一時ファイル削除
rm -rf /tmp/mirai-*
```

## 5. 認証エラー

### 症状
```
401 Unauthorized
```

### 原因
1. JWT有効期限切れ
2. SECRET_KEY変更
3. 2FA検証失敗

### 診断
```bash
# 1. JWT検証
python -c "
import jwt
token = 'YOUR_TOKEN'
secret = 'YOUR_SECRET'
try:
    payload = jwt.decode(token, secret, algorithms=['HS256'])
    print('Valid:', payload)
except jwt.ExpiredSignatureError:
    print('Expired')
except jwt.InvalidTokenError as e:
    print('Invalid:', e)
"

# 2. SECRET_KEY確認
grep SECRET_KEY backend/.env
```

### 対処法
```bash
# 1. トークン再発行
curl -X POST http://localhost:9100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# 2. SECRET_KEY復元（バックアップから）
cp /backups/mks/.env_YYYYMMDD_HHMMSS backend/.env
sudo systemctl restart mirai-knowledge-app
```

## 6. チェックリスト

### 基本診断チェックリスト
- [ ] サービス状態確認（systemctl status）
- [ ] ログ確認（journalctl/error.log）
- [ ] ディスク容量確認（df -h）
- [ ] メモリ使用量確認（free -h）
- [ ] CPU使用率確認（top）
- [ ] データベース接続確認（psql）
- [ ] ネットワーク確認（ping/curl）
```

## 実行コマンド例
```bash
# Skill tool経由で実行
/ops-runbook "{feature_name}の運用手順書を作成"

# Task tool経由で実行（別プロセス）
Task(subagent_type="general-purpose", prompt="ops-runbookとして、{feature_name}の運用手順書とトラブルシューティングガイドを作成", description="Create runbook")
```

## 次のステップ
運用手順書作成後、本番デプロイ前に運用チームにレビューを依頼。

## 注意事項
- 手順は具体的かつ明確に記載する
- コマンド例は実際に動作するものを記載する
- トラブルシューティングは「症状→原因→診断→対処法」の順で記載
- 緊急連絡先を必ず記載する
- 定期メンテナンス手順を忘れずに記載する
