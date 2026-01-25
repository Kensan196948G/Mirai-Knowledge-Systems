# Mirai Knowledge Systems - Monitoring and Alerting Setup Guide

## Overview

This guide provides comprehensive instructions for setting up monitoring and alerting for the Mirai Knowledge Systems platform. Effective monitoring ensures system reliability, performance, and quick issue resolution.

## Table of Contents

1. [Monitoring Architecture](#monitoring-architecture)
2. [Prometheus Setup](#prometheus-setup)
3. [Grafana Dashboard Configuration](#grafana-dashboard-configuration)
4. [Alert Manager Configuration](#alert-manager-configuration)
5. [Application Metrics](#application-metrics)
6. [System Monitoring](#system-monitoring)
7. [Log Aggregation](#log-aggregation)
8. [Alert Rules and Notifications](#alert-rules-and-notifications)
9. [Monitoring Best Practices](#monitoring-best-practices)
10. [Troubleshooting Monitoring](#troubleshooting-monitoring)

## Monitoring Architecture

### Components Overview

```
Application (Flask + Gunicorn)
    ↓ Exposes /metrics endpoint
    ↓ Prometheus metrics format
    ↓
Prometheus Server
    ↓ Scrapes metrics every 15s
    ↓ Stores time-series data
    ↓ Evaluates alert rules
    ↓ Sends alerts to Alertmanager
    ↓
Alertmanager
    ↓ Receives alerts from Prometheus
    ↓ Groups, inhibits, silences alerts
    ↓ Sends notifications (Email, Slack, etc.)
    ↓
Grafana
    ↓ Queries Prometheus for data
    ↓ Creates dashboards and visualizations
    ↓ Provides alerting capabilities
```

### Monitoring Stack Requirements

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert handling and notifications
- **Node Exporter**: System metrics collection
- **PostgreSQL Exporter**: Database metrics (optional)
- **Redis Exporter**: Cache metrics (optional)

## Prometheus Setup

### Installation

#### Ubuntu/Debian Installation
```bash
# Add Prometheus repository
sudo apt update
sudo apt install -y wget curl

# Download and install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvf prometheus-2.45.0.linux-amd64.tar.gz
sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus

# Create Prometheus user
sudo useradd --no-create-home --shell /bin/false prometheus
sudo chown -R prometheus:prometheus /opt/prometheus

# Create systemd service
sudo nano /etc/systemd/system/prometheus.service
```

#### Systemd Service Configuration
```ini
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/prometheus/prometheus \
  --config.file /opt/prometheus/prometheus.yml \
  --storage.tsdb.path /opt/prometheus/data \
  --web.console.templates=/opt/prometheus/consoles \
  --web.console.libraries=/opt/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
```

#### Service Management
```bash
# Enable and start Prometheus
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus

# Check status
sudo systemctl status prometheus

# View logs
sudo journalctl -u prometheus -f
```

### Prometheus Configuration

#### Main Configuration File
```yaml
# /opt/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'mks_application'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'postgres_exporter'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis_exporter'
    static_configs:
      - targets: ['localhost:9121']
```

#### Alert Rules Configuration
```yaml
# /opt/prometheus/alert_rules.yml
groups:
  - name: mks_application_alerts
    rules:
      - alert: MKSHighErrorRate
        expr: rate(mks_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
          service: mks
        annotations:
          summary: "High error rate in MKS application ({{ $value }} errors/minute)"
          description: "Error rate is {{ $value }} errors per minute, above threshold of 0.1"

      - alert: MKSHighResponseTime
        expr: histogram_quantile(0.95, rate(mks_http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
          service: mks
        annotations:
          summary: "High response time in MKS application ({{ $value }}s)"
          description: "95th percentile response time is {{ $value }}s, above threshold of 2s"

      - alert: MKSDown
        expr: up{job="mks_application"} == 0
        for: 1m
        labels:
          severity: critical
          service: mks
        annotations:
          summary: "MKS application is down"
          description: "MKS application has been down for more than 1 minute"

  - name: system_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}%, above threshold of 80%"

      - alert: HighMemoryUsage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}%, above threshold of 85%"

      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk space available is {{ $value }}%, below threshold of 10%"
```

### Additional Exporters Setup

#### Node Exporter (System Metrics)
```bash
# Download and install Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvf node_exporter-1.6.1.linux-amd64.tar.gz
sudo mv node_exporter-1.6.1.linux-amd64 /opt/node_exporter
sudo chown -R prometheus:prometheus /opt/node_exporter

# Create systemd service
sudo nano /etc/systemd/system/node_exporter.service
```

```ini
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/node_exporter/node_exporter

[Install]
WantedBy=multi-user.target
```

#### PostgreSQL Exporter (Database Metrics)
```bash
# Install PostgreSQL exporter
wget https://github.com/prometheus-community/postgres_exporter/releases/download/v0.12.1/postgres_exporter-0.12.1.linux-amd64.tar.gz
tar xvf postgres_exporter-0.12.1.linux-amd64.tar.gz
sudo mv postgres_exporter-0.12.1.linux-amd64 /opt/postgres_exporter

# Create database user for monitoring
sudo -u postgres psql
CREATE USER postgres_exporter PASSWORD 'secure_password';
GRANT pg_monitor TO postgres_exporter;
\q

# Create systemd service
sudo nano /etc/systemd/system/postgres_exporter.service
```

```ini
[Unit]
Description=PostgreSQL Exporter
Wants=network-online.target postgresql.service
After=network-online.target postgresql.service

[Service]
User=postgres
Group=postgres
Type=simple
Environment="DATA_SOURCE_NAME=postgresql://postgres_exporter:secure_password@localhost:5432/mks_prod?sslmode=disable"
ExecStart=/opt/postgres_exporter/postgres_exporter

[Install]
WantedBy=multi-user.target
```

#### Redis Exporter (Cache Metrics)
```bash
# Install Redis exporter
wget https://github.com/oliver006/redis_exporter/releases/download/v1.54.0/redis_exporter-v1.54.0.linux-amd64.tar.gz
tar xvf redis_exporter-v1.54.0.linux-amd64.tar.gz
sudo mv redis_exporter-v1.54.0.linux-amd64 /opt/redis_exporter

# Create systemd service
sudo nano /etc/systemd/system/redis_exporter.service
```

```ini
[Unit]
Description=Redis Exporter
Wants=network-online.target redis-server.service
After=network-online.target redis-server.service

[Service]
User=redis
Group=redis
Type=simple
ExecStart=/opt/redis_exporter/redis_exporter -redis.addr localhost:6379

[Install]
WantedBy=multi-user.target
```

## Grafana Dashboard Configuration

### Grafana Installation

#### Ubuntu/Debian Installation
```bash
# Add Grafana repository
sudo apt install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Install Grafana
sudo apt update
sudo apt install -y grafana

# Start and enable Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

#### Initial Configuration
```bash
# Access Grafana at http://localhost:3000
# Default login: admin/admin
# Change password on first login

# Add Prometheus as data source
# Configuration → Data Sources → Add data source → Prometheus
# URL: http://localhost:9090
# Access: Browser
```

### MKS Dashboard Creation

#### System Overview Dashboard
```json
{
  "dashboard": {
    "title": "MKS System Overview",
    "tags": ["mks", "system"],
    "timezone": "browser",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "legendFormat": "Memory Usage %"
          }
        ]
      },
      {
        "title": "Disk Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100",
            "legendFormat": "{{ mountpoint }} Usage %"
          }
        ]
      }
    ]
  }
}
```

#### Application Performance Dashboard
```json
{
  "dashboard": {
    "title": "MKS Application Performance",
    "tags": ["mks", "application"],
    "timezone": "browser",
    "panels": [
      {
        "title": "HTTP Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mks_http_requests_total[5m])",
            "legendFormat": "{{ method }} {{ endpoint }}"
          }
        ]
      },
      {
        "title": "Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(mks_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mks_errors_total[5m])",
            "legendFormat": "{{ type }} errors"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "graph",
        "targets": [
          {
            "expr": "mks_active_users",
            "legendFormat": "Active Users"
          }
        ]
      }
    ]
  }
}
```

#### Database Performance Dashboard
```json
{
  "dashboard": {
    "title": "MKS Database Performance",
    "tags": ["mks", "database"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "title": "Query Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mks_database_query_duration_seconds_sum[5m]) / rate(mks_database_query_duration_seconds_count[5m])",
            "legendFormat": "Average Query Time"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100",
            "legendFormat": "Redis Cache Hit Rate %"
          }
        ]
      }
    ]
  }
}
```

### Dashboard Import and Customization

#### Importing Dashboards
```bash
# Import dashboard JSON via Grafana UI
# Dashboard → Import → Upload JSON file

# Or use Grafana API
curl -X POST -H "Content-Type: application/json" \
  -d @dashboard.json \
  http://admin:password@localhost:3000/api/dashboards/db
```

#### Dashboard Best Practices
- Use consistent color schemes
- Include relevant time ranges
- Add descriptive panel titles
- Use appropriate graph types
- Include alert thresholds as reference lines
- Document dashboard purpose and metrics

## Alert Manager Configuration

### Alertmanager Installation

#### Installation Steps
```bash
# Download Alertmanager
wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz
tar xvf alertmanager-0.25.0.linux-amd64.tar.gz
sudo mv alertmanager-0.25.0.linux-amd64 /opt/alertmanager

# Create user and set permissions
sudo useradd --no-create-home --shell /bin/false alertmanager
sudo chown -R alertmanager:alertmanager /opt/alertmanager

# Create systemd service
sudo nano /etc/systemd/system/alertmanager.service
```

#### Systemd Service
```ini
[Unit]
Description=Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
ExecStart=/opt/alertmanager/alertmanager \
  --config.file=/opt/alertmanager/alertmanager.yml \
  --storage.path=/opt/alertmanager/data \
  --web.listen-address=:9093

[Install]
WantedBy=multi-user.target
```

### Alertmanager Configuration

#### Main Configuration File
```yaml
# /opt/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
  smtp_require_tls: true

templates:
  - '/opt/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'email-alerts'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      repeat_interval: 1h
    - match:
        service: mks
      receiver: 'mks-team'
      group_wait: 1m
      repeat_interval: 30m

receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'admin@your-domain.com'
        headers:
          Subject: '{{ .GroupLabels.alertname }} - {{ .GroupLabels.service }}'

  - name: 'critical-alerts'
    email_configs:
      - to: 'critical@your-domain.com'
        headers:
          Subject: 'CRITICAL: {{ .GroupLabels.alertname }} - {{ .GroupLabels.service }}'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#critical-alerts'
        title: 'CRITICAL ALERT'
        text: '{{ .CommonAnnotations.summary }}'

  - name: 'mks-team'
    email_configs:
      - to: 'mks-team@your-domain.com'
        headers:
          Subject: 'MKS Alert: {{ .GroupLabels.alertname }}'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#mks-alerts'
        title: 'MKS Alert'
        text: '{{ .CommonAnnotations.summary }}'
```

### Notification Templates

#### Email Template
```html
<!-- /opt/alertmanager/templates/email.tmpl -->
{{ define "email.default.html" }}
<!DOCTYPE html>
<html>
<head>
    <title>{{ .GroupLabels.alertname }}</title>
</head>
<body>
    <h1>{{ .GroupLabels.alertname }}</h1>
    <p><strong>Service:</strong> {{ .GroupLabels.service }}</p>
    <p><strong>Severity:</strong> {{ .GroupLabels.severity }}</p>
    <p><strong>Summary:</strong> {{ .CommonAnnotations.summary }}</p>
    <p><strong>Description:</strong> {{ .CommonAnnotations.description }}</p>

    <h2>Alerts</h2>
    <table border="1">
        <tr>
            <th>Alert</th>
            <th>Status</th>
            <th>Started</th>
        </tr>
        {{ range .Alerts }}
        <tr>
            <td>{{ .Annotations.summary }}</td>
            <td>{{ .Status }}</td>
            <td>{{ .StartsAt.Format "2006-01-02 15:04:05" }}</td>
        </tr>
        {{ end }}
    </table>

    <p><small>Generated by Alertmanager at {{ .ExternalURL }}</small></p>
</body>
</html>
{{ end }}
```

### Alertmanager Web UI

#### Accessing Alertmanager
- **URL**: http://localhost:9093
- **Features**:
  - View active alerts
  - Silence alerts
  - View alert history
  - Test notification channels

#### Managing Silences
```bash
# Silence all MKS alerts for maintenance
curl -X POST http://localhost:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "service", "value": "mks", "isRegex": false}
    ],
    "startsAt": "2024-12-01T10:00:00Z",
    "endsAt": "2024-12-01T12:00:00Z",
    "createdBy": "admin",
    "comment": "Scheduled maintenance"
  }'
```

## Application Metrics

### Built-in Prometheus Metrics

The MKS application exposes the following metrics at `/metrics`:

#### HTTP Request Metrics
```prometheus
# Total HTTP requests
mks_http_requests_total{method="GET", endpoint="/api/v1/knowledge", status="200"} 15420

# Request duration histogram
mks_http_request_duration_seconds_bucket{method="GET", endpoint="/api/v1/knowledge", le="0.1"} 12000
mks_http_request_duration_seconds_bucket{method="GET", endpoint="/api/v1/knowledge", le="0.5"} 14500
mks_http_request_duration_seconds_bucket{method="GET", endpoint="/api/v1/knowledge", le="1.0"} 15200
mks_http_request_duration_seconds_bucket{method="GET", endpoint="/api/v1/knowledge", le="+Inf"} 15420
mks_http_request_duration_seconds_sum{method="GET", endpoint="/api/v1/knowledge"} 2345.67
mks_http_request_duration_seconds_count{method="GET", endpoint="/api/v1/knowledge"} 15420
```

#### Error Metrics
```prometheus
# Total errors by type and endpoint
mks_errors_total{type="http_error", endpoint="/api/v1/knowledge"} 23
mks_errors_total{type="database_error", endpoint="/api/v1/knowledge"} 5
```

#### Business Metrics
```prometheus
# Active users
mks_active_users 12

# Total knowledge entries
mks_knowledge_total 1250

# Authentication attempts
mks_auth_attempts_total{status="success"} 15432
mks_auth_attempts_total{status="failure"} 23
```

### Custom Metrics Implementation

#### Adding Custom Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Custom business metrics
KNOWLEDGE_VIEWS = Counter(
    'mks_knowledge_views_total',
    'Total knowledge entry views',
    ['category', 'priority']
)

SEARCH_QUERIES = Counter(
    'mks_search_queries_total',
    'Total search queries',
    ['query_type', 'result_count']
)

USER_SESSIONS = Gauge(
    'mks_active_user_sessions',
    'Number of active user sessions'
)

# Usage in application code
@app.route('/api/v1/knowledge/<int:id>')
def get_knowledge(id):
    knowledge = get_knowledge_by_id(id)
    KNOWLEDGE_VIEWS.labels(
        category=knowledge.category,
        priority=knowledge.priority
    ).inc()
    return jsonify(knowledge)
```

### Metrics Validation

#### Checking Metrics Endpoint
```bash
# Verify metrics are exposed
curl http://localhost:8000/metrics | head -20

# Check specific metric
curl http://localhost:8000/metrics | grep mks_http_requests_total

# Validate metric format
curl http://localhost:8000/metrics | promtool check metrics
```

#### Prometheus Query Testing
```bash
# Test Prometheus queries
curl "http://localhost:9090/api/v1/query?query=mks_http_requests_total"

# Check metric ingestion
curl "http://localhost:9090/api/v1/query?query=up{job='mks_application'}"
```

## System Monitoring

### Key System Metrics

#### CPU Monitoring
```prometheus
# CPU usage percentage
100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# CPU usage by core
irate(node_cpu_seconds_total[5m]) * 100
```

#### Memory Monitoring
```prometheus
# Memory usage percentage
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Memory breakdown
node_memory_MemTotal_bytes
node_memory_MemFree_bytes
node_memory_Buffers_bytes
node_memory_Cached_bytes
```

#### Disk Monitoring
```prometheus
# Disk usage percentage
(1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100

# Disk I/O
rate(node_disk_io_time_seconds_total[5m])
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])
```

#### Network Monitoring
```prometheus
# Network traffic
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# Network errors
rate(node_network_receive_errs_total[5m])
rate(node_network_transmit_errs_total[5m])
```

### Process Monitoring

#### Gunicorn Process Monitoring
```bash
# Check Gunicorn processes
ps aux | grep gunicorn

# Monitor worker processes
sudo systemctl status mks.service

# Check process resource usage
pidof gunicorn | xargs ps -o pid,ppid,cmd,%cpu,%mem --pid
```

#### Database Process Monitoring
```bash
# PostgreSQL process status
sudo systemctl status postgresql

# Database connection count
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Database size monitoring
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('mks_prod'));"
```

## Log Aggregation

### Centralized Logging Setup

#### Using Promtail + Loki (Optional)
```yaml
# /opt/promtail/promtail.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /opt/promtail/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: mks_application
    static_configs:
      - targets:
          - localhost
        labels:
          job: mks_app
          __path__: /var/log/mks/application.log

  - job_name: mks_access
    static_configs:
      - targets:
          - localhost
        labels:
          job: mks_access
          __path__: /var/log/mks/access.log
```

### Log Monitoring Queries

#### Application Error Monitoring
```bash
# Count errors by hour
grep "ERROR" /var/log/mks/application.log | \
  awk '{print substr($1,1,13)}' | \
  sort | uniq -c

# Monitor error rate
tail -f /var/log/mks/application.log | \
  grep --line-buffered "ERROR" | \
  awk '{print strftime("%Y-%m-%d %H:%M:%S"), $0}'
```

#### Access Log Analysis
```bash
# Top requested endpoints
awk '{print $7}' /var/log/mks/access.log | \
  sort | uniq -c | sort -nr | head -10

# Response time analysis
awk '{print $NF}' /var/log/mks/access.log | \
  sort -n | \
  awk 'BEGIN {c=0; sum=0} {a[c++]=$1; sum+=$1} END {print "Min:", a[0], "Max:", a[c-1], "Avg:", sum/c}'

# HTTP status code distribution
awk '{print $9}' /var/log/mks/access.log | \
  sort | uniq -c | sort -nr
```

## Alert Rules and Notifications

### Alert Rule Best Practices

#### Alert Design Principles
- **Actionable**: Alerts should require human action
- **Informative**: Include context and impact assessment
- **Non-noisy**: Avoid false positives
- **Escalating**: Different severity levels for different responses

#### Alert Severity Levels
- **Critical**: Immediate action required, service down
- **Warning**: Action needed but not immediately critical
- **Info**: Awareness notifications, no immediate action

### Notification Channels

#### Email Notifications
- **Primary channel** for all alerts
- **Distribution lists** for different teams
- **Escalation paths** for critical alerts

#### Slack/Teams Integration
```bash
# Slack webhook integration
curl -X POST -H 'Content-type: application/json' \
  --data '{
    "channel": "#alerts",
    "username": "Alertmanager",
    "text": "CRITICAL: MKS Application Down",
    "icon_emoji": ":warning:"
  }' \
  https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

#### SMS/Pager Notifications
```yaml
# For critical alerts only
receivers:
  - name: 'critical-sms'
    webhook_configs:
      - url: 'https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT/Messages.json'
        http_config:
          basic_auth:
            username: 'your-account-sid'
            password: 'your-auth-token'
```

### Alert Response Procedures

#### Critical Alert Response
1. **Acknowledge** alert within 5 minutes
2. **Assess impact** and affected users
3. **Begin investigation** immediately
4. **Communicate** status to stakeholders
5. **Resolve or escalate** within SLA
6. **Post-mortem** analysis for root cause

#### Warning Alert Response
1. **Acknowledge** alert within 15 minutes
2. **Assess urgency** and potential impact
3. **Schedule investigation** during business hours
4. **Monitor trend** for escalation potential
5. **Document findings** and remediation

## Monitoring Best Practices

### Dashboard Organization

#### Dashboard Hierarchy
- **Executive Dashboard**: High-level business metrics
- **Operations Dashboard**: System health and performance
- **Application Dashboard**: Application-specific metrics
- **Infrastructure Dashboard**: Server and network metrics

#### Dashboard Maintenance
- Regular review and updates
- Remove unused or obsolete panels
- Document dashboard purpose and metrics
- Version control dashboard definitions

### Alert Management

#### Alert Review Process
- **Weekly review** of alert effectiveness
- **False positive analysis** and rule tuning
- **Alert fatigue prevention** through consolidation
- **Documentation updates** based on lessons learned

#### Alert Maintenance
- Regular testing of alert rules
- Update thresholds based on baseline changes
- Review and update contact information
- Test notification channels quarterly

### Performance Benchmarking

#### Establishing Baselines
```bash
# Capture normal operation metrics
# Run for 1 week during normal load
curl -s http://localhost:9090/api/v1/query_range \
  -d 'query=mks_http_request_duration_seconds{quantile="0.95"}' \
  -d 'start=2024-12-01T00:00:00Z' \
  -d 'end=2024-12-08T00:00:00Z' \
  -d 'step=3600s'
```

#### Performance Regression Detection
- Automated comparison against baselines
- Alert on significant deviations
- Trend analysis for gradual changes
- Capacity planning based on growth trends

### Monitoring Documentation

#### Runbooks and Procedures
- Document alert response procedures
- Maintain troubleshooting guides
- Update contact lists regularly
- Create escalation matrices

#### Knowledge Base
- Document common issues and resolutions
- Maintain incident history
- Share post-mortem reports
- Create training materials

## Troubleshooting Monitoring

### Common Monitoring Issues

#### Prometheus Issues

**Metrics not appearing:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify scrape configuration
curl http://localhost:9090/config

# Check application metrics endpoint
curl http://localhost:8000/metrics
```

**High cardinality issues:**
```bash
# Check metric cardinality
curl http://localhost:9090/api/v1/query?query=count({__name__=~".+"}) by (__name__)

# Identify high-cardinality metrics
curl 'http://localhost:9090/api/v1/series?match[]=mks_http_requests_total' | jq length
```

#### Grafana Issues

**Dashboard not loading:**
```bash
# Check Grafana logs
sudo journalctl -u grafana-server -f

# Verify data source connectivity
curl http://admin:password@localhost:3000/api/datasources

# Test query
curl "http://localhost:9090/api/v1/query?query=up"
```

#### Alertmanager Issues

**Alerts not firing:**
```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules

# Verify alertmanager configuration
curl http://localhost:9093/api/v1/status

# Check alertmanager logs
sudo journalctl -u alertmanager -f
```

### Monitoring Performance Issues

#### Prometheus Performance Tuning
```yaml
# prometheus.yml tuning
global:
  scrape_interval: 30s  # Increase from 15s for high metric volume
  evaluation_interval: 30s

# Storage tuning
storage:
  tsdb:
    retention.time: 30d
    wal_compression: true
```

#### Grafana Performance Optimization
```ini
# /etc/grafana/grafana.ini
[server]
root_url = https://grafana.your-domain.com

[database]
type = postgres
host = localhost:5432
name = grafana
user = grafana
password = secure_password

[alerting]
enabled = true
execute_alerts = true
```

### Monitoring Maintenance

#### Regular Maintenance Tasks
- **Daily**: Check alert status and system health
- **Weekly**: Review dashboard performance and alert effectiveness
- **Monthly**: Update monitoring configurations and thresholds
- **Quarterly**: Review and update alerting rules and dashboards

#### Backup and Recovery
```bash
# Backup Prometheus data
sudo systemctl stop prometheus
tar czf prometheus_backup_$(date +%Y%m%d).tar.gz /opt/prometheus/data/
sudo systemctl start prometheus

# Backup Grafana dashboards
curl http://localhost:3000/api/dashboards/home | jq -r '.dashboard' > grafana_dashboards.json
```

This comprehensive monitoring and alerting setup guide provides everything needed to implement robust monitoring for the Mirai Knowledge Systems platform, ensuring high availability and quick issue resolution.