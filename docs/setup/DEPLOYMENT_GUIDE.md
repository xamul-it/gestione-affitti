# Gestione Affitti - Deployment Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-28
**Target Environments:** Staging, Production

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Environment Setup](#environment-setup)
4. [Database Deployment](#database-deployment)
5. [Backend Deployment](#backend-deployment)
6. [Frontend Deployment](#frontend-deployment)
7. [Nginx Configuration](#nginx-configuration)
8. [SSL/TLS Setup](#ssltls-setup)
9. [Monitoring & Logging](#monitoring--logging)
10. [Backup Strategy](#backup-strategy)
11. [Rollback Procedures](#rollback-procedures)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

**Minimum (Staging):**
- CPU: 2 cores
- RAM: 4 GB
- Storage: 20 GB SSD
- Network: 100 Mbps

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8+ GB
- Storage: 50+ GB SSD
- Network: 1 Gbps
- Load Balancer (optional but recommended)

### Software Requirements

**Operating System:**
- Ubuntu 22.04 LTS (recommended)
- Debian 11+
- CentOS 8+
- RHEL 8+

**Required Software:**
```bash
# System packages
- Python 3.10+
- PostgreSQL 14+
- Nginx 1.18+
- Node.js 18+ (for frontend build)
- npm 9+
- Git
- certbot (for SSL)

# Python packages
- pip
- virtualenv or venv

# Optional
- Docker & Docker Compose
- Redis (for future caching)
```

### Access Requirements
- SSH access to server
- sudo/root privileges
- Domain name (for production)
- SSL certificate (Let's Encrypt recommended)
- PostgreSQL admin credentials

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Internet / Users                      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │   Load Balancer      │ (Optional)
           │   (nginx/HAProxy)    │
           └──────────┬───────────┘
                      │
           ┌──────────┴───────────┐
           │                      │
           ▼                      ▼
  ┌─────────────────┐   ┌─────────────────┐
  │  Nginx (SSL)    │   │  Nginx (SSL)    │
  │  Reverse Proxy  │   │  Reverse Proxy  │
  └────────┬────────┘   └────────┬────────┘
           │                      │
           ▼                      ▼
  ┌─────────────────┐   ┌─────────────────┐
  │  Frontend       │   │  Frontend       │
  │  (Static Files) │   │  (Static Files) │
  └─────────────────┘   └─────────────────┘
           │
           │ API Requests
           ▼
  ┌─────────────────┐   ┌─────────────────┐
  │  Backend API    │   │  Backend API    │
  │  (Gunicorn/     │   │  (Gunicorn/     │
  │   Uvicorn)      │   │   Uvicorn)      │
  └────────┬────────┘   └────────┬────────┘
           │                      │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │  PostgreSQL Database │
           │  (Primary + Replica) │
           └──────────────────────┘
```

---

## Environment Setup

### 1. Create Deployment User

```bash
# Create dedicated user for the application
sudo adduser --system --group --home /opt/gestione-affitti gestione-affitti

# Create directory structure
sudo mkdir -p /opt/gestione-affitti/{backend,frontend,logs,backups}
sudo chown -R gestione-affitti:gestione-affitti /opt/gestione-affitti
```

### 2. Clone Repository

```bash
# Switch to deployment user
sudo su - gestione-affitti

# Clone repository
cd /opt/gestione-affitti
git clone https://github.com/your-org/gestione-affitti.git app
cd app

# Checkout production branch
git checkout production  # or main/master
```

### 3. Environment Configuration

#### Backend Environment (.env)

```bash
# Create backend .env file
cd /opt/gestione-affitti/app/backend
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://gestione_affitti:STRONG_PASSWORD@localhost:5432/gestione_affitti_prod

# Security
SECRET_KEY=GENERATE_SECURE_RANDOM_KEY_HERE_64_CHARS_MIN

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Gestione Affitti
VERSION=1.0.0

# CORS Configuration (Update with your domain)
BACKEND_CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Module System
MODULE_DIR=modules

# File Storage
UPLOAD_DIR=/opt/gestione-affitti/storage
MAX_UPLOAD_SIZE=10485760  # 10MB

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/gestione-affitti/logs/backend.log

# Environment
ENVIRONMENT=production
DEBUG=False
EOF

# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))" >> .env.secret
# Copy the generated key to SECRET_KEY in .env

# Secure the file
chmod 600 .env
```

#### Frontend Environment

```bash
# Create frontend .env file
cd /opt/gestione-affitti/app/frontend
cat > .env.production << 'EOF'
# API Configuration
VITE_API_BASE_URL=https://api.your-domain.com/api/v1

# Application
VITE_APP_NAME=Gestione Affitti
VITE_APP_VERSION=1.0.0
EOF
```

---

## Database Deployment

### 1. Install PostgreSQL

```bash
# Install PostgreSQL 14
sudo apt update
sudo apt install -y postgresql-14 postgresql-contrib-14

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User

```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
psql << 'EOF'
-- Create user
CREATE USER gestione_affitti WITH PASSWORD 'STRONG_PASSWORD_HERE';

-- Create database
CREATE DATABASE gestione_affitti_prod OWNER gestione_affitti;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE gestione_affitti_prod TO gestione_affitti;

-- Connect to database and set schema permissions
\c gestione_affitti_prod
GRANT ALL ON SCHEMA public TO gestione_affitti;

-- Exit
\q
EOF

# Return to deployment user
exit
```

### 3. Configure PostgreSQL

```bash
# Edit postgresql.conf for production
sudo nano /etc/postgresql/14/main/postgresql.conf

# Recommended settings:
# max_connections = 100
# shared_buffers = 256MB
# effective_cache_size = 1GB
# maintenance_work_mem = 64MB
# checkpoint_completion_target = 0.9
# wal_buffers = 16MB
# default_statistics_target = 100
# random_page_cost = 1.1
# effective_io_concurrency = 200
# work_mem = 2621kB
# min_wal_size = 1GB
# max_wal_size = 4GB

# Configure authentication
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add line (after local all postgres):
# local   gestione_affitti_prod    gestione_affitti    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 4. Initialize Database Schema

```bash
# Switch to deployment user
sudo su - gestione-affitti
cd /opt/gestione-affitti/app/backend

# Activate virtual environment (will be created in next section)
source venv/bin/activate

# Run migrations or create tables
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Verify tables created
psql -U gestione_affitti -d gestione_affitti_prod -c "\dt"
```

---

## Backend Deployment

### 1. Install Python Dependencies

```bash
# As deployment user
cd /opt/gestione-affitti/app/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn uvicorn[standard]

# Deactivate
deactivate
```

### 2. Create Systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/gestione-affitti-backend.service
```

**Service file content:**
```ini
[Unit]
Description=Gestione Affitti Backend API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=gestione-affitti
Group=gestione-affitti
WorkingDirectory=/opt/gestione-affitti/app/backend

# Environment
Environment="PATH=/opt/gestione-affitti/app/backend/venv/bin"
EnvironmentFile=/opt/gestione-affitti/app/backend/.env

# Start command
ExecStart=/opt/gestione-affitti/app/backend/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --keepalive 5 \
    --log-level info \
    --access-logfile /opt/gestione-affitti/logs/access.log \
    --error-logfile /opt/gestione-affitti/logs/error.log \
    app.main:app

# Restart policy
Restart=always
RestartSec=5

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/gestione-affitti/logs /opt/gestione-affitti/storage

[Install]
WantedBy=multi-user.target
```

### 3. Start Backend Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable gestione-affitti-backend

# Start service
sudo systemctl start gestione-affitti-backend

# Check status
sudo systemctl status gestione-affitti-backend

# View logs
sudo journalctl -u gestione-affitti-backend -f
```

### 4. Verify Backend

```bash
# Test backend is running
curl http://127.0.0.1:8000/health

# Expected response:
# {"status":"ok"}

# Test API endpoint
curl http://127.0.0.1:8000/api/v1/modules/enabled

# Should return module list
```

---

## Frontend Deployment

### 1. Build Frontend

```bash
# As deployment user
cd /opt/gestione-affitti/app/frontend

# Install dependencies
npm ci --production=false

# Build for production
npm run build

# This creates /opt/gestione-affitti/app/frontend/dist/
```

### 2. Deploy Static Files

```bash
# Copy build to web root
sudo mkdir -p /var/www/gestione-affitti
sudo cp -r /opt/gestione-affitti/app/frontend/dist/* /var/www/gestione-affitti/
sudo chown -R www-data:www-data /var/www/gestione-affitti
```

### 3. Automatic Deployment Script

Create deployment script for future updates:

```bash
sudo nano /opt/gestione-affitti/deploy-frontend.sh
```

**Script content:**
```bash
#!/bin/bash
set -e

echo "Deploying frontend..."

# Navigate to frontend directory
cd /opt/gestione-affitti/app/frontend

# Pull latest code
git pull origin production

# Install dependencies
npm ci --production=false

# Build
npm run build

# Deploy
sudo rm -rf /var/www/gestione-affitti/*
sudo cp -r dist/* /var/www/gestione-affitti/
sudo chown -R www-data:www-data /var/www/gestione-affitti

echo "Frontend deployed successfully!"
```

```bash
# Make executable
chmod +x /opt/gestione-affitti/deploy-frontend.sh
```

---

## Nginx Configuration

### 1. Install Nginx

```bash
sudo apt install -y nginx
```

### 2. Configure Site

```bash
# Create nginx configuration
sudo nano /etc/nginx/sites-available/gestione-affitti
```

**Configuration content:**
```nginx
# Upstream backend servers
upstream backend {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    # Add more backend servers for load balancing:
    # server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Server - Frontend
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Root directory
    root /var/www/gestione-affitti;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml+rss;

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API docs
    location /docs {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA routing - serve index.html for all non-API routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Logging
    access_log /var/log/nginx/gestione-affitti-access.log;
    error_log /var/log/nginx/gestione-affitti-error.log;
}
```

### 3. Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/gestione-affitti /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## SSL/TLS Setup

### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Create webroot directory
sudo mkdir -p /var/www/certbot

# Obtain certificate
sudo certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d your-domain.com \
    -d www.your-domain.com

# Update nginx configuration with certificate paths
# (Already included in nginx config above)

# Reload nginx
sudo systemctl reload nginx

# Test auto-renewal
sudo certbot renew --dry-run

# Certbot will auto-renew via systemd timer
sudo systemctl status certbot.timer
```

### Using Custom SSL Certificate

```bash
# Copy certificate files
sudo cp your-cert.crt /etc/ssl/certs/gestione-affitti.crt
sudo cp your-key.key /etc/ssl/private/gestione-affitti.key

# Set permissions
sudo chmod 644 /etc/ssl/certs/gestione-affitti.crt
sudo chmod 600 /etc/ssl/private/gestione-affitti.key

# Update nginx config ssl_certificate paths
# ssl_certificate /etc/ssl/certs/gestione-affitti.crt;
# ssl_certificate_key /etc/ssl/private/gestione-affitti.key;
```

---

## Monitoring & Logging

### 1. Application Logs

```bash
# Backend logs
sudo tail -f /opt/gestione-affitti/logs/access.log
sudo tail -f /opt/gestione-affitti/logs/error.log

# Systemd logs
sudo journalctl -u gestione-affitti-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/gestione-affitti-access.log
sudo tail -f /var/log/nginx/gestione-affitti-error.log
```

### 2. Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/gestione-affitti
```

**Content:**
```
/opt/gestione-affitti/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 gestione-affitti gestione-affitti
    sharedscripts
    postrotate
        systemctl reload gestione-affitti-backend > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/gestione-affitti-*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### 3. Monitoring with Systemd

```bash
# Check service status
sudo systemctl status gestione-affitti-backend

# View resource usage
systemd-cgtop

# Check failed services
systemctl --failed
```

### 4. Database Monitoring

```bash
# PostgreSQL activity
sudo su - postgres
psql -d gestione_affitti_prod << 'EOF'
SELECT * FROM pg_stat_activity;
SELECT * FROM pg_stat_database WHERE datname = 'gestione_affitti_prod';
EOF
```

---

## Backup Strategy

### 1. Database Backups

```bash
# Create backup script
sudo nano /opt/gestione-affitti/backup-database.sh
```

**Script content:**
```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/gestione-affitti/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="gestione_affitti_prod"
DB_USER="gestione_affitti"
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -U $DB_USER \
    -h localhost \
    -d $DB_NAME \
    --no-owner \
    --no-acl \
    | gzip > $BACKUP_FILE

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    echo "Backup created successfully: $BACKUP_FILE"

    # Delete old backups
    find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up (retention: $RETENTION_DAYS days)"
else
    echo "Backup failed!"
    exit 1
fi
```

```bash
# Make executable
chmod +x /opt/gestione-affitti/backup-database.sh

# Add to crontab
sudo crontab -e -u gestione-affitti

# Add line for daily backup at 2 AM:
# 0 2 * * * /opt/gestione-affitti/backup-database.sh >> /opt/gestione-affitti/logs/backup.log 2>&1
```

### 2. File Storage Backups

```bash
# Backup uploaded files
sudo rsync -av --delete \
    /opt/gestione-affitti/storage/ \
    /opt/gestione-affitti/backups/storage_$(date +%Y%m%d)/
```

### 3. Restore Procedures

**Restore database:**
```bash
# Stop backend
sudo systemctl stop gestione-affitti-backend

# Restore from backup
PGPASSWORD="$DB_PASSWORD" gunzip -c /opt/gestione-affitti/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
    psql -U gestione_affitti -d gestione_affitti_prod

# Start backend
sudo systemctl start gestione-affitti-backend
```

---

## Rollback Procedures

### Application Rollback

```bash
# 1. Stop services
sudo systemctl stop gestione-affitti-backend

# 2. Switch to previous version
cd /opt/gestione-affitti/app
git checkout <previous-commit-hash>

# 3. Rebuild frontend
cd frontend
npm ci
npm run build
sudo cp -r dist/* /var/www/gestione-affitti/

# 4. Restart backend
cd ../backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl start gestione-affitti-backend

# 5. Verify
curl http://localhost:8000/health
```

### Database Rollback

See [Restore Procedures](#3-restore-procedures) above

---

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
sudo journalctl -u gestione-affitti-backend -n 50

# Common issues:
# 1. Database connection error - check DATABASE_URL in .env
# 2. Port already in use - check: sudo lsof -i :8000
# 3. Permission issues - check file ownership
# 4. Module import errors - reinstall dependencies
```

### Frontend Not Loading

```bash
# Check nginx error log
sudo tail -f /var/log/nginx/gestione-affitti-error.log

# Common issues:
# 1. API base URL incorrect - check VITE_API_BASE_URL
# 2. CORS errors - check BACKEND_CORS_ORIGINS
# 3. 404 on routes - check nginx try_files configuration
```

### Database Connection Issues

```bash
# Test connection
psql -U gestione_affitti -d gestione_affitti_prod -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql

# Check pg_hba.conf authentication
sudo cat /etc/postgresql/14/main/pg_hba.conf
```

### Performance Issues

```bash
# Check system resources
htop
free -h
df -h

# Check backend workers
ps aux | grep gunicorn

# Increase workers if needed (edit systemd service)
# Recommendation: (2 x CPU cores) + 1
```

---

## Post-Deployment Checklist

- [ ] Backend service running and accessible
- [ ] Frontend deployed and loading
- [ ] SSL certificate installed and valid
- [ ] Database backups configured
- [ ] Log rotation configured
- [ ] Monitoring setup complete
- [ ] DNS records configured
- [ ] Firewall rules configured
- [ ] Module system functional
- [ ] API documentation accessible
- [ ] Test user accounts created
- [ ] Admin access configured
- [ ] Email notifications working (if applicable)
- [ ] Backup restoration tested
- [ ] Rollback procedure tested
- [ ] Team trained on deployment process

---

## Security Hardening

### Firewall Configuration

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL only from localhost (default)
# No rule needed - listens on localhost only

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Additional Security Measures

```bash
# Disable root SSH login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd

# Install fail2ban
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Keep system updated
sudo apt update && sudo apt upgrade -y
```

---

## Contacts & Support

**Technical Support:** support@your-company.com
**Emergency Contact:** +39 XXX XXXXXXX
**Documentation:** https://docs.your-domain.com

---

**End of Deployment Guide**

**Document Version:** 1.0.0
**Last Updated:** 2025-11-28
