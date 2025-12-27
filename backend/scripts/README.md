# エラー自動検知・自動修復システム

## 概要

このシステムは、Mirai Knowledge Systemのエラーを自動的に検知し、修復するための永続的な監視デーモンです。

## 機能

### 1. エラー検知

以下のエラーを自動検知します：

- **HTTP 4xx/5xx エラー**: クライアント/サーバーエラーの検出
- **Python例外**: トレースバック、各種Exceptionの検出
- **データベース接続エラー**: PostgreSQL接続障害の検出
- **ファイルシステムエラー**: ファイル不存在、権限エラー
- **メモリ不足**: MemoryError、OOM検出
- **ディスク容量不足**: ディスクフル状態の検出
- **ポート使用状況**: ポート競合の検出
- **JSON解析エラー**: 破損したJSONファイルの検出
- **Redis接続エラー**: Redisサービス障害の検出
- **SSL証明書エラー**: 証明書関連の問題検出

### 2. 自動修復アクション

検出されたエラーに対して以下の修復を自動実行します：

- **サービス再起動**: Flask、PostgreSQL、Redisの再起動
- **ログローテーション**: 大きくなったログファイルのローテーション（10MB超）
- **キャッシュクリア**: キャッシュディレクトリのクリーンアップ
- **一時ファイル削除**: /tmp内の古い一時ファイル削除
- **ディレクトリ作成**: 必要なディレクトリ（data、logs、uploads、cache）の作成
- **権限修正**: ファイル/ディレクトリ権限の修正
- **プロセス終了**: ポートを占有しているプロセスの強制終了
- **データベースVACUUM**: PostgreSQLのVACUUM実行
- **JSON修復**: 破損したJSONファイルのバックアップと修復
- **古いファイル削除**: 30日以上古いファイルの削除

### 3. ヘルスチェック

以下の項目を定期的に監視：

- PostgreSQL接続状態（60秒間隔）
- Redis接続状態（60秒間隔）
- ディスク使用率（300秒間隔、閾値: 90%）
- メモリ使用率（300秒間隔、閾値: 85%）
- HTTPエンドポイント（30秒間隔）

### 4. システムメトリクス収集

- CPU使用率
- メモリ使用量
- ディスク使用量
- ネットワーク統計
- プロセス数

## ファイル構成

```
backend/
├── scripts/
│   ├── auto_fix_daemon.py          # メインデーモン
│   ├── health_monitor.py           # ヘルスチェック・メトリクス収集
│   ├── error_patterns.json         # エラーパターン定義
│   ├── auto-fix-daemon.service     # systemdサービス定義
│   └── README.md                   # このファイル
└── logs/
    ├── auto_fix.log                # 自動修復ログ
    └── alerts.log                  # アラートログ
```

## 使用方法

### 1. 手動実行（1回のみ）

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/scripts
python3 auto_fix_daemon.py
```

### 2. 継続的監視モード

```bash
python3 auto_fix_daemon.py --continuous
```

**動作:**
- 15回のエラー検知ループを実行
- 5分間待機
- 再び15回のループを実行（永続的に繰り返す）

### 3. カスタム設定での実行

```bash
# ループ回数を20回、待機時間を10分に変更
python3 auto_fix_daemon.py --continuous --loop-count 20 --wait-minutes 10

# カスタム設定ファイルとログファイルを指定
python3 auto_fix_daemon.py --continuous \
  --config /path/to/custom_config.json \
  --log-file /path/to/custom.log
```

### 4. systemdサービスとして起動

#### インストール

```bash
# サービスファイルをコピー
sudo cp auto-fix-daemon.service /etc/systemd/system/

# systemdをリロード
sudo systemctl daemon-reload

# サービスを有効化（起動時に自動起動）
sudo systemctl enable auto-fix-daemon

# サービスを起動
sudo systemctl start auto-fix-daemon
```

#### 管理コマンド

```bash
# ステータス確認
sudo systemctl status auto-fix-daemon

# ログ確認
sudo journalctl -u auto-fix-daemon -f

# 停止
sudo systemctl stop auto-fix-daemon

# 再起動
sudo systemctl restart auto-fix-daemon

# 無効化（自動起動を停止）
sudo systemctl disable auto-fix-daemon
```

### 5. ヘルスチェックのみ実行

```bash
python3 health_monitor.py
```

出力例:
```json
{
  "timestamp": "2025-12-28T10:30:00",
  "checks": {
    "database_connection": {
      "status": "healthy",
      "message": "accepting connections"
    },
    "disk_space": {
      "status": "healthy",
      "usage_percent": 45.2,
      "free_gb": 250.5
    }
  },
  "overall_status": "healthy",
  "metrics": {
    "cpu": {"usage_percent": 25.3},
    "memory": {"usage_percent": 60.5}
  }
}
```

## コマンドラインオプション

### auto_fix_daemon.py

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--continuous` | 継続的監視モードを有効化 | False（1回実行） |
| `--config PATH` | 設定ファイルのパス | `./error_patterns.json` |
| `--log-file PATH` | ログファイルのパス | `../logs/auto_fix.log` |
| `--loop-count N` | 1イテレーションあたりのループ回数 | 15 |
| `--wait-minutes N` | イテレーション間の待機時間（分） | 5 |

## 設定ファイル（error_patterns.json）

### エラーパターンの定義

```json
{
  "error_patterns": [
    {
      "id": "unique_id",
      "name": "エラー名",
      "pattern": "正規表現パターン",
      "severity": "warning|error|critical",
      "auto_fix": true,
      "actions": [
        {
          "type": "action_type",
          "description": "説明"
        }
      ]
    }
  ]
}
```

### 利用可能なアクションタイプ

- `service_restart`: サービス再起動
- `log_rotate`: ログローテーション
- `cache_clear`: キャッシュクリア
- `temp_file_cleanup`: 一時ファイル削除
- `create_missing_dirs`: ディレクトリ作成
- `fix_permissions`: 権限修正
- `check_port`: ポート確認
- `kill_process_on_port`: プロセス終了
- `database_vacuum`: DB VACUUM
- `backup_and_fix_json`: JSON修復
- `old_file_cleanup`: 古いファイル削除
- `alert`: アラート送信のみ
- `log_analysis`: ログ分析

### 自動修復設定

```json
{
  "auto_fix_config": {
    "max_retries": 3,              // 最大リトライ回数
    "retry_delay": 60,             // リトライ間隔（秒）
    "cooldown_period": 300,        // クールダウン期間（秒）
    "enable_notifications": true,  // 通知有効化
    "notification_channels": ["log", "email"],
    "backup_before_fix": true      // 修復前バックアップ
  }
}
```

## ログファイル

### auto_fix.log

自動修復の詳細ログ

```
2025-12-28 10:30:15 - AutoFixDaemon - [INFO] - === 検知サイクル 1 開始 ===
2025-12-28 10:30:16 - AutoFixDaemon - [WARNING] - エラー検出: HTTP 5xxエラー
2025-12-28 10:30:17 - AutoFixDaemon - [INFO] - 修復アクション実行: service_restart
2025-12-28 10:30:20 - AutoFixDaemon - [INFO] - 自動修復完了: http_5xx
```

### alerts.log

重要なアラート（JSON形式）

```json
{"timestamp": "2025-12-28T10:30:00", "severity": "critical", "message": "Critical health check failures: database_connection"}
```

## セキュリティ考慮事項

1. **権限**: デーモンは `www-data` ユーザーで実行されます
2. **sudo権限**: サービス再起動には sudo権限が必要（sudoersに設定）
3. **リソース制限**: systemdサービスでメモリ512MB、CPU 50%に制限
4. **プライベート一時領域**: systemdの `PrivateTmp=true` を使用
5. **バックアップ**: 修復前に自動バックアップを作成

## トラブルシューティング

### デーモンが起動しない

```bash
# ログを確認
sudo journalctl -u auto-fix-daemon -n 50

# 権限を確認
ls -la /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/scripts/

# 手動実行でエラー確認
python3 auto_fix_daemon.py
```

### 自動修復が動作しない

1. `error_patterns.json` の `auto_fix` が `true` か確認
2. クールダウン期間（デフォルト300秒）内かチェック
3. ログファイルのパスが正しいか確認

### ヘルスチェックが失敗する

```bash
# PostgreSQL確認
pg_isready

# Redis確認
redis-cli ping

# ポート確認
netstat -tlnp | grep -E '(5000|5432|6379)'
```

## パフォーマンス

- **メモリ使用量**: 約50-100MB
- **CPU使用率**: 通常1-5%
- **ディスクI/O**: ログスキャン時に一時的に増加
- **ログファイルサイズ**: 自動ローテーション（10MB超）

## 拡張方法

### 新しいエラーパターンを追加

1. `error_patterns.json` の `error_patterns` に追加
2. 必要に応じて新しいアクションタイプを実装
3. デーモンを再起動

### カスタムアクションの実装

`auto_fix_daemon.py` の `execute_action()` メソッドに追加:

```python
elif action_type == 'custom_action':
    return self._custom_action(action.get('param'))

def _custom_action(self, param):
    """カスタムアクション実装"""
    # 処理内容
    return True  # 成功時
```

## 依存パッケージ

```bash
pip install psutil requests
```

システムコマンド:
- `pg_isready`: PostgreSQL接続確認
- `lsof`: ポート使用確認
- `systemctl`: サービス管理
- `gzip`: ログ圧縮
- `tar`: バックアップ作成

## ライセンス

Mirai Knowledge System の一部として提供されます。

## サポート

問題が発生した場合は、以下を確認してください：
- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/auto_fix.log`
- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/alerts.log`
- `sudo journalctl -u auto-fix-daemon`
