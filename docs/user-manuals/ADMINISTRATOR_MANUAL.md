# Mirai Knowledge Systems - Administrator Manual

## Overview
This manual is designed for system administrators responsible for managing and maintaining the Mirai Knowledge Systems platform. Administrators have full access to all system features and are responsible for user management, system configuration, monitoring, and ensuring platform stability.

## Table of Contents
1. [System Overview](#system-overview)
2. [Administrator Responsibilities](#administrator-responsibilities)
3. [User Management](#user-management)
4. [System Configuration](#system-configuration)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Security Management](#security-management)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## System Overview

### Platform Architecture
Mirai Knowledge Systems is a web-based knowledge management platform for construction companies, built with:
- **Backend**: Flask (Python) with JWT authentication and RBAC
- **Frontend**: Static HTML/CSS/JavaScript with real-time updates via SocketIO
- **Database**: PostgreSQL (production) or JSON files (development)
- **Caching**: Redis for performance optimization
- **Monitoring**: Prometheus metrics and health checks

### Key Features for Administrators
- User account management and role assignment
- System configuration and environment management
- Access logging and audit trail monitoring
- Performance monitoring and optimization
- Backup and recovery operations
- Security policy management

## Administrator Responsibilities

### Daily Tasks
- Monitor system health and performance
- Review system logs for anomalies
- Manage user access requests
- Monitor storage usage and plan capacity
- Review security alerts and incidents

### Weekly Tasks
- Review user activity reports
- Update system documentation
- Check backup integrity
- Monitor system performance trends
- Review and update security policies

### Monthly Tasks
- Generate system usage reports
- Review and optimize system performance
- Plan system upgrades and maintenance windows
- Audit user access and permissions
- Update compliance documentation

## User Management

### Creating User Accounts

1. **Access User Management**
   - Log in with administrator credentials
   - Navigate to Admin Panel > User Management

2. **Create New User**
   ```bash
   # Via API
   curl -X POST http://localhost:5100/api/v1/admin/users \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "newuser",
       "password": "TempPass123!",
       "role": "construction_manager",
       "email": "newuser@company.com",
       "full_name": "New User"
     }'
   ```

3. **Assign Initial Password**
   - New users must change their password on first login
   - Temporary passwords should be communicated securely

### Managing User Roles

#### Available Roles and Permissions

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| `admin` | System Administrator | Full system access, user management, system configuration |
| `construction_manager` | Construction Manager | Create/edit knowledge, manage incidents, approve content |
| `quality_assurance` | Quality Assurance Officer | Review and approve content, manage regulations |
| `partner` | External Partner | Read-only access to approved content |

#### Changing User Roles

```bash
# Update user role via API
curl -X PUT http://localhost:5100/api/v1/admin/users/123/role \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "quality_assurance"}'
```

### User Deactivation and Deletion

1. **Temporary Deactivation**
   ```bash
   curl -X PUT http://localhost:5100/api/v1/admin/users/123/status \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{"status": "inactive"}'
   ```

2. **Permanent Deletion**
   - Only perform when legally required
   - Data will be anonymized, not deleted
   ```bash
   curl -X DELETE http://localhost:5100/api/v1/admin/users/123 \
     -H "Authorization: Bearer <admin_token>"
   ```

### Bulk User Operations

For large organizations, use the bulk import feature:

```bash
# Bulk user import via CSV
curl -X POST http://localhost:5100/api/v1/admin/users/bulk-import \
  -H "Authorization: Bearer <admin_token>" \
  -F "file=@users.csv"
```

CSV Format:
```csv
username,email,full_name,role,department
yamada,yamada@company.com,山田太郎,construction_manager,第一工事部
suzuki,suzuki@company.com,鈴木花子,quality_assurance,品質管理部
```

## System Configuration

### Environment Variables

#### Core Configuration
```bash
# JWT Security
MKS_JWT_SECRET_KEY=your-secure-random-key-minimum-32-chars
MKS_JWT_ACCESS_TOKEN_EXPIRES=1h
MKS_JWT_REFRESH_TOKEN_EXPIRES=30d

# Database
MKS_USE_POSTGRESQL=true
DATABASE_URL=postgresql://user:pass@localhost:5432/mks_db

# Redis Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# Environment
MKS_ENV=production
MKS_DATA_DIR=/var/lib/mks/data
```

#### Security Configuration
```bash
# HTTPS and Security Headers
MKS_FORCE_HTTPS=true
MKS_TRUST_PROXY_HEADERS=true
MKS_HSTS_ENABLED=true
MKS_HSTS_MAX_AGE=31536000
MKS_HSTS_INCLUDE_SUBDOMAINS=true

# Rate Limiting
MKS_RATE_LIMIT_ENABLED=true
MKS_RATE_LIMIT_REQUESTS_PER_MINUTE=1000
```

#### Monitoring Configuration
```bash
# Prometheus Metrics
MKS_METRICS_ENABLED=true
MKS_METRICS_PORT=9090

# Logging
MKS_LOG_LEVEL=INFO
MKS_LOG_FILE=/var/log/mks/application.log
MKS_AUDIT_LOG_ENABLED=true
```

### Database Configuration

#### PostgreSQL Setup
```bash
# Create database
createdb mks_db

# Create user
createuser mks_user --createdb --login
psql -c "ALTER USER mks_user PASSWORD 'secure_password';"

# Grant permissions
psql -c "GRANT ALL PRIVILEGES ON DATABASE mks_db TO mks_user;"
```

#### Connection Pooling
```python
# In production, configure connection pooling
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
SQLALCHEMY_POOL_TIMEOUT=30
```

### Redis Configuration

#### Production Redis Setup
```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru

# Enable Redis service
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

#### Redis Cluster (High Availability)
For production environments with high traffic:

```bash
# Redis Cluster configuration
redis-cli --cluster create 127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003 \
  127.0.0.1:7004 127.0.0.1:7005 127.0.0.1:7006 \
  --cluster-replicas 1
```

## Monitoring and Maintenance

### System Health Monitoring

#### Health Check Endpoints
```bash
# Overall system health
curl http://localhost:5100/api/v1/health

# Database health
curl http://localhost:5100/api/v1/health/db

# Prometheus metrics
curl http://localhost:5100/metrics
```

#### Key Metrics to Monitor

**System Metrics:**
- CPU usage (< 80% sustained)
- Memory usage (< 85% sustained)
- Disk space (> 20% free)
- Network I/O

**Application Metrics:**
- Response time (< 500ms average)
- Error rate (< 1%)
- Active users
- Database connection pool usage

**Business Metrics:**
- Knowledge creation rate
- User engagement (daily active users)
- Content approval backlog
- Incident reporting trends

### Log Management

#### Log Files Location
```bash
/var/log/mks/
├── application.log          # Main application logs
├── access.log              # HTTP access logs
├── audit.log               # Security/audit logs
├── error.log               # Error logs only
└── security.log            # Security events
```

#### Log Rotation Configuration
```bash
# Logrotate configuration (/etc/logrotate.d/mks)
/var/log/mks/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 0644 mks mks
    postrotate
        systemctl reload mks.service
    endscript
}
```

#### Log Analysis
```bash
# Search for errors in last hour
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" /var/log/mks/error.log

# Count HTTP status codes
awk '{print $9}' /var/log/mks/access.log | sort | uniq -c | sort -nr

# Monitor failed login attempts
grep "LOGIN_FAILED" /var/log/mks/security.log | tail -20
```

### Performance Optimization

#### Database Optimization

**Index Management:**
```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_knowledge_category ON knowledge(category);
CREATE INDEX CONCURRENTLY idx_knowledge_status ON knowledge(status);
CREATE INDEX CONCURRENTLY idx_knowledge_created_at ON knowledge(created_at);
```

**Query Optimization:**
```sql
-- Use EXPLAIN ANALYZE for query analysis
EXPLAIN ANALYZE
SELECT * FROM knowledge
WHERE category = '施工計画' AND status = 'approved'
ORDER BY created_at DESC
LIMIT 50;
```

#### Cache Optimization

**Redis Cache Configuration:**
```python
# Cache TTL settings
CACHE_TTL_KNOWLEDGE = 600      # 10 minutes
CACHE_TTL_SEARCH = 300         # 5 minutes
CACHE_TTL_USER_DATA = 3600     # 1 hour
CACHE_TTL_DASHBOARD = 1800     # 30 minutes
```

**Cache Monitoring:**
```bash
# Redis cache statistics
redis-cli info stats
redis-cli --stat

# Cache hit/miss ratio monitoring
redis-cli info commandstats | grep get
```

#### Application Performance Tuning

**Gunicorn Configuration (Production):**
```python
# gunicorn.conf.py
workers = (multiprocessing.cpu_count() * 2) + 1
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
```

**Memory Management:**
```python
# Memory profiling
from memory_profiler import profile

@profile
def expensive_function():
    # Monitor memory usage of critical functions
    pass
```

## Security Management

### Authentication and Authorization

#### JWT Token Management
```bash
# Check token expiration
curl -H "Authorization: Bearer <token>" \
  http://localhost:5100/api/v1/auth/me

# Force token refresh
curl -X POST http://localhost:5100/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

#### Multi-Factor Authentication (MFA)

**Enable MFA for Users:**
```bash
# Generate MFA secret for user
curl -X POST http://localhost:5100/api/v1/admin/users/123/mfa/setup \
  -H "Authorization: Bearer <admin_token>"

# Verify MFA setup
curl -X POST http://localhost:5100/api/v1/admin/users/123/mfa/verify \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
```

### Access Control and Auditing

#### Audit Logging
All administrative actions are automatically logged:

```bash
# View recent admin actions
tail -f /var/log/mks/audit.log

# Search for specific user actions
grep "user:admin" /var/log/mks/audit.log | tail -10
```

#### Permission Auditing
Regular permission audits should be performed:

```bash
# List all admin users
curl http://localhost:5100/api/v1/admin/users?role=admin \
  -H "Authorization: Bearer <admin_token>"

# Check user permissions
curl http://localhost:5100/api/v1/admin/users/123/permissions \
  -H "Authorization: Bearer <admin_token>"
```

### Security Incident Response

#### Security Event Monitoring
```bash
# Monitor security events
tail -f /var/log/mks/security.log

# Alert patterns to monitor
grep -E "(FAILED_LOGIN|UNAUTHORIZED|INJECTION)" /var/log/mks/security.log
```

#### Incident Response Procedure

1. **Detection**: Security monitoring alerts or log analysis
2. **Assessment**: Determine scope and impact
3. **Containment**: Isolate affected systems
4. **Recovery**: Restore from clean backups
5. **Lessons Learned**: Update security policies

### Data Protection

#### Encryption at Rest
```bash
# Database encryption (PostgreSQL)
ALTER TABLE sensitive_data
ADD COLUMN encrypted_data bytea;

# File encryption for backups
openssl enc -aes-256-cbc -salt -in backup.sql -out backup.sql.enc
```

#### Data Sanitization
```python
# Input validation middleware
from bleach import clean

def sanitize_input(data):
    return clean(data, tags=[], strip=True)
```

## Backup and Recovery

### Automated Backup System

#### Database Backup
```bash
# PostgreSQL backup script
#!/bin/bash
BACKUP_DIR="/var/backups/mks"
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -U mks_user -h localhost mks_db > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete
```

#### Application Data Backup
```bash
# Backup application files and configurations
tar -czf /var/backups/mks/app_backup_$(date +%Y%m%d).tar.gz \
  /opt/mks/ \
  --exclude='*.log' \
  --exclude='*.tmp'
```

#### Redis Backup
```bash
# Redis data backup
redis-cli save
cp /var/lib/redis/dump.rdb /var/backups/mks/redis_backup_$(date +%Y%m%d).rdb
```

### Backup Verification

#### Integrity Checks
```bash
# Verify database backup
gzip -t /var/backups/mks/db_backup_20241201.sql.gz

# Test database restore
createdb test_restore
psql -d test_restore < /var/backups/mks/db_backup_20241201.sql
dropdb test_restore
```

#### Backup Monitoring
```bash
# Check backup success
ls -la /var/backups/mks/ | tail -5

# Monitor backup script execution
grep "BACKUP_COMPLETED" /var/log/mks/backup.log
```

### Disaster Recovery

#### Recovery Procedures

**Complete System Recovery:**
1. Restore from latest full backup
2. Verify data integrity
3. Update system configurations
4. Test application functionality
5. Notify users of system availability

**Database Recovery:**
```bash
# Stop application
sudo systemctl stop mks

# Restore database
psql -U mks_user -h localhost mks_db < /var/backups/mks/db_backup_20241201.sql

# Start application
sudo systemctl start mks
```

**Point-in-Time Recovery:**
```bash
# Restore to specific transaction
psql -c "SELECT pg_stop_backup();"
psql -c "SELECT pg_xlog_replay_resume();"
```

### Backup Scheduling

#### Cron Configuration
```bash
# Daily backup at 2 AM
0 2 * * * /opt/mks/scripts/backup.sh

# Weekly full backup on Sundays
0 3 * * 0 /opt/mks/scripts/backup-full.sh

# Monthly archive
0 4 1 * * /opt/mks/scripts/backup-archive.sh
```

## Troubleshooting

### Common Issues and Solutions

#### High Memory Usage
**Symptoms:** Application slowdown, OOM errors
**Solutions:**
```bash
# Check memory usage
ps aux --sort=-%mem | head -10

# Restart application
sudo systemctl restart mks

# Check for memory leaks
python -c "import tracemalloc; tracemalloc.start(); # Run problematic code"
```

#### Database Connection Issues
**Symptoms:** Timeout errors, connection refused
**Solutions:**
```bash
# Check database status
sudo systemctl status postgresql

# Check connection pool
psql -c "SELECT * FROM pg_stat_activity;"

# Reset connection pool
sudo systemctl restart mks
```

#### Slow Response Times
**Symptoms:** API calls taking >1 second
**Solutions:**
```bash
# Check system resources
top -b -n1 | head -20

# Analyze slow queries
psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;"

# Check cache hit rate
redis-cli info stats | grep keyspace
```

#### Authentication Failures
**Symptoms:** Login failures, token errors
**Solutions:**
```bash
# Check JWT configuration
grep JWT_SECRET /opt/mks/.env

# Verify user credentials
curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Check user status
curl http://localhost:5100/api/v1/admin/users?username=test \
  -H "Authorization: Bearer <admin_token>"
```

### Log Analysis for Troubleshooting

#### Error Pattern Recognition
```bash
# Find most common errors
grep "ERROR" /var/log/mks/application.log | \
  sed 's/.*ERROR//' | \
  sort | uniq -c | sort -nr | head -10

# Check recent errors
tail -50 /var/log/mks/error.log

# Correlate errors with user actions
grep "2024-12-01" /var/log/mks/application.log | grep -A5 -B5 "ERROR"
```

#### Performance Issue Investigation
```bash
# Find slow requests
awk '$NF > 1 {print $0}' /var/log/mks/access.log | tail -20

# Analyze response time distribution
awk '{print $NF}' /var/log/mks/access.log | \
  sort -n | \
  awk 'BEGIN {c=0; sum=0} {a[c++]=$1; sum+=$1} END {print "Min:", a[0], "Max:", a[c-1], "Avg:", sum/c}'
```

## Best Practices

### System Administration

#### Change Management
- Always test changes in development environment first
- Use feature flags for gradual rollouts
- Maintain rollback procedures
- Document all changes in changelog

#### Capacity Planning
- Monitor resource usage trends
- Plan for 30% growth in user base
- Implement auto-scaling where possible
- Regular capacity reviews

### Security Best Practices

#### Principle of Least Privilege
- Grant minimum required permissions
- Regular permission audits
- Remove inactive accounts promptly
- Use role-based access control

#### Security Monitoring
- Implement comprehensive logging
- Set up security alerts
- Regular security assessments
- Keep dependencies updated

### Performance Optimization

#### Proactive Monitoring
- Set up performance baselines
- Monitor key metrics continuously
- Implement performance budgets
- Regular performance audits

#### Continuous Improvement
- Analyze performance data regularly
- Optimize slow queries
- Implement caching strategies
- Upgrade infrastructure as needed

### Documentation and Communication

#### Knowledge Sharing
- Maintain up-to-date documentation
- Share incident reports and solutions
- Document troubleshooting procedures
- Create runbooks for common tasks

#### User Communication
- Notify users of planned maintenance
- Communicate system issues transparently
- Provide status updates during incidents
- Gather user feedback regularly

---

## Support and Resources

### Emergency Contacts
- **System Administrator**: admin@company.com
- **Database Administrator**: dba@company.com
- **Security Team**: security@company.com

### Documentation Resources
- [API Documentation](../API_Documentation.md)
- [Deployment Guide](../deployment/PRODUCTION_DEPLOYMENT.md)
- [Security Procedures](../security/SECURITY_PROCEDURES.md)
- [Troubleshooting Guide](../troubleshooting/TROUBLESHOOTING.md)

### External Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)

---

*This manual is maintained by the Mirai Knowledge Systems development team. Last updated: December 2025*