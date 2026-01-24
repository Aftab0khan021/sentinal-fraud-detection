# Production Deployment Runbook

## Pre-Deployment Checklist

### Environment Setup
- [ ] Set all environment variables in `.env` file
- [ ] Generate strong JWT secret keys (min 32 characters)
- [ ] Configure Redis password
- [ ] Set Grafana admin password
- [ ] Configure PagerDuty service key
- [ ] Configure Slack webhook URLs
- [ ] Obtain SSL/TLS certificates (replace self-signed)
- [ ] Configure domain DNS records

### Infrastructure
- [ ] Provision servers/VMs (11 CPU cores, 25GB RAM minimum)
- [ ] Install Docker 20.10+ and Docker Compose 2.0+
- [ ] Configure firewall rules (ports 80, 443, 9090, 3001, 16686)
- [ ] Set up backup storage for Redis data
- [ ] Configure log rotation
- [ ] Set up monitoring alerts

### Security
- [ ] Review and update CORS allowed origins
- [ ] Enable HTTPS enforcement
- [ ] Configure rate limiting thresholds
- [ ] Review authentication settings
- [ ] Scan for vulnerabilities (`docker scan`)
- [ ] Review security headers

---

## Deployment Steps

### 1. Clone Repository
```bash
git clone https://github.com/your-org/sentinal-fraud-detection.git
cd sentinal-fraud-detection
```

### 2. Configure Environment
```bash
# Copy environment template
cp python/.env.example python/.env

# Edit environment variables
nano python/.env

# Required variables:
# - JWT_SECRET_KEY
# - JWT_REFRESH_SECRET_KEY
# - REDIS_PASSWORD
# - GRAFANA_ADMIN_PASSWORD
# - PAGERDUTY_SERVICE_KEY
# - SLACK_WEBHOOK_URL
```

### 3. Build Images
```bash
# Build all services
docker-compose build

# Verify images
docker images | grep sentinal
```

### 4. Start Services
```bash
# Start infrastructure first (Redis, Prometheus, Grafana)
docker-compose up -d redis-master redis-replica-1 redis-replica-2
docker-compose up -d redis-sentinel-1 redis-sentinel-2 redis-sentinel-3
docker-compose up -d prometheus alertmanager grafana jaeger

# Wait for services to be healthy
docker-compose ps

# Start API instances
docker-compose up -d api-1 api-2 api-3

# Start load balancer
docker-compose up -d nginx

# Start frontend
docker-compose up -d frontend
```

### 5. Verify Deployment
```bash
# Check all services are running
docker-compose ps

# Check health endpoints
curl https://localhost/health
curl https://localhost/health/ready
curl https://localhost/health/live

# Check each API instance
curl http://localhost:8000/health  # Won't work - behind LB
docker-compose exec api-1 curl http://localhost:8000/health
docker-compose exec api-2 curl http://localhost:8000/health
docker-compose exec api-3 curl http://localhost:8000/health

# Check Redis Sentinel
docker-compose exec redis-sentinel-1 redis-cli -p 26379 sentinel master mymaster

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana
open http://localhost:3001  # Login with configured credentials
```

### 6. Smoke Tests
```bash
# Test authentication
curl -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@sentinal.ai","password":"SecurePass123!"}'

# Test fraud detection (with token)
TOKEN="<access_token_from_login>"
curl -X POST https://localhost/api/analyze/77 \
  -H "Authorization: Bearer $TOKEN"

# Test rate limiting
for i in {1..15}; do
  curl -X POST https://localhost/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test","password":"test"}'
done
# Should see 429 Too Many Requests after 10 requests

# Test load balancing
for i in {1..10}; do
  curl https://localhost/health | jq .instance_id
done
# Should see different instance IDs (api-1, api-2, api-3)
```

---

## Post-Deployment Validation

### Monitoring Setup
1. **Grafana Dashboards**
   - Open http://localhost:3001
   - Verify all dashboards load
   - Check data is flowing from Prometheus

2. **Jaeger Tracing**
   - Open http://localhost:16686
   - Generate test traffic
   - Verify traces appear in UI

3. **Prometheus Metrics**
   - Open http://localhost:9090
   - Check all targets are UP
   - Verify metrics are being scraped

4. **AlertManager**
   - Open http://localhost:9093
   - Verify configuration loaded
   - Test alert by triggering a rule

### Performance Baseline
```bash
# Run load test to establish baseline
k6 run tests/load/baseline.js

# Expected results:
# - P95 latency: < 200ms
# - Error rate: < 1%
# - Throughput: > 100 req/s
```

---

## Rollback Procedures

### Quick Rollback (Docker Compose)
```bash
# Stop all services
docker-compose down

# Checkout previous version
git checkout <previous-tag>

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify rollback
curl https://localhost/health
```

### Gradual Rollback (Rolling)
```bash
# Stop one API instance at a time
docker-compose stop api-3
docker-compose rm -f api-3

# Rebuild with previous version
git checkout <previous-tag>
docker-compose build api

# Start with previous version
docker-compose up -d api-3

# Verify instance is healthy
docker-compose exec api-3 curl http://localhost:8000/health

# Repeat for api-2 and api-1
```

### Database Rollback (Redis)
```bash
# Redis data is persisted in volumes
# To rollback Redis data, restore from backup

# Stop Redis
docker-compose stop redis-master redis-replica-1 redis-replica-2

# Restore backup
docker run --rm -v sentinal-fraud-detection_redis-master-data:/data \
  -v /path/to/backup:/backup alpine \
  sh -c "cd /data && tar xzf /backup/redis-backup.tar.gz"

# Restart Redis
docker-compose up -d redis-master redis-replica-1 redis-replica-2
```

---

## Disaster Recovery

### Redis Failover
```bash
# Sentinel will automatically promote a replica
# To manually trigger failover:
docker-compose exec redis-sentinel-1 \
  redis-cli -p 26379 sentinel failover mymaster

# Verify new master
docker-compose exec redis-sentinel-1 \
  redis-cli -p 26379 sentinel master mymaster
```

### Complete System Failure
```bash
# 1. Stop all services
docker-compose down

# 2. Restore from backups
# - Redis data: /var/lib/redis/data
# - Grafana dashboards: /var/lib/grafana
# - Prometheus data: /var/lib/prometheus

# 3. Restart services
docker-compose up -d

# 4. Verify all services healthy
docker-compose ps
```

### Data Backup
```bash
# Backup Redis data
docker run --rm -v sentinal-fraud-detection_redis-master-data:/data \
  -v /backup:/backup alpine \
  tar czf /backup/redis-backup-$(date +%Y%m%d).tar.gz -C /data .

# Backup Grafana dashboards
docker run --rm -v sentinal-fraud-detection_grafana_data:/data \
  -v /backup:/backup alpine \
  tar czf /backup/grafana-backup-$(date +%Y%m%d).tar.gz -C /data .

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup-script.sh
```

---

## Scaling Procedures

### Horizontal Scaling (Add API Instance)
```bash
# Edit docker-compose.yml to add api-4
# Update nginx.conf to include api-4:8000

# Rebuild NGINX
docker-compose build nginx
docker-compose up -d nginx

# Start new API instance
docker-compose up -d api-4

# Verify load balancer sees new instance
curl https://localhost/health | jq .instance_id
```

### Vertical Scaling (Increase Resources)
```bash
# Edit docker-compose.yml to add resource limits
services:
  api-1:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

# Recreate services
docker-compose up -d --force-recreate api-1 api-2 api-3
```

### Redis Scaling
```bash
# Add more replicas for read scaling
# Edit docker-compose.yml to add redis-replica-3

docker-compose up -d redis-replica-3

# Update Sentinel configuration
docker-compose exec redis-sentinel-1 \
  redis-cli -p 26379 sentinel set mymaster parallel-syncs 2
```

---

## Troubleshooting Guide

### API Not Responding
```bash
# Check API logs
docker-compose logs -f api-1 api-2 api-3

# Check if instances are healthy
docker-compose ps

# Check NGINX logs
docker-compose logs -f nginx

# Common issues:
# - Redis connection failed: Check Redis is running
# - Model not loaded: Check data volume is mounted
# - High latency: Check CPU/memory usage
```

### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis-master

# Check Redis logs
docker-compose logs -f redis-master

# Test Redis connection
docker-compose exec redis-master redis-cli -a <password> ping

# Check Sentinel status
docker-compose exec redis-sentinel-1 \
  redis-cli -p 26379 sentinel master mymaster
```

### High Latency
```bash
# Check metrics in Grafana
open http://localhost:3001

# Check traces in Jaeger
open http://localhost:16686

# Check resource usage
docker stats

# Common causes:
# - Cache miss rate high: Check Redis
# - Model inference slow: Check CPU usage
# - Network latency: Check between services
```

### Alerts Not Firing
```bash
# Check AlertManager status
curl http://localhost:9093/api/v1/status

# Check Prometheus rules
curl http://localhost:9090/api/v1/rules

# Check AlertManager logs
docker-compose logs -f alertmanager

# Test alert manually
curl -X POST http://localhost:9090/api/v1/alerts \
  -d '[{"labels":{"alertname":"test","severity":"warning"}}]'
```

---

## Maintenance Windows

### Planned Maintenance
1. **Notify users** 24 hours in advance
2. **Schedule during low traffic** (typically 2-4 AM)
3. **Create backup** before changes
4. **Test in staging** first
5. **Have rollback plan** ready

### Zero-Downtime Updates
```bash
# Update one instance at a time
docker-compose stop api-3
docker-compose pull api
docker-compose up -d api-3

# Wait for health check to pass
sleep 30

# Repeat for other instances
docker-compose stop api-2
docker-compose up -d api-2
sleep 30

docker-compose stop api-1
docker-compose up -d api-1
```

---

## Security Incident Response

### Suspected Breach
1. **Isolate affected systems**
   ```bash
   docker-compose stop <affected-service>
   ```

2. **Preserve logs**
   ```bash
   docker-compose logs <service> > incident-logs.txt
   ```

3. **Rotate credentials**
   ```bash
   # Generate new JWT secrets
   # Update .env file
   # Restart services
   ```

4. **Notify security team** via Slack #sentinal-security

5. **Review access logs** in Grafana

6. **Update firewall rules** if needed

---

## Contacts

### On-Call Rotation
- **Primary**: Check PagerDuty schedule
- **Secondary**: Check PagerDuty schedule
- **Escalation**: security@sentinal.ai

### External Services
- **PagerDuty**: https://sentinal.pagerduty.com
- **Slack**: #sentinal-alerts, #sentinal-critical
- **Monitoring**: http://grafana.sentinal.ai

---

## Appendix

### Useful Commands
```bash
# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart api-1

# Check resource usage
docker stats

# Clean up old images
docker system prune -a

# Export metrics
curl http://localhost:9090/api/v1/query?query=up

# Check certificate expiry
echo | openssl s_client -connect localhost:443 2>/dev/null | \
  openssl x509 -noout -dates
```

### Configuration Files
- **Environment**: `python/.env`
- **NGINX**: `nginx/nginx.conf`
- **Prometheus**: `monitoring/prometheus.yml`
- **AlertManager**: `monitoring/alertmanager.yml`
- **Grafana**: `monitoring/dashboards/*.json`
- **Redis Sentinel**: `redis/sentinel.conf`
