# 監視設定ガイド

建設土木ナレッジシステムの監視設定と運用方法を定義します。

## 目次

1. [監視項目一覧](#監視項目一覧)
2. [ヘルスチェック設定](#ヘルスチェック設定)
3. [ログ監視](#ログ監視)
4. [アラート設定](#アラート設定)
5. [通知先設定](#通知先設定)
6. [ダッシュボード構成](#ダッシュボード構成)

---

## 監視項目一覧

### システムリソース監視

#### CPU使用率

**監視内容:**
- 全体のCPU使用率
- GunicornプロセスごとのCPU使用率
- 1分/5分/15分の負荷平均

**閾値:**
| レベル | 条件 | アクション |
|--------|------|------------|
| Warning | CPU使用率 > 70% が5分継続 | アラート通知 |
| Critical | CPU使用率 > 90% が3分継続 | 緊急通知 + 自動スケーリング検討 |

**監視コマンド:**
```bash
# CPU使用率確認
top -b -n 1 | head -5
mpstat 1 5

# プロセス別CPU使用率
ps aux | grep gunicorn | awk '{print $3, $11}'

# 負荷平均
uptime
cat /proc/loadavg
```

**監視スクリプト例:**
```bash
#!/bin/bash
# /usr/local/bin/check_cpu.sh

THRESHOLD_WARN=70
THRESHOLD_CRIT=90

CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
CPU_USAGE_INT=${CPU_USAGE%.*}

if [ $CPU_USAGE_INT -gt $THRESHOLD_CRIT ]; then
    echo "CRITICAL: CPU usage is ${CPU_USAGE}%"
    exit 2
elif [ $CPU_USAGE_INT -gt $THRESHOLD_WARN ]; then
    echo "WARNING: CPU usage is ${CPU_USAGE}%"
    exit 1
else
    echo "OK: CPU usage is ${CPU_USAGE}%"
    exit 0
fi
```

---

#### メモリ使用率

**監視内容:**
- 物理メモリ使用率
- スワップ使用率
- Gunicornプロセスごとのメモリ使用量

**閾値:**
| レベル | 条件 | アクション |
|--------|------|------------|
| Warning | メモリ使用率 > 80% | アラート通知 |
| Critical | メモリ使用率 > 90% または スワップ使用率 > 50% | 緊急通知 + プロセス再起動検討 |

**監視コマンド:**
```bash
# メモリ使用率確認
free -h
cat /proc/meminfo | grep -E "MemTotal|MemAvailable|SwapTotal|SwapFree"

# プロセス別メモリ使用量
ps aux | grep gunicorn | awk '{sum+=$6} END {print sum/1024 " MB"}'

# 詳細メモリ情報
vmstat 1 5
```

**監視スクリプト例:**
```bash
#!/bin/bash
# /usr/local/bin/check_memory.sh

THRESHOLD_WARN=80
THRESHOLD_CRIT=90

MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')

if [ $MEM_USAGE -gt $THRESHOLD_CRIT ]; then
    echo "CRITICAL: Memory usage is ${MEM_USAGE}%"
    exit 2
elif [ $MEM_USAGE -gt $THRESHOLD_WARN ]; then
    echo "WARNING: Memory usage is ${MEM_USAGE}%"
    exit 1
else
    echo "OK: Memory usage is ${MEM_USAGE}%"
    exit 0
fi
```

---

#### ディスク使用率

**監視内容:**
- ルートパーティション使用率
- データディレクトリ使用率
- ログディレクトリ使用率
- inode使用率

**閾値:**
| レベル | 条件 | アクション |
|--------|------|------------|
| Warning | ディスク使用率 > 80% | アラート通知 + ログクリーンアップ |
| Critical | ディスク使用率 > 90% | 緊急通知 + 古いファイル削除 |

**監視コマンド:**
```bash
# ディスク使用率確認
df -h
df -i  # inode使用率

# ディレクトリ別使用量
du -sh /var/lib/mirai-knowledge-system/*
du -sh /var/log/mirai-knowledge-system/*

# 大きなファイルの検索
find /var/log -type f -size +100M -exec ls -lh {} \;
```

**監視スクリプト例:**
```bash
#!/bin/bash
# /usr/local/bin/check_disk.sh

THRESHOLD_WARN=80
THRESHOLD_CRIT=90
PARTITION="/"

DISK_USAGE=$(df -h $PARTITION | tail -1 | awk '{print $5}' | sed 's/%//')

if [ $DISK_USAGE -gt $THRESHOLD_CRIT ]; then
    echo "CRITICAL: Disk usage on $PARTITION is ${DISK_USAGE}%"
    exit 2
elif [ $DISK_USAGE -gt $THRESHOLD_WARN ]; then
    echo "WARNING: Disk usage on $PARTITION is ${DISK_USAGE}%"
    exit 1
else
    echo "OK: Disk usage on $PARTITION is ${DISK_USAGE}%"
    exit 0
fi
```

---

#### ネットワーク

**監視内容:**
- ネットワークトラフィック（受信/送信）
- 接続数
- パケットロス率
- レスポンスタイム

**閾値:**
| レベル | 条件 | アクション |
|--------|------|------------|
| Warning | 接続数 > 1000 または パケットロス > 1% | アラート通知 |
| Critical | 接続数 > 5000 または パケットロス > 5% | 緊急通知 + DDoS対策 |

**監視コマンド:**
```bash
# ネットワーク統計
netstat -s
ss -s

# 接続数確認
netstat -an | grep :8000 | wc -l
ss -tan | grep :8000 | wc -l

# 帯域使用量
iftop -i eth0
nethogs

# パケットロス確認
ping -c 10 8.8.8.8
mtr google.com
```

---

### アプリケーション監視

#### プロセス監視

**監視内容:**
- Gunicornマスタープロセス
- Gunicornワーカープロセス数
- プロセスの稼働時間
- ゾンビプロセス

**閾値:**
| レベル | 条件 | アクション |
|--------|------|------------|
| Critical | Gunicornプロセスが起動していない | 緊急通知 + 自動再起動 |
| Warning | ワーカー数が設定値と異なる | アラート通知 |

**監視コマンド:**
```bash
# プロセス状態確認
cd /path/to/backend
./run_production.sh status

# プロセス一覧
ps aux | grep gunicorn

# プロセス数確認
pgrep -c gunicorn

# ゾンビプロセス確認
ps aux | grep defunct
```

**監視スクリプト例:**
```bash
#!/bin/bash
# /usr/local/bin/check_gunicorn.sh

PID_FILE="/path/to/backend/gunicorn.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "CRITICAL: PID file not found"
    exit 2
fi

PID=$(cat "$PID_FILE")
if ! kill -0 "$PID" 2>/dev/null; then
    echo "CRITICAL: Gunicorn process not running (PID: $PID)"
    exit 2
fi

WORKER_COUNT=$(pgrep -P "$PID" | wc -l)
EXPECTED_WORKERS=${MKS_GUNICORN_WORKERS:-4}

if [ $WORKER_COUNT -lt $EXPECTED_WORKERS ]; then
    echo "WARNING: Only $WORKER_COUNT workers running (expected: $EXPECTED_WORKERS)"
    exit 1
fi

echo "OK: Gunicorn running with $WORKER_COUNT workers"
exit 0
```

---

#### レスポンスタイム

**監視内容:**
- APIエンドポイント平均レスポンスタイム
- P50, P95, P99レスポンスタイム
- エンドポイント別レスポンスタイム

**閾値:**
| レベル | 条件 | アクション |
|--------|------|------------|
| Warning | 平均レスポンスタイム > 1秒 | アラート通知 |
| Critical | 平均レスポンスタイム > 5秒 | 緊急通知 + パフォーマンスチューニング |

**監視コマンド:**
```bash
# curlでレスポンスタイム測定
time curl -s -o /dev/null https://api.example.com/health

# 詳細レスポンスタイム
curl -w "\nTime Total: %{time_total}s\nTime Connect: %{time_connect}s\nTime StartTransfer: %{time_starttransfer}s\n" \
  -o /dev/null -s https://api.example.com/api/v1/knowledges

# アクセスログから分析
awk '{print $NF}' /var/log/nginx/mirai-knowledge-access.log | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count}'
```

**監視スクリプト例:**
```bash
#!/bin/bash
# /usr/local/bin/check_response_time.sh

THRESHOLD_WARN=1.0
THRESHOLD_CRIT=5.0
URL="https://api.example.com/health"

RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$URL")

if (( $(echo "$RESPONSE_TIME > $THRESHOLD_CRIT" | bc -l) )); then
    echo "CRITICAL: Response time is ${RESPONSE_TIME}s"
    exit 2
elif (( $(echo "$RESPONSE_TIME > $THRESHOLD_WARN" | bc -l) )); then
    echo "WARNING: Response time is ${RESPONSE_TIME}s"
    exit 1
else
    echo "OK: Response time is ${RESPONSE_TIME}s"
    exit 0
fi
```

---

#### エラー率

**監視内容:**
- HTTPステータスコード別の発生率
- 5xx系エラー率
- 4xx系エラー率（特に401, 403, 404）

**閾値:**
| レベル | 条件 | アクション |
|--------|------|------------|
| Warning | 5xxエラー率 > 1% | アラート通知 |
| Critical | 5xxエラー率 > 5% | 緊急通知 + 障害対応 |

**監視コマンド:**
```bash
# Nginxアクセスログからエラー率算出
tail -10000 /var/log/nginx/mirai-knowledge-access.log | \
  awk '{print $9}' | sort | uniq -c | sort -rn

# 5xxエラーのみ抽出
grep ' 5[0-9][0-9] ' /var/log/nginx/mirai-knowledge-access.log | tail -20

# エラー率計算
total=$(wc -l < /var/log/nginx/mirai-knowledge-access.log)
errors=$(grep ' 5[0-9][0-9] ' /var/log/nginx/mirai-knowledge-access.log | wc -l)
echo "Error rate: $(echo "scale=2; $errors * 100 / $total" | bc)%"
```

---

## ヘルスチェック設定

### エンドポイント実装

**推奨実装（app_v2.py に追加）:**

```python
from flask import jsonify
import psutil
import os

@app.route('/health', methods=['GET'])
def health_check():
    """基本ヘルスチェック"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/health/detail', methods=['GET'])
def health_check_detail():
    """詳細ヘルスチェック"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # メモリ使用率
        memory = psutil.virtual_memory()

        # ディスク使用率
        disk = psutil.disk_usage('/')

        # データベース接続確認
        db_healthy = check_database_connection()

        health_status = {
            'status': 'healthy' if db_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': 'ok' if db_healthy else 'error',
                'cpu': {
                    'status': 'ok' if cpu_percent < 90 else 'warning',
                    'usage_percent': cpu_percent
                },
                'memory': {
                    'status': 'ok' if memory.percent < 90 else 'warning',
                    'usage_percent': memory.percent,
                    'available_mb': memory.available / 1024 / 1024
                },
                'disk': {
                    'status': 'ok' if disk.percent < 90 else 'warning',
                    'usage_percent': disk.percent,
                    'free_gb': disk.free / 1024 / 1024 / 1024
                }
            }
        }

        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

def check_database_connection():
    """データベース接続確認"""
    try:
        # JSONファイルの読み取りテスト
        data_dir = os.getenv('MKS_DATA_DIR', 'data')
        test_file = os.path.join(data_dir, 'users.json')

        if not os.path.exists(test_file):
            return False

        with open(test_file, 'r', encoding='utf-8') as f:
            json.load(f)

        return True
    except Exception:
        return False
```

---

### Nginx設定

```nginx
# /etc/nginx/sites-available/mirai-knowledge-system

# 基本ヘルスチェック（Nginx自体）
location /health {
    access_log off;
    return 200 "OK\n";
    add_header Content-Type text/plain;
}

# アプリケーションヘルスチェック
location /health/app {
    proxy_pass http://mirai_knowledge_backend/health;
    proxy_set_header Host $host;
    access_log off;
}

# 詳細ヘルスチェック（内部監視用）
location /health/detail {
    # 内部ネットワークからのみアクセス許可
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;

    proxy_pass http://mirai_knowledge_backend/health/detail;
    proxy_set_header Host $host;
    access_log off;
}
```

---

### 外部監視ツール設定

#### Uptime Robot設定例

```yaml
Monitor Type: HTTP(s)
Friendly Name: Mirai Knowledge System - Production
URL: https://api.example.com/health
Monitoring Interval: 5 minutes
Alert Contacts: admin@example.com, sms:+81-xxx-xxxx-xxxx
```

#### Datadog設定例

```yaml
# datadog-agent/conf.d/http_check.d/conf.yaml

init_config:

instances:
  - name: mirai_knowledge_health
    url: https://api.example.com/health
    timeout: 5
    http_response_status_code: 200
    tags:
      - service:mirai-knowledge
      - env:production

  - name: mirai_knowledge_health_detail
    url: https://internal.example.com/health/detail
    timeout: 10
    http_response_status_code: 200
    content_match: '"status":"healthy"'
    tags:
      - service:mirai-knowledge
      - env:production
```

---

## ログ監視

### アプリケーションログ

**ログファイル:**
- `/var/log/mirai-knowledge-system/app.log`
- `/path/to/backend/logs/error.log`
- `/path/to/backend/logs/access.log`

**監視対象パターン:**

```bash
# エラーパターン
ERROR|CRITICAL|Exception|Traceback|Failed|Internal Server Error

# 警告パターン
WARNING|WARN|Deprecated|Timeout

# セキュリティ関連
Authentication failed|Unauthorized|Invalid token|Permission denied|SQL injection
```

**監視コマンド:**

```bash
# リアルタイム監視
tail -f /var/log/mirai-knowledge-system/app.log | grep -E "ERROR|CRITICAL"

# エラー集計（過去1時間）
find /var/log/mirai-knowledge-system -name "*.log" -mmin -60 \
  -exec grep -h "ERROR" {} \; | wc -l

# エラーの種類別集計
grep "ERROR" /var/log/mirai-knowledge-system/app.log | \
  awk '{print $5}' | sort | uniq -c | sort -rn
```

**ログローテーション設定:**

```bash
# /etc/logrotate.d/mirai-knowledge-system

/var/log/mirai-knowledge-system/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        /usr/bin/systemctl reload mirai-knowledge-system > /dev/null 2>&1 || true
    endscript
}

/path/to/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        kill -USR1 $(cat /path/to/backend/gunicorn.pid) > /dev/null 2>&1 || true
    endscript
}
```

---

### Nginxログ

**ログファイル:**
- `/var/log/nginx/mirai-knowledge-access.log`
- `/var/log/nginx/mirai-knowledge-error.log`

**監視対象:**

```bash
# 5xxエラー監視
tail -f /var/log/nginx/mirai-knowledge-error.log | grep -E "error|crit|alert|emerg"

# アクセスログ分析（Top 10 IP）
awk '{print $1}' /var/log/nginx/mirai-knowledge-access.log | \
  sort | uniq -c | sort -rn | head -10

# レスポンスタイム分析
awk '{print $NF}' /var/log/nginx/mirai-knowledge-access.log | \
  sort -n | awk 'BEGIN{c=0;sum=0}{a[c++]=$1;sum+=$1}END{
    print "Min:", a[0];
    print "P50:", a[int(c*0.5)];
    print "P95:", a[int(c*0.95)];
    print "Max:", a[c-1];
    print "Avg:", sum/c
  }'
```

---

### システムログ

**ログファイル:**
- `/var/log/syslog` (Debian/Ubuntu)
- `/var/log/messages` (RHEL/CentOS)

**監視対象:**

```bash
# ディスク関連エラー
grep -i "disk\|I/O error" /var/log/syslog

# メモリ関連
grep -i "out of memory\|OOM" /var/log/syslog

# セキュリティ関連
grep -i "authentication failure\|invalid user" /var/log/auth.log
```

---

## アラート設定

### アラート優先度

| 優先度 | 対応時間 | 通知方法 | 例 |
|--------|----------|----------|-----|
| P1 (Critical) | 即座 | 電話 + SMS + Email + Slack | サービス全停止、データ損失 |
| P2 (High) | 15分以内 | SMS + Email + Slack | 主要機能停止、高負荷 |
| P3 (Medium) | 1時間以内 | Email + Slack | 部分機能障害、警告閾値超過 |
| P4 (Low) | 4時間以内 | Email | 情報提供、軽微な警告 |

---

### アラートルール設定

#### CPU使用率アラート

```yaml
# Prometheus AlertManager設定例

groups:
  - name: cpu_alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 70
        for: 5m
        labels:
          severity: warning
          service: mirai-knowledge
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value }}% for 5 minutes"

      - alert: CriticalCPUUsage
        expr: cpu_usage_percent > 90
        for: 3m
        labels:
          severity: critical
          service: mirai-knowledge
        annotations:
          summary: "Critical CPU usage detected"
          description: "CPU usage is {{ $value }}% for 3 minutes"
```

#### メモリ使用率アラート

```yaml
groups:
  - name: memory_alerts
    rules:
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 80
        for: 5m
        labels:
          severity: warning
          service: mirai-knowledge
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value }}%"

      - alert: CriticalMemoryUsage
        expr: memory_usage_percent > 90
        for: 2m
        labels:
          severity: critical
          service: mirai-knowledge
        annotations:
          summary: "Critical memory usage detected"
          description: "Memory usage is {{ $value }}%"
```

#### ディスク使用率アラート

```yaml
groups:
  - name: disk_alerts
    rules:
      - alert: HighDiskUsage
        expr: disk_usage_percent > 80
        for: 10m
        labels:
          severity: warning
          service: mirai-knowledge
        annotations:
          summary: "High disk usage detected"
          description: "Disk usage on {{ $labels.mountpoint }} is {{ $value }}%"

      - alert: CriticalDiskUsage
        expr: disk_usage_percent > 90
        for: 5m
        labels:
          severity: critical
          service: mirai-knowledge
        annotations:
          summary: "Critical disk usage detected"
          description: "Disk usage on {{ $labels.mountpoint }} is {{ $value }}%"
```

#### エラー率アラート

```yaml
groups:
  - name: error_rate_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: warning
          service: mirai-knowledge
        annotations:
          summary: "High 5xx error rate detected"
          description: "5xx error rate is {{ $value }} req/s"

      - alert: CriticalErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
          service: mirai-knowledge
        annotations:
          summary: "Critical 5xx error rate detected"
          description: "5xx error rate is {{ $value }} req/s"
```

---

## 通知先設定

### Email通知

**設定例（Postfix）:**

```bash
# /etc/postfix/main.cf
myhostname = monitoring.example.com
relayhost = [smtp.example.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_security_level = encrypt

# /etc/postfix/sasl_passwd
[smtp.example.com]:587 username:password

# 権限設定
sudo postmap /etc/postfix/sasl_passwd
sudo chmod 600 /etc/postfix/sasl_passwd
sudo systemctl restart postfix
```

**テストコマンド:**

```bash
echo "Test alert" | mail -s "Test Alert from Monitoring" admin@example.com
```

---

### Slack通知

**Webhook URL設定:**

```bash
# .env.production に追加
export MKS_SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
```

**通知スクリプト:**

```bash
#!/bin/bash
# /usr/local/bin/notify_slack.sh

WEBHOOK_URL="${MKS_SLACK_WEBHOOK_URL}"
SEVERITY="$1"
MESSAGE="$2"

# 重大度に応じた色設定
case "$SEVERITY" in
    critical)
        COLOR="#FF0000"
        EMOJI=":rotating_light:"
        ;;
    warning)
        COLOR="#FFA500"
        EMOJI=":warning:"
        ;;
    info)
        COLOR="#36A64F"
        EMOJI=":information_source:"
        ;;
    *)
        COLOR="#808080"
        EMOJI=":bell:"
        ;;
esac

# Slack通知
curl -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @- << EOF
{
  "attachments": [
    {
      "color": "$COLOR",
      "pretext": "$EMOJI Mirai Knowledge System Alert",
      "text": "$MESSAGE",
      "footer": "Monitoring System",
      "ts": $(date +%s)
    }
  ]
}
EOF
```

**使用例:**

```bash
/usr/local/bin/notify_slack.sh critical "CPU usage exceeded 90%"
/usr/local/bin/notify_slack.sh warning "Disk usage is at 85%"
```

---

### SMS通知（Twilio）

**設定:**

```bash
# .env.production に追加
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_FROM_NUMBER="+1234567890"
export TWILIO_TO_NUMBER="+819012345678"
```

**通知スクリプト:**

```bash
#!/bin/bash
# /usr/local/bin/notify_sms.sh

MESSAGE="$1"

curl -X POST "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages.json" \
  --data-urlencode "Body=$MESSAGE" \
  --data-urlencode "From=${TWILIO_FROM_NUMBER}" \
  --data-urlencode "To=${TWILIO_TO_NUMBER}" \
  -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}"
```

---

## ダッシュボード構成

### Grafanaダッシュボード設定例

#### パネル1: システムリソース概要

```json
{
  "title": "System Resources Overview",
  "panels": [
    {
      "title": "CPU Usage",
      "targets": [
        {
          "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
        }
      ],
      "thresholds": [
        {"value": 70, "color": "yellow"},
        {"value": 90, "color": "red"}
      ]
    },
    {
      "title": "Memory Usage",
      "targets": [
        {
          "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
        }
      ],
      "thresholds": [
        {"value": 80, "color": "yellow"},
        {"value": 90, "color": "red"}
      ]
    },
    {
      "title": "Disk Usage",
      "targets": [
        {
          "expr": "(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100"
        }
      ],
      "thresholds": [
        {"value": 80, "color": "yellow"},
        {"value": 90, "color": "red"}
      ]
    }
  ]
}
```

#### パネル2: アプリケーションメトリクス

```json
{
  "title": "Application Metrics",
  "panels": [
    {
      "title": "Request Rate",
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])"
        }
      ]
    },
    {
      "title": "Response Time (P95)",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
        }
      ]
    },
    {
      "title": "Error Rate",
      "targets": [
        {
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
        }
      ]
    },
    {
      "title": "Active Workers",
      "targets": [
        {
          "expr": "gunicorn_workers"
        }
      ]
    }
  ]
}
```

#### パネル3: ビジネスメトリクス

```json
{
  "title": "Business Metrics",
  "panels": [
    {
      "title": "Active Users (24h)",
      "targets": [
        {
          "expr": "count(count_over_time(user_login_total[24h]))"
        }
      ]
    },
    {
      "title": "Knowledge Created (24h)",
      "targets": [
        {
          "expr": "increase(knowledge_created_total[24h])"
        }
      ]
    },
    {
      "title": "Searches Performed (1h)",
      "targets": [
        {
          "expr": "increase(search_queries_total[1h])"
        }
      ]
    }
  ]
}
```

---

### シンプルな監視スクリプト（cron実行）

```bash
#!/bin/bash
# /usr/local/bin/simple_monitoring.sh

LOG_FILE="/var/log/mirai-knowledge-monitoring.log"
ALERT_EMAIL="admin@example.com"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    local subject="$1"
    local body="$2"
    echo "$body" | mail -s "$subject" "$ALERT_EMAIL"
    /usr/local/bin/notify_slack.sh critical "$subject: $body"
}

# CPU監視
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print int(100 - $1)}')
if [ $CPU_USAGE -gt 90 ]; then
    alert "Critical: High CPU Usage" "CPU usage is ${CPU_USAGE}%"
elif [ $CPU_USAGE -gt 70 ]; then
    log "WARNING: CPU usage is ${CPU_USAGE}%"
fi

# メモリ監視
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEM_USAGE -gt 90 ]; then
    alert "Critical: High Memory Usage" "Memory usage is ${MEM_USAGE}%"
elif [ $MEM_USAGE -gt 80 ]; then
    log "WARNING: Memory usage is ${MEM_USAGE}%"
fi

# ディスク監視
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    alert "Critical: High Disk Usage" "Disk usage is ${DISK_USAGE}%"
elif [ $DISK_USAGE -gt 80 ]; then
    log "WARNING: Disk usage is ${DISK_USAGE}%"
fi

# プロセス監視
if ! pgrep -f gunicorn > /dev/null; then
    alert "Critical: Gunicorn Not Running" "Gunicorn process not found. Attempting restart..."
    cd /path/to/backend && ./run_production.sh start
fi

# ヘルスチェック
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health)
if [ "$HEALTH_STATUS" != "200" ]; then
    alert "Critical: Health Check Failed" "Health endpoint returned status: ${HEALTH_STATUS}"
fi

log "Monitoring check completed - CPU: ${CPU_USAGE}%, MEM: ${MEM_USAGE}%, DISK: ${DISK_USAGE}%"
```

**cron設定:**

```bash
# crontab -e

# 5分ごとに監視実行
*/5 * * * * /usr/local/bin/simple_monitoring.sh

# 毎日深夜にログローテーション確認
0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/mirai-knowledge-system
```

---

## 参考資料

- [障害対応手順書](./06_Incident-Response-Procedures.md)
- [バックアップ・リストア詳細手順](./08_Backup-Restore-Procedures.md)
- [SLA・SLO](./03_SLA・SLO(SLA-SLO).md)

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-27 | 1.0 | 初版作成 - 詳細な監視設定ガイドを追加 | Codex |
