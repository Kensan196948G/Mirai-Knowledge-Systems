# Mirai Knowledge Systems - 構造化ログガイド

**Phase**: G-15
**Version**: 1.6.0
**Date**: 2026-02-17

---

## 目次

1. [概要](#概要)
2. [JSONスキーマ](#jsonスキーマ)
3. [環境設定](#環境設定)
4. [Correlation ID追跡](#correlation-id追跡)
5. [ログクエリ例](#ログクエリ例)
6. [Grafana統合](#grafana統合)
7. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### 構造化ログとは

構造化ログは、ログメッセージをJSON形式で出力することで、機械可読性を高め、ログ分析ツールとの統合を容易にする手法です。

**従来のログ（非構造化）**:
```
2026-02-17 14:32:01 - app_v2 - INFO - User admin logged in from 192.168.0.145
```

**構造化ログ（JSON形式）**:
```json
{
  "timestamp": "2026-02-17T14:32:01.123456",
  "level": "INFO",
  "logger": "app_v2",
  "message": "User logged in",
  "user_id": 5,
  "username": "admin",
  "ip_address": "192.168.0.145",
  "correlation_id": "a7f3c9e1-4b2d-4a5e-8f1c-3d2e9b6c4a8f"
}
```

### メリット

- ✅ **検索容易**: jq, grep, Grafana Loki等で高速クエリ
- ✅ **集計可能**: エラー率、レスポンスタイム等の自動集計
- ✅ **分散トレーシング**: Correlation IDでリクエスト追跡
- ✅ **監視統合**: Prometheus, Grafana, ELK Stack等と連携

---

## JSONスキーマ

### 基本フィールド（全ログ共通）

| フィールド | 型 | 説明 | 例 |
|-----------|-----|------|-----|
| `timestamp` | ISO 8601 | ログ出力時刻 | `2026-02-17T14:32:01.123456` |
| `level` | String | ログレベル | `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `logger` | String | ロガー名 | `app_v2`, `ms365_sync_service` |
| `message` | String | ログメッセージ | `Request completed` |
| `module` | String | Pythonモジュール名 | `app_v2` |
| `function` | String | 関数名 | `get_knowledge` |
| `line` | Integer | 行番号 | `4123` |
| `environment` | String | 環境 | `development`, `production` |
| `service` | String | サービス識別子 | `mirai-knowledge-backend` |

### リクエストコンテキストフィールド（HTTP リクエスト時）

| フィールド | 型 | 説明 | 例 |
|-----------|-----|------|-----|
| `correlation_id` | UUID | 相関ID（リクエスト追跡用） | `a7f3c9e1-4b2d-4a5e-8f1c-3d2e9b6c4a8f` |
| `user_id` | Integer | ユーザーID | `5` |
| `username` | String | ユーザー名 | `admin` |
| `ip_address` | String | クライアントIPアドレス | `192.168.0.145` |
| `method` | String | HTTPメソッド | `GET`, `POST`, `PUT`, `DELETE` |
| `path` | String | リクエストパス | `/api/v1/knowledge` |
| `user_agent` | String | User-Agent文字列 | `Mozilla/5.0...` |
| `referer` | String | Refererヘッダー | `https://example.com/dashboard` |

### レスポンスメトリクスフィールド（after_request時）

| フィールド | 型 | 説明 | 例 |
|-----------|-----|------|-----|
| `status_code` | Integer | HTTPステータスコード | `200`, `404`, `500` |
| `duration_ms` | Float | リクエスト処理時間（ミリ秒） | `142.5` |
| `endpoint` | String | Flaskエンドポイント名 | `get_knowledge` |

### 例外フィールド（エラー時）

| フィールド | 型 | 説明 | 例 |
|-----------|-----|------|-----|
| `exception` | String | 例外型とメッセージ | `ValueError: Invalid token` |
| `stack_trace` | String | スタックトレース | `Traceback (most recent call last):\n...` |

---

## 環境設定

### 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `MKS_ENABLE_JSON_LOGGING` | `true`（本番）/ `false`（開発） | JSON logging有効化 |
| `MKS_LOG_FILE` | `/var/log/mirai-knowledge/app.log` | ログファイルパス |
| `MKS_LOG_LEVEL` | `INFO` | ログレベル（DEBUG/INFO/WARNING/ERROR/CRITICAL） |
| `MKS_ENV` | `development` | 環境識別子（development/production） |

### 開発環境設定（デフォルト）

```bash
# .env または環境変数
MKS_ENV=development
# MKS_ENABLE_JSON_LOGGING は自動でfalseになる

# ログ出力: 標準フォーマット（コンソール）
# 2026-02-17 14:32:01 - app_v2 - INFO - Request completed
```

### 本番環境設定（推奨）

```bash
# .env または環境変数
MKS_ENV=production
MKS_ENABLE_JSON_LOGGING=true  # 自動有効化（明示不要）
MKS_LOG_FILE=/var/log/mirai-knowledge/app.log
MKS_LOG_LEVEL=INFO

# ログ出力: JSON形式（ファイル）
# {"timestamp":"2026-02-17T14:32:01.123456","level":"INFO",...}
```

### ログローテーション

```
ファイルサイズ: 100MB到達時に自動ローテーション
保持世代: 10ファイル
最大容量: 1GB（100MB × 10 + 現在ファイル）

ファイル名:
- app.log          ← 現在のログ
- app.log.1        ← 1世代前
- app.log.2        ← 2世代前
- ...
- app.log.10       ← 最古（次回削除）
```

---

## Correlation ID追跡

### Correlation IDとは

Correlation IDは、単一リクエストに関連する全ログエントリを追跡するための一意識別子（UUID v4）です。

### Flow

```
1. クライアント → リクエスト送信
   ├─ X-Correlation-ID: "abc123"（既存トレースID、オプション）
   └─ または ヘッダーなし

2. Backend (before_request)
   ├─ X-Correlation-IDヘッダーチェック
   ├─ なし → UUID v4生成（例: "a7f3c9e1-..."）
   └─ g.correlation_id に保存

3. 処理中の全ログ
   ├─ JSONFormatter が g.correlation_id 自動付与
   └─ 例: "correlation_id": "a7f3c9e1-..."

4. Backend (after_request)
   ├─ レスポンスヘッダーに X-Correlation-ID 追加
   └─ リクエスト完了ログ出力

5. クライアント ← レスポンス受信
   └─ X-Correlation-ID: "a7f3c9e1-..."（次リクエストで引き継ぎ可能）
```

### 使用例

**クライアント側（分散トレーシング）**:
```javascript
// フロントエンド→バックエンド
const correlationId = crypto.randomUUID();

fetch('/api/v1/knowledge', {
  headers: {
    'X-Correlation-ID': correlationId
  }
});

// エラー時
console.error('API failed', { correlationId });
// → ログ: "a7f3c9e1-4b2d-4a5e-8f1c-3d2e9b6c4a8f"で検索
```

**バックエンド側（ログ検索）**:
```bash
# Correlation IDで全ログ抽出
grep "a7f3c9e1-4b2d-4a5e-8f1c-3d2e9b6c4a8f" /var/log/mirai-knowledge/app.log
```

---

## ログクエリ例

### jqコマンド

**基本クエリ**:
```bash
# 全ログをJSONパース
cat /var/log/mirai-knowledge/app.log | jq .

# ERROR レベルのみ
jq 'select(.level == "ERROR")' < /var/log/mirai-knowledge/app.log

# 特定ユーザーのログ
jq 'select(.username == "admin")' < /var/log/mirai-knowledge/app.log

# 遅いリクエスト（>1秒）
jq 'select(.duration_ms > 1000)' < /var/log/mirai-knowledge/app.log

# 特定エンドポイント
jq 'select(.endpoint == "get_knowledge")' < /var/log/mirai-knowledge/app.log
```

**Correlation ID追跡**:
```bash
# 特定リクエストの全ログ
jq 'select(.correlation_id == "a7f3c9e1-4b2d-4a5e-8f1c-3d2e9b6c4a8f")' < app.log

# 時系列順ソート
jq 'select(.correlation_id == "a7f3c9e1-...")' app.log | jq -s 'sort_by(.timestamp)'
```

**集計クエリ**:
```bash
# エンドポイント別エラー数
jq 'select(.level == "ERROR") | .endpoint' app.log | sort | uniq -c

# ステータスコード分布
jq '.status_code' app.log | sort | uniq -c

# 平均レスポンスタイム（エンドポイント別）
jq -s 'group_by(.endpoint) | map({endpoint: .[0].endpoint, avg_duration: (map(.duration_ms) | add / length)})' app.log
```

### grepコマンド

```bash
# ERRORレベル検索
grep '"level":"ERROR"' /var/log/mirai-knowledge/app.log

# 特定ユーザー
grep '"username":"admin"' /var/log/mirai-knowledge/app.log

# Correlation ID
grep '"correlation_id":"a7f3c9e1-4b2d-4a5e-8f1c-3d2e9b6c4a8f"' app.log

# 500エラー
grep '"status_code":500' /var/log/mirai-knowledge/app.log

# 遅いリクエスト（正規表現で1000ms以上）
grep -E '"duration_ms":[0-9]{4,}\.' /var/log/mirai-knowledge/app.log
```

---

## Grafana統合

### ログデータソース設定

**Loki使用（推奨）**:
```yaml
# prometheus.yml または loki-config.yaml
scrape_configs:
  - job_name: 'mirai-knowledge-logs'
    static_configs:
      - targets: ['localhost:3100']
        labels:
          job: 'mirai-knowledge-backend'
          environment: 'production'
          __path__: '/var/log/mirai-knowledge/app.log'
```

**JSON Log plugin使用（代替）**:
- Grafana UI → Configuration → Data Sources → Add data source
- Type: JSON API または Loki
- URL: ファイルパスまたはLoki URL

### ダッシュボードパネル（Phase G-15 Phase 2追加）

#### Panel 1: Recent Errors

**クエリ（Loki）**:
```logql
{job="mirai-knowledge-backend"} | json | level="ERROR" | line_format "{{.timestamp}} {{.message}}"
```

**表示**: Table形式、直近100件

**カラム**:
- Timestamp
- User (username)
- Endpoint
- Message
- Correlation ID（リンク）

#### Panel 2: Request Correlation

**クエリ（Loki）**:
```logql
{job="mirai-knowledge-backend"} | json | correlation_id="$correlation_id"
```

**変数**: `$correlation_id`（テキスト入力）

**表示**: Logs panel、時系列順

#### Panel 3: Slow Queries

**クエリ（Loki）**:
```logql
{job="mirai-knowledge-backend"} | json | duration_ms > 1000
```

**表示**: Graph、p95/p99パーセンタイル

**アラート閾値**: duration_ms > 2000（2秒超）

---

## トラブルシューティング

### Q1: JSON loggingが有効にならない

**症状**: 本番環境でも標準フォーマットログが出力される

**確認**:
```bash
# 環境変数確認
echo $MKS_ENV
echo $MKS_ENABLE_JSON_LOGGING

# ログ先頭確認
head -1 /var/log/mirai-knowledge/app.log | jq .
# エラー → JSON形式でない
```

**原因**: MKS_ENABLE_JSON_LOGGING=false または MKS_ENV≠production

**対策**:
```bash
export MKS_ENV=production
export MKS_ENABLE_JSON_LOGGING=true
systemctl restart mirai-knowledge-app
```

---

### Q2: ログファイルが作成されない

**症状**: `/var/log/mirai-knowledge/app.log`が存在しない

**確認**:
```bash
ls -la /var/log/mirai-knowledge/
# Permission denied または No such file or directory
```

**原因**: ディレクトリ権限不足

**対策**:
```bash
# ディレクトリ作成
sudo mkdir -p /var/log/mirai-knowledge

# 権限設定（mirai-knowledge-appユーザーで実行する場合）
sudo chown mirai-app:mirai-app /var/log/mirai-knowledge
sudo chmod 755 /var/log/mirai-knowledge
```

---

### Q3: Correlation IDがログに出ない

**症状**: JSONログに`correlation_id`フィールドがない

**確認**:
```bash
# ログサンプル確認
tail -1 /var/log/mirai-knowledge/app.log | jq '.correlation_id'
# null
```

**原因**: リクエスト外のログ（起動時、バックグラウンドタスク等）

**説明**: Correlation IDはHTTPリクエスト時のみ生成されます。
- ✅ 正常: アプリ起動時のログには`correlation_id`なし
- ✅ 正常: `/api/v1/knowledge`リクエスト時のログには`correlation_id`あり

---

### Q4: ログが大きくなりすぎる

**症状**: `/var/log/mirai-knowledge/app.log`が10GB超え

**確認**:
```bash
du -sh /var/log/mirai-knowledge/
# 10G /var/log/mirai-knowledge/
```

**原因**: ログローテーション未動作

**対策**:
```bash
# RotatingFileHandler設定確認
grep "RotatingFileHandler" backend/json_logger.py
# maxBytes=100*1024*1024, backupCount=10 を確認

# 手動でローテーション実行（Python）
python3 -c "
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler('/var/log/mirai-knowledge/app.log', maxBytes=100*1024*1024, backupCount=10)
handler.doRollover()
"
```

---

### Q5: Correlation IDで検索してもログが1件しか見つからない

**症状**: `grep correlation_id app.log`で1行しかヒットしない

**原因**: リクエスト中に1つのログしか出力されていない（正常）

**説明**:
- ✅ 正常: シンプルなGETリクエスト → "Request completed"ログのみ
- ⚠️ 異常: 複雑な処理（DB接続、外部API呼び出し等）でログが1つだけ

**対策**: 重要な処理ステップでlogger.info()を追加
```python
logger.info("Fetching data from database", extra={"query": query_name})
logger.info("External API call started", extra={"api": "MS365"})
```

---

## ベストプラクティス

### ✅ DO（推奨）

1. **重要な処理でログ出力**:
   ```python
   logger.info("User authentication successful", extra={"user_id": user_id})
   logger.error("Database connection failed", extra={"error": str(e)})
   ```

2. **%sプレースホルダー使用**（セキュリティ、Phase G-2ルール）:
   ```python
   logger.info("User %s logged in from %s", username, ip_address)
   # NOT: logger.info(f"User {username} logged in from {ip_address}")
   ```

3. **Correlation IDを引き継ぐ（マイクロサービス）**:
   ```python
   headers = {"X-Correlation-ID": g.correlation_id}
   response = requests.get(external_api_url, headers=headers)
   ```

4. **機密情報を出力しない**:
   ```python
   # ❌ BAD
   logger.info("JWT token: %s", token)

   # ✅ GOOD
   logger.info("JWT token length: %d", len(token))
   ```

### ❌ DON'T（非推奨）

1. **print()使用禁止**（Phase G-2で全廃済み）:
   ```python
   # ❌ BAD
   print("User logged in")

   # ✅ GOOD
   logger.info("User logged in")
   ```

2. **f-string使用禁止**（セキュリティ、Phase G-2ルール）:
   ```python
   # ❌ BAD
   logger.info(f"User {user_id} accessed {endpoint}")

   # ✅ GOOD
   logger.info("User %s accessed %s", user_id, endpoint)
   ```

3. **Correlation IDを手動設定しない**:
   ```python
   # ❌ BAD
   g.correlation_id = "my-custom-id"

   # ✅ GOOD
   # 自動生成に任せる（before_request_metricsで設定済み）
   ```

---

## 付録

### A. ログファイル構造

```
/var/log/mirai-knowledge/
├── app.log           ← 最新ログ（100MB未満）
├── app.log.1         ← 1世代前（100MB）
├── app.log.2         ← 2世代前（100MB）
├── ...
└── app.log.10        ← 最古（100MB）
```

### B. JSON Schema（完全版）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "timestamp": {"type": "string", "format": "date-time"},
    "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
    "logger": {"type": "string"},
    "message": {"type": "string"},
    "module": {"type": "string"},
    "function": {"type": "string"},
    "line": {"type": "integer"},
    "environment": {"type": "string", "enum": ["development", "production"]},
    "service": {"type": "string", "const": "mirai-knowledge-backend"},
    "correlation_id": {"type": "string", "format": "uuid"},
    "user_id": {"type": "integer"},
    "username": {"type": "string"},
    "ip_address": {"type": "string", "format": "ipv4"},
    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
    "path": {"type": "string"},
    "user_agent": {"type": "string"},
    "status_code": {"type": "integer"},
    "duration_ms": {"type": "number"},
    "endpoint": {"type": "string"},
    "exception": {"type": "string"},
    "stack_trace": {"type": "string"}
  },
  "required": ["timestamp", "level", "logger", "message", "environment", "service"]
}
```

### C. ログレベルガイドライン

| レベル | 使用場面 | 例 |
|--------|---------|-----|
| `DEBUG` | 開発時デバッグ情報 | `logger.debug("SQL query: %s", query)` |
| `INFO` | 通常動作の記録 | `logger.info("User logged in")` |
| `WARNING` | 警告（処理継続可能） | `logger.warning("Cache miss")` |
| `ERROR` | エラー（処理失敗） | `logger.error("Database connection failed")` |
| `CRITICAL` | 致命的エラー（サービス停止） | `logger.critical("Out of memory")` |

---

**生成日**: 2026-02-17
**バージョン**: Phase G-15 Phase 1
**担当**: Claude Code + code-reviewer agent
