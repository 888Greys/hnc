# HNC Legal Questionnaire - Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- 4GB+ RAM available
- 10GB+ disk space

### 1. Clone and Setup
```bash
git clone <repository-url>
cd HNC
chmod +x deploy.sh
./deploy.sh setup
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
nano .env
```

### 3. Start Services
```bash
# Development mode
./deploy.sh start dev

# Production mode
./deploy.sh start prod
```

## 📋 Production Deployment Checklist

### Security Configuration
- [ ] Update all default passwords in `.env`
- [ ] Generate strong SECRET_KEY and JWT_SECRET_KEY (32+ characters)
- [ ] Configure CEREBRAS_API_KEY for AI functionality
- [ ] Set up SSL certificates in `ssl/` directory
- [ ] Review and configure firewall rules
- [ ] Enable audit logging (`FEATURE_AUDIT_LOGGING=true`)

### Database Setup
- [ ] Verify PostgreSQL credentials
- [ ] Test database connectivity
- [ ] Run initial database migrations
- [ ] Set up database backup schedule
- [ ] Configure connection pooling

### Application Configuration
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper `API_BASE_URL` and `FRONTEND_URL`
- [ ] Set appropriate `LOG_LEVEL` (INFO or WARNING for production)
- [ ] Configure email settings for notifications
- [ ] Set file upload limits and allowed types

### Infrastructure
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up monitoring and health checks
- [ ] Configure log rotation
- [ ] Set up backup automation
- [ ] Test disaster recovery procedures

### Performance Optimization
- [ ] Configure worker processes based on CPU cores
- [ ] Set appropriate database connection pool size
- [ ] Configure Redis for caching
- [ ] Optimize Docker resource limits

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  Next.js App    │────│   FastAPI       │
│   (Port 80/443) │    │   (Port 3000)   │    │   (Port 8000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  PostgreSQL     │────│     Redis       │
                       │   (Port 5432)   │    │   (Port 6379)   │
                       └─────────────────┘    └─────────────────┘
```

## 🐳 Docker Services

### Core Services
- **hnc-frontend**: Next.js application (Port 3000)
- **hnc-backend**: FastAPI server (Port 8000)
- **hnc-database**: PostgreSQL 15 (Port 5432)
- **hnc-redis**: Redis cache (Port 6379)
- **nginx**: Reverse proxy (Port 80/443)

### Service Dependencies
```
nginx → hnc-frontend → hnc-backend → hnc-database
                    └─→ hnc-redis
```

## 🛠️ Management Commands

### Service Management
```bash
# Start services
./deploy.sh start [dev|prod]

# Stop services
./deploy.sh stop

# Restart services
./deploy.sh restart [dev|prod]

# View service status
./deploy.sh status

# View logs
./deploy.sh logs [service-name]
```

### Data Management
```bash
# Create backup
./deploy.sh backup

# Restore from backup
./deploy.sh restore <backup-directory>

# Run database migrations
./deploy.sh migrate

# Create database migration
./deploy.sh create-migration "Migration description"
```

### Maintenance
```bash
# Update services
./deploy.sh update

# Clean unused resources
./deploy.sh clean

# View export history
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/export/history

# Cleanup expired exports
curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/export/cleanup
```

## 🔍 Monitoring & Health Checks

### Service URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Health Check Commands
```bash
# Check all services
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test frontend health
curl http://localhost:3000

# Check database connectivity
docker-compose exec hnc-database pg_isready -U hnc_user

# Check Redis connectivity
docker-compose exec hnc-redis redis-cli ping
```

## 📊 Performance Tuning

### Recommended Resources
- **Small Deployment**: 2 CPU, 4GB RAM, 20GB storage
- **Medium Deployment**: 4 CPU, 8GB RAM, 50GB storage
- **Large Deployment**: 8 CPU, 16GB RAM, 100GB storage

### Database Optimization
```sql
-- Monitor active connections
SELECT count(*) FROM pg_stat_activity;

-- Check database size
SELECT pg_size_pretty(pg_database_size('hnc_legal'));

-- Monitor slow queries
SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC;
```

### Redis Monitoring
```bash
# Monitor memory usage
docker-compose exec hnc-redis redis-cli info memory

# Monitor connected clients
docker-compose exec hnc-redis redis-cli info clients

# Check key statistics
docker-compose exec hnc-redis redis-cli info keyspace
```

## 🔐 Security Best Practices

### Environment Security
- Store sensitive variables in `.env` file (never commit to git)
- Use Docker secrets for production deployments
- Regularly rotate API keys and passwords
- Enable HTTPS in production with valid SSL certificates

### Application Security
- Implement proper CORS configuration
- Use strong password hashing (bcrypt with 12+ rounds)
- Set up rate limiting
- Enable audit logging for sensitive operations
- Validate all input data

### Network Security
- Use internal Docker networks
- Restrict database access to application containers only
- Configure firewall rules for external access
- Use reverse proxy for SSL termination

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check database status
docker-compose exec hnc-database pg_isready

# View database logs
docker-compose logs hnc-database

# Reset database (WARNING: This deletes all data)
docker-compose down -v
docker-compose up hnc-database
```

#### Frontend Build Errors
```bash
# Clear Node.js cache
docker-compose exec hnc-frontend npm cache clean --force

# Rebuild frontend
docker-compose build --no-cache hnc-frontend
```

#### API Connection Issues
```bash
# Check backend logs
docker-compose logs hnc-backend

# Test API directly
curl -H "Content-Type: application/json" http://localhost:8000/health

# Check environment variables
docker-compose exec hnc-backend env | grep API
```

#### SSL Certificate Issues
```bash
# Generate self-signed certificate for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem

# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout
```

### Log Analysis
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f hnc-backend

# Search for errors
docker-compose logs | grep -i error

# Export logs for analysis
docker-compose logs > logs_$(date +%Y%m%d_%H%M%S).txt
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Use load balancer for multiple frontend instances
- Implement database read replicas
- Scale Redis with clustering
- Use container orchestration (Kubernetes)

### Vertical Scaling
- Increase CPU and memory allocation
- Optimize database configuration
- Tune application worker processes
- Configure connection pooling

## 🔄 Backup & Recovery

### Automated Backups
The system includes automated backup functionality:
```bash
# Schedule in crontab
0 2 * * * /path/to/deploy.sh backup

# Backup retention is managed automatically
# Configure retention period in .env: BACKUP_RETENTION_DAYS=30
```

### Manual Backup
```bash
# Create immediate backup
./deploy.sh backup

# Backup specific components
docker-compose exec hnc-database pg_dump -U hnc_user hnc_legal > backup.sql
docker-compose exec hnc-redis redis-cli --rdb dump.rdb
```

### Disaster Recovery
```bash
# Full system restore
./deploy.sh stop
./deploy.sh restore /path/to/backup/directory
./deploy.sh start

# Database-only restore
docker-compose exec -T hnc-database psql -U hnc_user hnc_legal < backup.sql
```

## 📞 Support & Contact

### Resources
- **API Documentation**: http://localhost:8000/docs
- **System Logs**: Check `data/logs/` directory
- **Export Files**: Available at `data/exports/`
- **Backup Files**: Stored in `data/backups/`

### Maintenance Windows
- **Database Maintenance**: Sundays 2:00-4:00 AM
- **Application Updates**: Scheduled maintenance notifications
- **Security Updates**: Applied immediately for critical issues

---

**Note**: This deployment guide provides comprehensive instructions for setting up and managing the HNC Legal Questionnaire system. Always test deployments in a staging environment before applying to production.