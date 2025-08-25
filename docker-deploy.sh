#!/bin/bash
# HNC Legal Questionnaire - Docker Deployment Script
# This script handles complete Docker deployment with multiple deployment modes

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="hnc-legal"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  HNC Legal Questionnaire - Docker Deploy  ${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

setup_environment() {
    print_info "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example "$ENV_FILE"
            print_success "Created .env file from .env.example"
            print_warning "Please review and update .env file with your configuration"
        else
            print_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    else
        print_success "Environment file exists"
    fi
    
    # Create data directory
    mkdir -p data
    mkdir -p test_reports
    mkdir -p logs
    
    print_success "Environment setup completed"
}

build_images() {
    print_info "Building Docker images..."
    
    # Build all images
    docker-compose build --no-cache
    
    print_success "Docker images built successfully"
}

deploy_production() {
    print_info "Deploying in production mode..."
    
    # Stop any running containers
    docker-compose down --remove-orphans
    
    # Start services in production mode
    docker-compose --profile production up -d
    
    # Wait for services to be healthy
    wait_for_services
    
    print_success "Production deployment completed"
    show_service_urls
}

deploy_development() {
    print_info "Deploying in development mode..."
    
    # Stop any running containers
    docker-compose down --remove-orphans
    
    # Start services in development mode
    docker-compose --profile dev up -d
    
    # Wait for services to be healthy
    wait_for_services
    
    print_success "Development deployment completed"
    show_service_urls_dev
}

deploy_basic() {
    print_info "Deploying basic services (no nginx)..."
    
    # Stop any running containers
    docker-compose down --remove-orphans
    
    # Start basic services
    docker-compose up -d hnc-database hnc-redis hnc-backend hnc-frontend
    
    # Wait for services to be healthy
    wait_for_services
    
    print_success "Basic deployment completed"
    show_service_urls_basic
}

deploy_streamlit_only() {
    print_info "Deploying legacy Streamlit application only..."
    
    # Stop any running containers
    docker-compose down --remove-orphans
    
    # Build and run just the Streamlit container
    docker build -t hnc-streamlit .
    docker run -d \
        --name hnc-streamlit-app \
        -p 8501:8501 \
        -v "$(pwd)/data:/app/data" \
        --env-file "$ENV_FILE" \
        hnc-streamlit
    
    print_success "Streamlit-only deployment completed"
    print_info "Access the application at: http://localhost:8501"
}

wait_for_services() {
    print_info "Waiting for services to become healthy..."
    
    local max_attempts=60
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        local healthy_services=0
        local total_services=0
        
        # Check database
        if docker-compose ps hnc-database | grep -q "healthy"; then
            ((healthy_services++))
        fi
        ((total_services++))
        
        # Check redis
        if docker-compose ps hnc-redis | grep -q "healthy"; then
            ((healthy_services++))
        fi
        ((total_services++))
        
        # Check backend
        if docker-compose ps hnc-backend | grep -q "healthy" || docker-compose ps hnc-backend-dev | grep -q "healthy"; then
            ((healthy_services++))
        fi
        ((total_services++))
        
        # Check frontend
        if docker-compose ps hnc-frontend | grep -q "healthy" || docker-compose ps hnc-frontend-dev | grep -q "Up"; then
            ((healthy_services++))
        fi
        ((total_services++))
        
        if [[ $healthy_services -eq $total_services ]]; then
            print_success "All services are healthy"
            return 0
        fi
        
        ((attempt++))
        echo -n "."
        sleep 5
    done
    
    echo
    print_warning "Some services may not be fully healthy yet, but deployment continues"
}

show_service_urls() {
    echo
    print_info "Service URLs (Production mode):"
    echo "  📱 Frontend:     http://localhost"
    echo "  🔧 Backend API:  http://localhost/api"
    echo "  📊 Health:       http://localhost/health"
    echo "  📚 API Docs:     http://localhost/docs"
    echo "  🗄️  Database:     localhost:5432"
    echo "  🔴 Redis:        localhost:6379"
}

show_service_urls_basic() {
    echo
    print_info "Service URLs (Basic mode):"
    echo "  📱 Frontend:     http://localhost:3000"
    echo "  🔧 Backend API:  http://localhost:8000"
    echo "  📊 Health:       http://localhost:8000/health"
    echo "  📚 API Docs:     http://localhost:8000/docs"
    echo "  🗄️  Database:     localhost:5432"
    echo "  🔴 Redis:        localhost:6379"
}

show_service_urls_dev() {
    echo
    print_info "Service URLs (Development mode):"
    echo "  📱 Frontend:     http://localhost:3000 (with hot reload)"
    echo "  🔧 Backend API:  http://localhost:8000 (with auto-reload)"
    echo "  📊 Health:       http://localhost:8000/health"
    echo "  📚 API Docs:     http://localhost:8000/docs"
    echo "  🗄️  Database:     localhost:5432"
    echo "  🔴 Redis:        localhost:6379"
}

show_status() {
    print_info "Current service status:"
    docker-compose ps
}

stop_services() {
    print_info "Stopping all services..."
    docker-compose down --remove-orphans
    
    # Also stop Streamlit if running
    if docker ps -q -f name=hnc-streamlit-app &> /dev/null; then
        docker stop hnc-streamlit-app && docker rm hnc-streamlit-app
    fi
    
    print_success "All services stopped"
}

cleanup() {
    print_info "Cleaning up Docker resources..."
    
    # Stop services
    stop_services
    
    # Remove images
    docker-compose down --rmi all --volumes --remove-orphans
    
    # Clean up any remaining containers
    docker container prune -f
    docker image prune -f
    docker volume prune -f
    
    print_success "Cleanup completed"
}

run_tests() {
    print_info "Running system tests in Docker..."
    
    # Make sure services are running
    if ! docker-compose ps hnc-backend | grep -q "Up"; then
        print_error "Backend service is not running. Please deploy first."
        exit 1
    fi
    
    # Run tests inside the backend container
    docker-compose exec hnc-backend python -m pytest tests/ -v
    
    print_success "Tests completed"
}

backup_data() {
    print_info "Creating data backup..."
    
    local backup_name="hnc-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_dir="backups"
    
    mkdir -p "$backup_dir"
    
    # Backup data directory
    tar -czf "$backup_dir/${backup_name}-data.tar.gz" data/
    
    # Backup database if running
    if docker-compose ps hnc-database | grep -q "Up"; then
        docker-compose exec -T hnc-database pg_dump -U hnc_user hnc_legal > "$backup_dir/${backup_name}-database.sql"
    fi
    
    print_success "Backup created: $backup_dir/$backup_name"
}

show_logs() {
    local service="$1"
    
    if [[ -z "$service" ]]; then
        print_info "Showing logs for all services:"
        docker-compose logs -f --tail=100
    else
        print_info "Showing logs for $service:"
        docker-compose logs -f --tail=100 "$service"
    fi
}

show_help() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  production     Deploy in production mode (with nginx)"
    echo "  development    Deploy in development mode (with hot reload)"
    echo "  basic          Deploy basic services (no nginx)"
    echo "  streamlit      Deploy legacy Streamlit application only"
    echo "  build          Build Docker images"
    echo "  stop           Stop all services"
    echo "  restart        Restart all services"
    echo "  status         Show service status"
    echo "  logs [service] Show logs (optionally for specific service)"
    echo "  test           Run system tests"
    echo "  backup         Create data backup"
    echo "  cleanup        Stop services and clean up resources"
    echo "  help           Show this help message"
    echo
    echo "Examples:"
    echo "  $0 production          # Deploy for production"
    echo "  $0 development         # Deploy for development"
    echo "  $0 logs hnc-backend    # Show backend logs"
    echo "  $0 backup              # Create backup"
}

# Main script logic
main() {
    print_header
    
    local command="${1:-help}"
    
    case "$command" in
        "production")
            check_prerequisites
            setup_environment
            build_images
            deploy_production
            ;;
        "development"|"dev")
            check_prerequisites
            setup_environment
            build_images
            deploy_development
            ;;
        "basic")
            check_prerequisites
            setup_environment
            build_images
            deploy_basic
            ;;
        "streamlit")
            check_prerequisites
            setup_environment
            deploy_streamlit_only
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            deploy_basic
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "test")
            run_tests
            ;;
        "backup")
            backup_data
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"