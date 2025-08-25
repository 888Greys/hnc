#!/bin/bash

# HNC Legal Questionnaire Deployment Script
# This script helps manage the Docker multi-service setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install docker-compose and try again."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p data/{clients,backups,logs}
    mkdir -p ssl
    print_success "Directories created"
}

# Create .env file if it doesn't exist
create_env_file() {
    if [ ! -f .env ]; then
        print_info "Creating .env file..."
        cat > .env << EOF
# HNC Legal Questionnaire Environment Variables

# Database Configuration
DATABASE_URL=postgresql://hnc_user:hnc_password@hnc-database:5432/hnc_legal
POSTGRES_DB=hnc_legal
POSTGRES_USER=hnc_user
POSTGRES_PASSWORD=hnc_password

# Redis Configuration
REDIS_URL=redis://hnc-redis:6379/0

# API Configuration
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Security
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cerebras AI Configuration
CEREBRAS_API_KEY=your-cerebras-api-key-here

# Application Settings
DATA_DIR=/app/data
LOG_LEVEL=INFO
DEBUG=false

# SSL Configuration (for production)
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
EOF
        print_success ".env file created. Please update the values as needed."
        print_warning "Remember to set your CEREBRAS_API_KEY in the .env file!"
    else
        print_info ".env file already exists"
    fi
}

# Function to start services
start_services() {
    local profile=$1
    print_info "Starting HNC Legal services..."
    
    if [ "$profile" = "dev" ]; then
        print_info "Starting in development mode..."
        docker-compose --profile dev up -d
    elif [ "$profile" = "prod" ]; then
        print_info "Starting in production mode..."
        docker-compose --profile production up -d
    else
        print_info "Starting basic services..."
        docker-compose up -d hnc-database hnc-redis hnc-backend hnc-frontend
    fi
    
    print_success "Services started successfully!"
    print_info "Frontend: http://localhost:3000"
    print_info "Backend API: http://localhost:8000"
    print_info "API Documentation: http://localhost:8000/docs"
}

# Function to stop services
stop_services() {
    print_info "Stopping HNC Legal services..."
    docker-compose down
    print_success "Services stopped"
}

# Function to view logs
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Function to check service status
check_status() {
    print_info "Checking service status..."
    docker-compose ps
    echo
    print_info "Service health checks:"
    docker-compose exec hnc-backend curl -s http://localhost:8000/health || print_error "Backend health check failed"
    docker-compose exec hnc-frontend curl -s http://localhost:3000 > /dev/null || print_error "Frontend health check failed"
}

# Function to backup data
backup_data() {
    local backup_dir="data/backups/$(date +%Y%m%d_%H%M%S)"
    print_info "Creating backup in $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # Backup database
    docker-compose exec hnc-database pg_dump -U hnc_user hnc_legal > "$backup_dir/database.sql"
    
    # Backup client files
    cp -r data/clients "$backup_dir/" 2>/dev/null || true
    
    print_success "Backup created in $backup_dir"
}

# Function to restore data
restore_data() {
    local backup_dir=$1
    if [ -z "$backup_dir" ]; then
        print_error "Please specify backup directory"
        exit 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        print_error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    print_info "Restoring data from $backup_dir..."
    
    # Restore database
    if [ -f "$backup_dir/database.sql" ]; then
        docker-compose exec -T hnc-database psql -U hnc_user hnc_legal < "$backup_dir/database.sql"
        print_success "Database restored"
    fi
    
    # Restore client files
    if [ -d "$backup_dir/clients" ]; then
        cp -r "$backup_dir/clients" data/
        print_success "Client files restored"
    fi
}

# Function to update services
update_services() {
    print_info "Updating HNC Legal services..."
    
    # Pull latest images
    docker-compose pull
    
    # Rebuild and restart services
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    
    print_success "Services updated successfully"
}

# Function to run database migrations
run_migrations() {
    print_info "Running database migrations..."
    docker-compose exec hnc-backend alembic upgrade head
    print_success "Migrations completed"
}

# Function to create database migration
create_migration() {
    local message=$1
    if [ -z "$message" ]; then
        print_error "Please provide migration message"
        exit 1
    fi
    
    print_info "Creating migration: $message"
    docker-compose exec hnc-backend alembic revision --autogenerate -m "$message"
    print_success "Migration created"
}

# Function to show help
show_help() {
    echo "HNC Legal Questionnaire Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [dev|prod]    Start services (dev/prod mode optional)"
    echo "  stop               Stop all services"
    echo "  restart [dev|prod] Restart services"
    echo "  status             Show service status"
    echo "  logs [service]     View logs (all services or specific service)"
    echo "  backup             Create data backup"
    echo "  restore <dir>      Restore data from backup directory"
    echo "  update             Update and restart services"
    echo "  migrate            Run database migrations"
    echo "  create-migration   Create new database migration"
    echo "  setup              Initial setup (create directories, .env file)"
    echo "  clean              Clean up unused Docker resources"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup           # Initial setup"
    echo "  $0 start dev       # Start in development mode"
    echo "  $0 start prod      # Start in production mode"
    echo "  $0 logs backend    # View backend logs"
    echo "  $0 backup          # Create backup"
    echo "  $0 restore data/backups/20240115_143000  # Restore backup"
}

# Main script logic
main() {
    case $1 in
        "setup")
            check_docker
            check_docker_compose
            create_directories
            create_env_file
            print_success "Setup completed! You can now run: $0 start"
            ;;
        "start")
            check_docker
            check_docker_compose
            create_directories
            start_services $2
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            start_services $2
            ;;
        "status")
            check_status
            ;;
        "logs")
            view_logs $2
            ;;
        "backup")
            backup_data
            ;;
        "restore")
            restore_data $2
            ;;
        "update")
            update_services
            ;;
        "migrate")
            run_migrations
            ;;
        "create-migration")
            create_migration "$2"
            ;;
        "clean")
            print_info "Cleaning up Docker resources..."
            docker system prune -f
            docker volume prune -f
            print_success "Cleanup completed"
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"