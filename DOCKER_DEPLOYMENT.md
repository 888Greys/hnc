# Docker Deployment Guide for HNC Legal Questionnaire

## 🐳 Docker Setup Overview

This guide provides comprehensive instructions for deploying the HNC Legal Questionnaire prototype using Docker containers. The setup includes both development and production deployment options.

## 📋 Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository
- **2GB RAM**: Minimum system requirements
- **1GB Disk Space**: For images and data

### Install Docker (if not already installed)

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker
```

**Ubuntu/Debian:**
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd HNC
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```env
# Cerebras AI Configuration (Optional)
CEREBRAS_API_KEY=your_api_key_here

# Application Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### 3. Create Data Directory
```bash
mkdir -p data
chmod 755 data
```

### 4. Build and Run
```bash
# Development mode
docker-compose up --build

# Production mode (with nginx)
docker-compose --profile production up --build -d
```

## 🔧 Docker Commands Reference

### Building the Application
```bash
# Build the Docker image
docker build -t hnc-questionnaire .

# Build with custom tag
docker build -t hnc-questionnaire:v1.0 .
```

### Running Containers

**Development Mode:**
```bash
# Run with docker-compose (recommended)
docker-compose up

# Run with logs
docker-compose up --build

# Run in background
docker-compose up -d
```

**Direct Docker Run:**
```bash
# Run container directly
docker run -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env:ro \
  --name hnc-app \
  hnc-questionnaire
```

### Container Management
```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f hnc-questionnaire

# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart containers
docker-compose restart
```

## 🌐 Access the Application

- **Local Development**: http://localhost:8501
- **Production (with nginx)**: http://localhost or http://your-domain.com

## 📊 Monitoring and Health Checks

### Health Check Endpoint
```bash
# Check application health
curl http://localhost:8501/_stcore/health
```

### View Container Logs
```bash
# Real-time logs
docker-compose logs -f hnc-questionnaire

# Last 100 lines
docker-compose logs --tail=100 hnc-questionnaire
```

### Container Statistics
```bash
# View resource usage
docker stats hnc-legal-questionnaire
```

## 🔒 Production Deployment

### 1. Security Considerations
```bash
# Use secrets for API keys
echo "your_api_key" | docker secret create cerebras_api_key -

# Run with read-only filesystem
docker run --read-only -v /tmp \
  -v $(pwd)/data:/app/data \
  hnc-questionnaire
```

### 2. SSL/TLS Setup
```bash
# Create SSL directory
mkdir ssl

# Add your certificates
cp your-cert.crt ssl/
cp your-private.key ssl/

# Update docker-compose.yml nginx volumes
```

### 3. Nginx Configuration
Create `nginx.conf` for production:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream streamlit {
        server hnc-questionnaire:8501;
    }

    server {
        listen 80;
        server_name your-domain.com;
        
        location / {
            proxy_pass http://streamlit;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 💾 Data Persistence

### Client Data Storage
- Client data is stored in `/app/data/client_data.json`
- Mounted as volume: `./data:/app/data`
- Ensure proper permissions: `chmod 755 data/`

### Backup Data
```bash
# Create backup
docker-compose exec hnc-questionnaire cp /app/data/client_data.json /app/data/backup_$(date +%Y%m%d).json

# Restore from backup
docker-compose exec hnc-questionnaire cp /app/data/backup_20240101.json /app/data/client_data.json
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find process using port 8501
lsof -i :8501

# Kill process
kill -9 <PID>
```

**Permission Denied (data directory):**
```bash
# Fix permissions
sudo chown -R $(id -u):$(id -g) data/
chmod 755 data/
```

**Container Won't Start:**
```bash
# Check logs
docker-compose logs hnc-questionnaire

# Debug container
docker-compose run --rm hnc-questionnaire bash
```

**Environment Variables Not Loaded:**
```bash
# Verify .env file exists
ls -la .env

# Check environment in container
docker-compose exec hnc-questionnaire env | grep CEREBRAS
```

### Performance Optimization

**Reduce Image Size:**
```bash
# Use multi-stage builds (already implemented)
# Remove unnecessary packages
# Use .dockerignore (already included)
```

**Improve Startup Time:**
```bash
# Pre-built base images
# Optimize dependency installation order
# Use Docker layer caching
```

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Cleaning Up
```bash
# Remove unused images
docker image prune

# Remove all stopped containers
docker container prune

# Remove unused volumes
docker volume prune

# Complete cleanup
docker system prune -a
```

## 📈 Scaling and Load Balancing

### Multiple Instances
```yaml
# In docker-compose.yml
services:
  hnc-questionnaire:
    # ... existing config
    deploy:
      replicas: 3
    scale: 3
```

### Load Balancer Configuration
```nginx
upstream streamlit_backend {
    server hnc-questionnaire_1:8501;
    server hnc-questionnaire_2:8501;
    server hnc-questionnaire_3:8501;
}
```

## 🆘 Support and Documentation

- **Container Logs**: `docker-compose logs -f`
- **Health Check**: `curl http://localhost:8501/_stcore/health`
- **Resource Usage**: `docker stats`
- **Application Status**: Check Streamlit health endpoint

For additional support, refer to:
- [Docker Documentation](https://docs.docker.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)