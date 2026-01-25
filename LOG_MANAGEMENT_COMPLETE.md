# ログ管理完全ガイド

Mirai Knowledge System - 本番環境ログ管理体制

作成日: 2026-01-09
バージョン: 1.0.0
ステータス: ✅ 完了

---

## 📋 目次

1. [概要](#概要)
2. [ログローテーション設定](#ログローテーション設定)
3. [構造化ログ（JSON形式）](#構造化ログjson形式)
4. [ログレベル管理](#ログレベル管理)
5. [ログ分析ツール](#ログ分析ツール)
6. [運用手順](#運用手順)
7. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### ログ管理の目的

本システムでは、以下の目的でログ管理体制を整備しています：

- **障害対応**: システム障害発生時の原因調査
- **セキュリティ監査**: 不正アクセス・異常動作の検知
- **パフォーマンス分析**: レスポンス時間・ボトルネック特定
- **法令遵守**: アクセスログ・監査ログの長期保存

### ログファイル一覧

| ログファイル | 用途 | 保持期間 | ローテーション条件 |
|------------|------|---------|----------------|
| `/var/log/mirai-knowledge/access.log` | HTTPアクセスログ | 14日 | 毎日 or 100MB超過 |
| `/var/log/mirai-knowledge/error.log` | Gunicornエラーログ | 90日 | 毎日 |
| `/var/log/mirai-knowledge/app.log` | Flaskアプリログ | 30日 | 毎日 |
| `/var/log/mirai-knowledge/audit.log` | セキュリティ監査ログ | 180日 | 毎日 |
| `/var/log/mirai-knowledge/*.log` | その他一般ログ | 30日 | 毎日 |

---

## ログローテーション設定

### インストール

```bash
# logrotate設定ファイルをシステムディレクトリにコピー
sudo cp config/logrotate/mirai-knowledge-system /etc/logrotate.d/

# パーミッション設定
sudo chmod 644 /etc/logrotate.d/mirai-knowledge-system
sudo chown root:root /etc/logrotate.d/mirai-knowledge-system
```

### 設定内容

#### 1. アクセスログ（高頻度・短期保持）

```
/var/log/mirai-knowledge/access.log {
    daily           # 毎日ローテーション
    rotate 14       # 14日分保持
    size 100M       # 100MB超過で強制ローテーション
    compress        # 圧縮保存
    delaycompress   # 最新分は次回まで非圧縮
}
```

**特徴**:
- サイズが大きくなりやすいため、100MB制限付き
- ディスク容量削減のため14日保持
- 統計分析に使用

#### 2. エラーログ（長期保持）

```
/var/log/mirai-knowledge/error.log {
    daily           # 毎日ローテーション
    rotate 90       # 90日分保持（長期トラブルシューティング用）
    compress        # 圧縮保存
}
```

**特徴**:
- 障害調査のため長期保持（90日）
- CRITICAL エラーは自動通知可能（オプション）

#### 3. 監査ログ（超長期保持）

```
/var/log/mirai-knowledge/audit.log {
    daily           # 毎日ローテーション
    rotate 180      # 180日分保持（法令遵守・監査対応）
    create 0600     # 厳格なパーミッション
}
```

**特徴**:
- セキュリティ監査用に180日保持
- チェックサム記録で改ざん検知

### ローテーション動作確認

```bash
# ドライラン（実際には実行しない）
sudo logrotate -d /etc/logrotate.d/mirai-knowledge-system

# 強制実行（テスト用）
sudo logrotate -f /etc/logrotate.d/mirai-knowledge-system

# ステータス確認
cat /var/lib/logrotate/status
```

---

## 構造化ログ（JSON形式）

### JSON形式の利点

- **機械可読性**: ログ分析ツール（Elasticsearch, Splunk等）と統合可能
- **検索効率**: フィールド単位で高速検索
- **一貫性**: 構造化されたデータで解析が容易

### アクセスログのJSON形式

**設定ファイル**: `backend/gunicorn.conf.py`

```python
access_log_format = '''{"timestamp":"%(t)s","remote_addr":"%(h)s","method":"%(m)s","path":"%(U)s","query":"%(q)s","protocol":"%(H)s","status":%(s)s,"size":%(b)s,"referer":"%(f)s","user_agent":"%(a)s","response_time_us":%(D)s,"response_time_ms":%(M)s,"process_id":"%(p)s"}'''
```

**出力例**:

```json
{
  "timestamp": "[09/Jan/2026:10:15:30 +0900]",
  "remote_addr": "192.168.0.100",
  "method": "POST",
  "path": "/api/v1/auth/login",
  "query": "",
  "protocol": "HTTP/1.1",
  "status": 200,
  "size": 512,
  "referer": "https://example.com/",
  "user_agent": "Mozilla/5.0...",
  "response_time_us": 125000,
  "response_time_ms": 125,
  "process_id": "12345"
}
```

### アプリケーションログのJSON形式

**実装**: `backend/json_logger.py`

```python
from json_logger import setup_json_logging

# Flask アプリケーション初期化時
setup_json_logging(
    app,
    log_file='/var/log/mirai-knowledge/app.log',
    log_level='INFO',
    enable_console=False  # 本番環境では無効
)
```

**出力例**:

```json
{
  "timestamp": "2026-01-09T10:15:30.123456",
  "level": "ERROR",
  "logger": "app_v2",
  "message": "Failed to authenticate user",
  "module": "app_v2",
  "function": "login",
  "line": 142,
  "user_id": 5,
  "request_id": "abc-def-123",
  "ip_address": "192.168.1.100",
  "method": "POST",
  "path": "/api/v1/auth/login",
  "exception": "ValueError: Invalid credentials"
}
```

### カスタムロガーの使用

```python
from json_logger import ContextualLogger

logger = ContextualLogger('my_module')

# 自動的に user_id, request_id が付加される
logger.info('User logged in')
logger.error('Database connection failed', exc_info=True)
```

---

## ログレベル管理

### 環境変数での設定

**ファイル**: `backend/.env`

```bash
# ログレベル: DEBUG, INFO, WARNING, ERROR, CRITICAL
MKS_LOG_LEVEL=INFO

# ログファイルパス
MKS_ACCESS_LOG=/var/log/mirai-knowledge/access.log
MKS_ERROR_LOG=/var/log/mirai-knowledge/error.log
MKS_APP_LOG=/var/log/mirai-knowledge/app.log
MKS_AUDIT_LOG=/var/log/mirai-knowledge/audit.log

# ログフォーマット: json or text
MKS_LOG_FORMAT=json
```

### ログレベルの使い分け

| レベル | 用途 | 本番環境 | 開発環境 |
|-------|------|---------|---------|
| **DEBUG** | デバッグ情報（変数値等） | ❌ 無効 | ✅ 有効 |
| **INFO** | 通常動作ログ（リクエスト等） | ✅ 有効 | ✅ 有効 |
| **WARNING** | 警告（非推奨機能使用等） | ✅ 有効 | ✅ 有効 |
| **ERROR** | エラー（例外発生等） | ✅ 有効 | ✅ 有効 |
| **CRITICAL** | 致命的エラー（サービス停止等） | ✅ 有効 | ✅ 有効 |

### 本番環境推奨設定

```bash
# 本番環境
MKS_LOG_LEVEL=INFO        # INFO以上を記録
MKS_LOG_FORMAT=json       # JSON形式

# 開発環境
MKS_LOG_LEVEL=DEBUG       # すべてのログを記録
MKS_LOG_FORMAT=text       # 可読性優先
```

---

## ログ分析ツール

### ログ分析スクリプト

**ファイル**: `scripts/log-analysis.sh`

### 基本的な使い方

```bash
# 全レポート出力
./scripts/log-analysis.sh full-report

# 個別レポート
./scripts/log-analysis.sh error-summary    # エラーログ集計
./scripts/log-analysis.sh access-stats     # アクセスログ統計
./scripts/log-analysis.sh disk-usage       # ディスク使用量
./scripts/log-analysis.sh recent-errors    # 最近のエラー
./scripts/log-analysis.sh slow-requests    # 遅いリクエスト検出
./scripts/log-analysis.sh status-codes     # HTTPステータスコード集計
./scripts/log-analysis.sh top-ips          # アクセス元IP集計
./scripts/log-analysis.sh user-activity    # ユーザーアクティビティ
```

### エラーログ集計

```bash
./scripts/log-analysis.sh error-summary
```

**出力例**:

```
========================================
エラーログ集計
========================================

=== ログレベル別集計 ===
   1245 "level":"INFO"
    342 "level":"WARNING"
     78 "level":"ERROR"
      5 "level":"CRITICAL"

=== エラー数統計 ===
総行数: 1670
ERROR: 78
WARNING: 342
CRITICAL: 5
✗ CRITICALエラーが検出されました！
```

### アクセスログ統計

```bash
./scripts/log-analysis.sh access-stats
```

**出力例**:

```
========================================
アクセスログ統計
========================================

=== HTTPステータスコード集計 ===
   8542 200
    156 404
     89 500
     45 401

=== リクエストメソッド集計 ===
   7234 GET
   1456 POST
     89 PUT
     34 DELETE

=== アクセス数集計 ===
総リクエスト数: 8921
成功 (200): 8542
エラー (4xx/5xx): 379
成功率: 95%
✓ 成功率は正常範囲です
```

### 遅いリクエスト検出

```bash
./scripts/log-analysis.sh slow-requests
```

**出力例**:

```
========================================
遅いリクエスト（レスポンス時間 > 1秒）
========================================

=== 1秒以上のリクエスト ===
検出数: 23 件

=== 上位10件（遅い順） ===
2026-01-09T10:15:30  POST  /api/v1/search  3542  200
2026-01-09T10:16:45  GET   /api/v1/documents/123  2134  200
```

### ディスク使用量確認

```bash
./scripts/log-analysis.sh disk-usage
```

**出力例**:

```
========================================
ログディスク使用量
========================================

=== ディレクトリ全体 ===
1.2G    /var/log/mirai-knowledge

=== ファイル別使用量（上位10件） ===
512M    access.log
342M    error.log
128M    app.log
 89M    access.log.1.gz
 67M    error.log.1.gz

=== 圧縮ファイル数 ===
圧縮済みログ: 45 ファイル

=== ディスクパーティション使用率 ===
/dev/sda1       50G   15G   33G   32% /var
✓ ディスク使用率は正常範囲です
```

---

## 運用手順

### 日次運用

#### 1. ログ確認（毎朝実施）

```bash
# エラーログ確認
./scripts/log-analysis.sh error-summary

# 前日のCRITICALエラー確認
grep '"level":"CRITICAL"' /var/log/mirai-knowledge/error.log | tail -20
```

#### 2. ディスク容量確認（週次）

```bash
# ログディスク使用量確認
./scripts/log-analysis.sh disk-usage

# パーティション全体
df -h /var
```

#### 3. パフォーマンス確認（週次）

```bash
# 遅いリクエスト検出
./scripts/log-analysis.sh slow-requests

# アクセス統計
./scripts/log-analysis.sh access-stats
```

### 月次運用

#### 1. ログレポート作成

```bash
# 全レポート出力して保存
./scripts/log-analysis.sh full-report > /tmp/log-report-$(date +%Y%m).txt
```

#### 2. 古いログのアーカイブ（オプション）

```bash
# 90日以上前のログをアーカイブ
cd /var/log/mirai-knowledge
tar czf ~/log-archive-$(date +%Y%m).tar.gz *.log.*.gz
```

#### 3. ディスク容量最適化

```bash
# 古いログ削除（慎重に！）
./scripts/log-analysis.sh clean-old-logs
```

### 障害発生時

#### 1. エラーログの緊急確認

```bash
# 最近のCRITICAL/ERRORを表示
./scripts/log-analysis.sh recent-errors

# リアルタイムでエラー監視
tail -f /var/log/mirai-knowledge/error.log | grep -E '(CRITICAL|ERROR)'
```

#### 2. アクセスログの緊急確認

```bash
# 直近のアクセスログ確認
tail -100 /var/log/mirai-knowledge/access.log | jq .

# 5xxエラーのみ抽出
grep '"status":5[0-9][0-9]' /var/log/mirai-knowledge/access.log | tail -50
```

#### 3. システム負荷確認

```bash
# プロセス確認
ps aux | grep gunicorn

# リソース使用状況
top -p $(pgrep -d',' gunicorn)
```

---

## トラブルシューティング

### ログローテーションが動作しない

#### 症状

```bash
# ログファイルが肥大化している
ls -lh /var/log/mirai-knowledge/
# -rw-r--r-- 1 kensan kensan 5.2G Jan 09 10:00 access.log  # 異常！
```

#### 原因と対処

**原因1: logrotateが実行されていない**

```bash
# cronジョブ確認
ls -l /etc/cron.daily/logrotate

# 手動実行
sudo logrotate -f /etc/logrotate.d/mirai-knowledge-system
```

**原因2: 設定ファイルの構文エラー**

```bash
# 設定検証
sudo logrotate -d /etc/logrotate.d/mirai-knowledge-system

# エラーメッセージを確認して修正
```

**原因3: パーミッション不足**

```bash
# ログディレクトリのパーミッション確認
ls -ld /var/log/mirai-knowledge/

# 修正
sudo chown kensan:kensan /var/log/mirai-knowledge/
sudo chmod 750 /var/log/mirai-knowledge/
```

### JSON形式のログがパースできない

#### 症状

```bash
# jqでエラーが出る
cat /var/log/mirai-knowledge/access.log | jq .
# parse error: Invalid numeric literal at line 1, column 10
```

#### 原因と対処

**原因1: 混在形式（JSON + テキスト）**

```bash
# JSON形式のみ抽出
grep '^{' /var/log/mirai-knowledge/access.log | jq .
```

**原因2: 不正なJSON（クォート不足等）**

```bash
# 設定確認
grep 'access_log_format' backend/gunicorn.conf.py

# Gunicorn再起動
sudo systemctl restart mirai-knowledge-prod.service
```

### ディスク容量不足

#### 症状

```bash
df -h /var
# /dev/sda1  50G  48G  0  96% /var  # 危険！
```

#### 緊急対処

```bash
# 1. 未圧縮のログを手動圧縮
cd /var/log/mirai-knowledge
gzip access.log.1 error.log.1

# 2. 古い圧縮ログを一時削除
rm -f *.log.*.gz

# 3. ログローテーション強制実行
sudo logrotate -f /etc/logrotate.d/mirai-knowledge-system

# 4. ディスク容量再確認
df -h /var
```

#### 恒久対策

```bash
# 保持期間を短縮（/etc/logrotate.d/mirai-knowledge-system）
# rotate 30 → rotate 7  # 30日 → 7日
sudo vi /etc/logrotate.d/mirai-knowledge-system

# または、ログを別パーティションに移動
sudo mkdir /mnt/logs
sudo rsync -av /var/log/mirai-knowledge/ /mnt/logs/
sudo ln -s /mnt/logs /var/log/mirai-knowledge
```

### ログに何も出力されない

#### 症状

```bash
# ログファイルが空、または更新されない
ls -lh /var/log/mirai-knowledge/app.log
# -rw-r--r-- 1 kensan kensan 0 Jan 09 08:00 app.log  # 空ファイル
```

#### 原因と対処

**原因1: ログファイルのパーミッション不足**

```bash
# パーミッション確認
ls -l /var/log/mirai-knowledge/app.log

# 修正
sudo chown kensan:kensan /var/log/mirai-knowledge/app.log
sudo chmod 640 /var/log/mirai-knowledge/app.log
```

**原因2: ログレベルが高すぎる**

```bash
# 環境変数確認
grep MKS_LOG_LEVEL backend/.env

# DEBUGに変更してテスト
MKS_LOG_LEVEL=DEBUG
sudo systemctl restart mirai-knowledge-prod.service
```

**原因3: ロガー設定の問題**

```bash
# Flaskアプリのログ設定確認
grep 'setup_json_logging' backend/app_v2.py

# ロガーが初期化されているか確認
```

---

## 高度な活用

### Elasticsearchとの統合

JSON形式のログはElasticsearch + Kibanaで可視化可能です。

```bash
# Filebeat設定例（/etc/filebeat/filebeat.yml）
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/mirai-knowledge/access.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "mirai-knowledge-access-%{+yyyy.MM.dd}"
```

### Prometheusとの統合

ログからメトリクスを抽出してPrometheusで監視可能です。

```bash
# mtail設定例（ログベースのメトリクス抽出）
counter http_requests_total by status_code

/^{"status":(?P<status_code>\d+)/ {
  http_requests_total[$status_code]++
}
```

### アラート通知

重大なエラーをSlack/メールで通知します。

```bash
# postrotateスクリプトに追加
if grep -q '"level":"CRITICAL"' /var/log/mirai-knowledge/error.log.1; then
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"CRITICALエラーが検出されました"}' \
    https://hooks.slack.com/services/YOUR/WEBHOOK/URL
fi
```

---

## まとめ

本ログ管理体制により、以下を実現しました：

✅ **自動ローテーション**: ディスク容量を管理しながら適切な期間保持
✅ **構造化ログ**: JSON形式で分析・統合が容易
✅ **柔軟な運用**: 環境変数でログレベル・フォーマットを制御
✅ **分析ツール**: 日次運用・障害対応に必要な分析機能
✅ **トラブルシューティング**: よくある問題の対処手順を明確化

### 次のステップ

- [ ] Elasticsearch + Kibana 統合（オプション）
- [ ] Prometheus + Grafana メトリクス監視（オプション）
- [ ] Slack/メール自動通知設定（オプション）
- [ ] ログ分析の自動レポート作成（cron設定）

---

**ドキュメント管理**

| 項目 | 内容 |
|-----|------|
| 作成日 | 2026-01-09 |
| 作成者 | Claude Code |
| バージョン | 1.0.0 |
| 最終更新 | 2026-01-09 |
| レビュー状況 | ✅ 完了 |

**関連ドキュメント**

- [PRODUCTION_DEPLOYMENT.md](/mnt/LinuxHDD/Mirai-Knowledge-Systems/PRODUCTION_DEPLOYMENT.md) - 本番環境デプロイ手順
- [SECURITY_HARDENING.md](/mnt/LinuxHDD/Mirai-Knowledge-Systems/SECURITY_HARDENING.md) - セキュリティ強化
- [config/logrotate/mirai-knowledge-system](/mnt/LinuxHDD/Mirai-Knowledge-Systems/config/logrotate/mirai-knowledge-system) - logrotate設定
- [backend/json_logger.py](/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/json_logger.py) - JSON形式ロガー実装
- [scripts/log-analysis.sh](/mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/log-analysis.sh) - ログ分析スクリプト
