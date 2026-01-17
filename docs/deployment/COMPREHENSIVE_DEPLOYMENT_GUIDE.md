# Mirai Knowledge Systems - Complete Deployment and Installation Guide

## Overview

This comprehensive guide covers all aspects of deploying and maintaining the Mirai Knowledge Systems platform, from initial installation to production operations.

## Table of Contents

1. [Quick Start Installation](#quick-start-installation)
2. [Development Environment Setup](#development-environment-setup)
3. [Production Deployment](#production-deployment)
4. [Database Setup and Migration](#database-setup-and-migration)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Systemd Service Management](#systemd-service-management)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup and Recovery](#backup-and-recovery)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start Installation

### Prerequisites

**System Requirements:**
- Ubuntu 20.04+ or Rocky Linux 8+
- 2 CPU cores minimum, 4 recommended
- 4GB RAM minimum, 8GB recommended
- 20GB free disk space
- Root or sudo access

**Required Software:**
- Python 3.8 or higher
- pip (Python package manager)
- Git
- Modern web browser

### One-Command Installation (Development)

For development or testing environments:

```bash
# Clone repository
git clone https://github.com/your-org/Mirai-Knowledge-Systems.git
cd Mirai-Knowledge-Systems

# Run automated setup
./scripts/setup-production-env.sh

# Start development server
./scripts/start_backend.sh
```

**What this script does:**
- Installs system dependencies
- Creates Python virtual environment
- Installs Python packages
- Sets up basic configuration
- Creates demo users
- Starts the development server

### Manual Installation Steps

If you prefer manual installation or need customization:

#### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git nginx postgresql postgresql-contrib
```

#### 2. Clone Repository
```bash
cd /opt
sudo git clone https://github.com/your-org/Mirai-Knowledge-Systems.git
sudo chown -R $USER:$USER Mirai-Knowledge-Systems
cd Mirai-Knowledge-Systems
```

#### 3. Python Environment Setup
```bash
# Create virtual environment
python3 -m venv venv_linux
source venv_linux/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

#### 4. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Generate secure JWT secret
python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env

# Edit configuration
nano .env
```

Required environment variables:
```bash
MKS_JWT_SECRET_KEY=your-generated-secret-key
MKS_ENV=development
MKS_DATA_DIR=/opt/Mirai-Knowledge-Systems/backend/data
CORS_ORIGINS=http://localhost:5100
```

#### 5. Database Setup (Optional for Development)
For development, the system uses JSON files by default. For production, see [Database Setup](#database-setup-and-migration).

#### 6. Start Application
```bash
# Development server
python app_v2.py

# Or use the startup script
./start_backend.sh
```

#### 7. Access Application
Open browser to: `http://localhost:5100/login.html`

**Default Demo Accounts:**
- **admin**: admin123 (Full access)
- **yamada**: yamada123 (Construction Manager)
- **partner**: partner123 (Read-only access)

---

## Development Environment Setup

### IDE Configuration

#### Visual Studio Code
Recommended extensions:
- Python
- Pylance
- Flask Snippets
- GitLens
- Prettier

VS Code settings for the project:
```json
{
  "python.defaultInterpreterPath": "./venv_linux/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

#### PyCharm
- Set project interpreter to `venv_linux/bin/python`
- Enable Flask support
- Configure run/debug configurations for `app_v2.py`

### Development Workflow

#### Code Quality Tools
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 backend/

# Run type checking
mypy backend/

# Format code
black backend/

# Run tests
pytest
```

#### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# Run tests
pytest

# Commit changes
git add .
git commit -m "Add new feature"

# Push and create PR
git push origin feature/new-feature
```

### Testing Setup

#### Unit Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=backend --cov-report=html tests/

# Run specific test file
pytest tests/test_api/test_auth.py
```

#### End-to-End Tests
```bash
# Install Playwright browsers
cd tests/e2e
npm install
npx playwright install

# Run E2E tests
npx playwright test
```

#### API Testing
```bash
# Using curl
curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Using HTTPie
http POST http://localhost:5100/api/v1/auth/login \
  username=admin password=admin123
```

---

## Production Deployment

### Production Architecture

```
Internet
    ↓
[Nginx Reverse Proxy - Port 80/443]
    ↓ SSL/TLS Termination
    ↓ Load Balancing (future)
    ↓
[Gunicorn WSGI Server - Port 8000]
    ↓ Process Management
    ↓ Static File Serving
    ↓
[Flask Application]
    ↓
[PostgreSQL Database - Port 5432]
    ↓ Connection Pooling
[Redis Cache (Optional) - Port 6379]
```

### Infrastructure Requirements

**Minimum Production Requirements:**
- 4 CPU cores
- 8GB RAM
- 100GB SSD storage
- Redundant power/networking
- SSL certificate
- Backup storage

**Recommended Production Setup:**
- 8 CPU cores
- 16GB RAM
- 200GB NVMe storage
- Load balancer
- Database read replicas
- CDN for static assets
- Monitoring stack (Prometheus/Grafana)

### Deployment Steps

#### 1. Server Preparation
```bash
# Update system and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server certbot git ufw

# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

#### 2. Application Deployment
```bash
# Clone repository
cd /opt
sudo git clone https://github.com/your-org/Mirai-Knowledge-Systems.git
sudo chown -R www-data:www-data Mirai-Knowledge-Systems

# Create virtual environment
cd Mirai-Knowledge-Systems
python3 -m venv venv_linux
source venv_linux/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

#### 3. Environment Configuration
```bash
# Production environment variables
cat > .env << EOF
MKS_JWT_SECRET_KEY=$(openssl rand -hex 32)
MKS_ENV=production
MKS_DATA_DIR=/var/lib/mks/data
MKS_FORCE_HTTPS=true
MKS_TRUST_PROXY_HEADERS=true
MKS_HSTS_ENABLED=true
DATABASE_URL=postgresql://mks_user:secure_password@localhost:5432/mks_prod
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=https://your-domain.com
EOF

# Secure permissions
chmod 600 .env
```

#### 4. Database Setup
See [Database Setup and Migration](#database-setup-and-migration) section.

#### 5. Web Server Configuration
See [SSL/TLS Configuration](#ssltls-configuration) section.

#### 6. Process Management
See [Systemd Service Management](#systemd-service-management) section.

#### 7. SSL Certificate Setup
See [SSL/TLS Configuration](#ssltls-configuration) section.

### Deployment Validation

#### Health Checks
```bash
# Application health
curl https://your-domain.com/api/v1/health

# Database connectivity
curl https://your-domain.com/api/v1/health/db

# SSL certificate validity
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null
```

#### Performance Testing
```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 https://your-domain.com/api/v1/knowledge

# Memory and CPU monitoring
top -p $(pgrep gunicorn)
free -h
```

#### Security Validation
```bash
# SSL configuration check
ssllabs-scan your-domain.com

# Security headers check
curl -I https://your-domain.com

# Open ports check
sudo netstat -tlnp | grep LISTEN
```

---

## Database Setup and Migration

### PostgreSQL Installation

#### Ubuntu/Debian
```bash
# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Configuration
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/16/main/postgresql.conf

# Recommended production settings
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### Database Creation

#### Create Production Database
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE USER mks_user WITH ENCRYPTED PASSWORD 'secure_password_here';
CREATE DATABASE mks_prod OWNER mks_user;
GRANT ALL PRIVILEGES ON DATABASE mks_prod TO mks_user;

# Set up extensions
\c mks_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
GRANT ALL ON SCHEMA public TO mks_user;
\q
```

#### Database Schema Setup
```bash
cd /opt/Mirai-Knowledge-Systems/backend

# Activate virtual environment
source ../venv_linux/bin/activate

# Create tables
python3 -c "
from database import engine, Base
Base.metadata.create_all(bind=engine)
print('Database schema created successfully')
"
```

### Data Migration

#### From JSON to PostgreSQL
```bash
# Run migration script
python3 migrate_json_to_postgres.py

# Expected output:
# ✅ 全データの移行が完了しました！
# 総移行件数: XXX件
```

#### Migration Validation
```bash
# Connect to database and verify data
sudo -u postgres psql -d mks_prod

# Check table counts
SELECT schemaname, tablename, n_tup_ins AS rows
FROM pg_stat_user_tables
ORDER BY n_tup_ins DESC;

# Verify data integrity
SELECT COUNT(*) FROM knowledge;
SELECT COUNT(*) FROM incidents;
SELECT COUNT(*) FROM consultations;
```

### Database Backup and Recovery

#### Automated Backup Setup
```bash
# Create backup script
cat > /opt/mks/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/mks"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="mks_prod"
DB_USER="mks_user"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
EOF

chmod +x /opt/mks/backup.sh
```

#### Backup Scheduling
```bash
# Daily backup at 2 AM
echo "0 2 * * * /opt/mks/backup.sh" | sudo crontab -

# Test backup
/opt/mks/backup.sh
```

#### Recovery Procedure
```bash
# Stop application
sudo systemctl stop mks.service

# Restore database
gunzip /var/backups/mks/db_backup_20241201.sql.gz
sudo -u postgres psql -d mks_prod < /var/backups/mks/db_backup_20241201.sql

# Start application
sudo systemctl start mks.service

# Verify restoration
curl https://your-domain.com/api/v1/health
```

---

## SSL/TLS Configuration

### Let's Encrypt Certificate Setup

#### Automated Setup
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test renewal
sudo certbot renew --dry-run
```

#### Manual Certificate Installation
```bash
# Create certificate directory
sudo mkdir -p /etc/letsencrypt/live/your-domain.com

# Place certificate files
sudo cp fullchain.pem /etc/letsencrypt/live/your-domain.com/
sudo cp privkey.pem /etc/letsencrypt/live/your-domain.com/

# Set proper permissions
sudo chmod 600 /etc/letsencrypt/live/your-domain.com/privkey.pem
sudo chmod 644 /etc/letsencrypt/live/your-domain.com/fullchain.pem
```

### Nginx SSL Configuration

#### SSL Configuration File
```nginx
# /etc/nginx/sites-available/mirai-knowledge-system
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Static files
    location /static/ {
        alias /opt/Mirai-Knowledge-Systems/webui/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # API responses should not be cached
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
```

#### Certificate Renewal Automation
```bash
# Setup renewal cron job
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Reload nginx after renewal (certbot post-hook)
sudo crontab -l | sed 's|certbot renew --quiet|certbot renew --quiet --post-hook "systemctl reload nginx"|' | sudo crontab -
```

### SSL Validation

#### Certificate Check
```bash
# Check certificate expiry
openssl s_client -connect your-domain.com:443 -servername your-domain.com < /dev/null 2>/dev/null | openssl x509 -noout -dates

# SSL Labs rating
curl -s "https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com" | grep -o 'rating.*'

# Certificate chain validation
openssl s_client -connect your-domain.com:443 -servername your-domain.com -showcerts < /dev/null
```

---

## Systemd Service Management

### Gunicorn Service Configuration

#### Create Systemd Service File
```bash
sudo nano /etc/systemd/system/mks.service
```

```ini
[Unit]
Description=Mirai Knowledge Systems
After=network.target postgresql.service redis-server.service
Requires=postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/Mirai-Knowledge-Systems/backend
Environment="PATH=/opt/Mirai-Knowledge-Systems/venv_linux/bin"
EnvironmentFile=/opt/Mirai-Knowledge-Systems/backend/.env
ExecStart=/opt/Mirai-Knowledge-Systems/venv_linux/bin/gunicorn --config /opt/Mirai-Knowledge-Systems/backend/gunicorn.conf.py app_v2:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
RestartSec=5
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Gunicorn Configuration File
```python
# /opt/Mirai-Knowledge-Systems/backend/gunicorn.conf.py
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
loglevel = "info"
accesslog = "/var/log/mks/gunicorn_access.log"
errorlog = "/var/log/mks/gunicorn_error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "mks_gunicorn"

# Server mechanics
pidfile = "/var/run/mks/gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None
```

### Service Management

#### Start and Enable Service
```bash
# Create log directory
sudo mkdir -p /var/log/mks
sudo chown www-data:www-data /var/log/mks

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl start mks.service
sudo systemctl enable mks.service

# Check status
sudo systemctl status mks.service
```

#### Service Monitoring
```bash
# View service logs
sudo journalctl -u mks.service -f

# Check if running
sudo systemctl is-active mks.service

# View resource usage
sudo systemctl show mks.service --property=MemoryCurrent,CPUUsageNSec
```

#### Service Maintenance
```bash
# Restart service
sudo systemctl restart mks.service

# Reload configuration (without restart)
sudo systemctl reload mks.service

# Stop service
sudo systemctl stop mks.service

# Disable service
sudo systemctl disable mks.service
```

---

## Monitoring Setup

### Prometheus Metrics

#### Application Metrics
The application exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Available metrics:
- `mks_http_requests_total`: Total HTTP requests
- `mks_http_request_duration_seconds`: Request latency
- `mks_database_connections`: Database connections
- `mks_active_users`: Active users
- `mks_knowledge_total`: Total knowledge entries

#### Prometheus Configuration
```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mks'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

#### Grafana Dashboard Setup
```bash
# Install Grafana
sudo apt install -y grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access Grafana at http://localhost:3000
# Default login: admin/admin
```

### System Monitoring

#### Key Metrics to Monitor
```bash
# CPU usage
top -bn1 | grep "Cpu(s)"

# Memory usage
free -h

# Disk usage
df -h /opt/Mirai-Knowledge-Systems

# Network connections
netstat -tlnp | grep :8000

# Application logs
tail -f /var/log/mks/application.log
```

#### Log Rotation Setup
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/mks

/var/log/mks/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 0644 www-data www-data
    postrotate
        systemctl reload mks.service
    endscript
}
```

### Alerting Setup

#### Prometheus Alert Rules
```yaml
# /etc/prometheus/alert_rules.yml
groups:
  - name: mks_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(mks_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(mks_http_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
```

#### Email Alerting
```yaml
# /etc/prometheus/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email-alerts'

receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'admin@your-domain.com'
```

---

## Performance Optimization

### Application Optimization

#### Database Query Optimization
```sql
-- Add indexes for performance
CREATE INDEX CONCURRENTLY idx_knowledge_category ON knowledge(category);
CREATE INDEX CONCURRENTLY idx_knowledge_status ON knowledge(status);
CREATE INDEX CONCURRENTLY idx_knowledge_created_at ON knowledge(created_at);
CREATE INDEX CONCURRENTLY idx_incidents_severity ON incidents(severity);
CREATE INDEX CONCURRENTLY idx_search_content ON knowledge USING gin(to_tsvector('japanese', content));
```

#### Caching Strategy
```python
# Redis cache configuration
CACHE_TTL_KNOWLEDGE = 600      # 10 minutes
CACHE_TTL_SEARCH = 300         # 5 minutes
CACHE_TTL_DASHBOARD = 1800     # 30 minutes
CACHE_TTL_USER_DATA = 3600     # 1 hour

# Cache invalidation strategy
def invalidate_cache(pattern):
    keys = redis_client.keys(f"mks:{pattern}:*")
    if keys:
        redis_client.delete(*keys)
```

#### Gunicorn Tuning
```python
# Production Gunicorn configuration
workers = (multiprocessing.cpu_count() * 2) + 1
worker_class = 'gevent'  # For I/O bound applications
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 10
```

### Infrastructure Optimization

#### Nginx Optimization
```nginx
# Performance optimizations
worker_processes auto;
worker_rlimit_nofile 65536;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Buffer sizes
    client_body_buffer_size 128k;
    client_max_body_size 50m;

    # Timeouts
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1024;
}
```

#### PostgreSQL Optimization
```sql
-- Performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = '100';

-- Connection pooling
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
```

### Monitoring Performance

#### Performance Benchmarks
```bash
# API response time testing
ab -n 1000 -c 10 https://your-domain.com/api/v1/knowledge

# Database query performance
EXPLAIN ANALYZE
SELECT * FROM knowledge
WHERE category = '施工計画'
ORDER BY created_at DESC
LIMIT 50;
```

#### Load Testing
```bash
# Install Locust
pip install locust

# Create load test
cat > locustfile.py << EOF
from locust import HttpUser, task

class MKSUser(HttpUser):
    @task
    def browse_knowledge(self):
        self.client.get("/api/v1/knowledge", headers={"Authorization": "Bearer <token>"})

    @task
    def search_content(self):
        self.client.get("/api/v1/search/unified?q=test", headers={"Authorization": "Bearer <token>"})
EOF

# Run load test
locust -f locustfile.py --host=https://your-domain.com
```

---

## Troubleshooting

### Common Issues and Solutions

#### Application Won't Start
```bash
# Check Python environment
source venv_linux/bin/activate
python --version

# Check dependencies
pip list | grep flask

# Check configuration
python -c "import os; print(os.environ.get('MKS_JWT_SECRET_KEY', 'NOT SET'))"

# Check logs
tail -f /var/log/mks/application.log
```

#### Database Connection Issues
```bash
# Test database connection
sudo -u postgres psql -d mks_prod -c "SELECT version();"

# Check PostgreSQL service
sudo systemctl status postgresql

# Check connection string
grep DATABASE_URL backend/.env

# Test from application
cd backend && python -c "from database import engine; print(engine.url)"
```

#### High Memory Usage
```bash
# Check memory usage
ps aux --sort=-%mem | head -10

# Check for memory leaks
python -c "
import tracemalloc
tracemalloc.start()
# Run problematic operation
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics('lineno')[:10]:
    print(stat)
"

# Restart application
sudo systemctl restart mks.service
```

#### SSL Certificate Issues
```bash
# Check certificate expiry
openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates

# Renew certificate
sudo certbot renew

# Check certificate files
ls -la /etc/letsencrypt/live/your-domain.com/

# Reload nginx
sudo systemctl reload nginx
```

#### Performance Issues
```bash
# Check system resources
top -b -n1 | head -20
iostat -x 1 5
free -h

# Check application metrics
curl http://localhost:8000/metrics | grep mks_http_request_duration_seconds

# Analyze slow queries
sudo -u postgres psql -d mks_prod -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;"

# Check cache hit rate
redis-cli info stats | grep keyspace_hits
```

### Log Analysis

#### Error Pattern Recognition
```bash
# Find most common errors
grep "ERROR" /var/log/mks/application.log | \
  sed 's/.*ERROR //' | \
  sort | uniq -c | sort -nr | head -10

# Check recent errors
tail -50 /var/log/mks/error.log

# Correlate errors with requests
grep "2024-12-01 10:" /var/log/mks/access.log | grep "500"
```

#### Performance Log Analysis
```bash
# Find slow requests
awk '$NF > 5 {print $0}' /var/log/mks/access.log | tail -20

# Calculate average response time
awk '{sum += $NF; count++} END {print "Average:", sum/count, "seconds"}' /var/log/mks/access.log
```

### Emergency Procedures

#### Application Down
1. Check service status: `sudo systemctl status mks.service`
2. Check logs: `sudo journalctl -u mks.service -n 50`
3. Restart service: `sudo systemctl restart mks.service`
4. If restart fails, check dependencies (PostgreSQL, Redis)
5. Contact development team if issue persists

#### Database Issues
1. Check PostgreSQL status: `sudo systemctl status postgresql`
2. Check disk space: `df -h`
3. Check database logs: `sudo tail -f /var/log/postgresql/postgresql-16-main.log`
4. Attempt restart: `sudo systemctl restart postgresql`
5. If corruption suspected, restore from backup

#### Security Incidents
1. Isolate affected systems
2. Change all passwords and API keys
3. Review access logs for suspicious activity
4. Update security policies
5. Report to appropriate authorities if required

### Getting Help

#### Support Resources
- **Documentation**: Check this guide and API documentation
- **Logs**: Application and system logs in `/var/log/mks/`
- **Metrics**: Prometheus metrics at `/metrics`
- **Health Checks**: `/api/v1/health` endpoints

#### Escalation Contacts
- **Development Team**: dev@company.com
- **System Administration**: admin@company.com
- **Security Team**: security@company.com
- **Management**: management@company.com

---

## Maintenance Checklists

### Daily Maintenance
- [ ] Check application health (`/api/v1/health`)
- [ ] Review error logs for anomalies
- [ ] Monitor system resources (CPU, memory, disk)
- [ ] Verify backup completion
- [ ] Check SSL certificate expiry

### Weekly Maintenance
- [ ] Review application metrics and trends
- [ ] Check database performance and connection counts
- [ ] Verify log rotation is working
- [ ] Test backup restoration procedures
- [ ] Review user access patterns

### Monthly Maintenance
- [ ] Update system packages and security patches
- [ ] Review and optimize database indexes
- [ ] Analyze application performance metrics
- [ ] Test disaster recovery procedures
- [ ] Review monitoring alerts and thresholds

### Quarterly Maintenance
- [ ] Major system updates and upgrades
- [ ] Security assessment and penetration testing
- [ ] Performance optimization and tuning
- [ ] Capacity planning and resource scaling
- [ ] Compliance audits and documentation updates

---

This comprehensive deployment and installation guide provides everything needed to successfully deploy, maintain, and troubleshoot the Mirai Knowledge Systems platform in both development and production environments.