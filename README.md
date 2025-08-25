# HNC Legal Questionnaire System

A comprehensive digital platform for legal estate planning, succession, and document generation services. Built with modern web technologies and AI-powered legal guidance.

## 🎯 Overview

The HNC Legal Questionnaire System is a full-stack application designed to streamline legal consultation processes, particularly in estate planning, succession, and legal document generation. The system provides:

- **Interactive Questionnaires**: Comprehensive forms for gathering client information
- **AI-Powered Legal Guidance**: Intelligent recommendations based on Kenyan law
- **Document Generation**: Automated creation of legal documents (wills, trusts, contracts)
- **Security & Encryption**: Enterprise-grade data protection for sensitive information
- **Professional Dashboard**: Tools for legal practitioners to manage clients and cases

## 🏗️ Architecture

### Frontend (Next.js 15.5.0)
- **Framework**: Next.js with TypeScript and App Router
- **UI Library**: Tailwind CSS for responsive design
- **Components**: Modern React components with form validation
- **State Management**: React Context API and local state

### Backend (FastAPI)
- **API Framework**: FastAPI with async support
- **Authentication**: JWT-based with role-based access control
- **Session Management**: Redis-backed session handling
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI Integration**: Cerebras AI SDK for legal recommendations

### Key Services
- **Kenya Law Database**: Comprehensive legal reference system
- **Document Template Engine**: Jinja2-based document generation
- **Encryption Service**: Multi-level data encryption for sensitive information
- **AI Prompt Engineering**: Advanced prompt system for legal guidance

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ and pip
- Node.js 18+ and npm
- Docker and Docker Compose (optional)
- PostgreSQL database
- Redis server

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd HNC
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run database migrations
   alembic upgrade head
   
   # Start the FastAPI server
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   
   # Start the Next.js development server
   npm run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 Documentation

### User Guides
- [User Manual](docs/user-manual.md) - Complete guide for end users
- [Legal Practitioner Guide](docs/practitioner-guide.md) - Guide for legal professionals
- [Admin Guide](docs/admin-guide.md) - System administration guide

### Technical Documentation
- [API Documentation](docs/api-documentation.md) - Complete API reference
- [Development Guide](docs/development-guide.md) - Developer setup and guidelines
- [Security Guide](docs/security-guide.md) - Security features and best practices
- [Deployment Guide](docs/deployment-guide.md) - Production deployment instructions

### Architecture Documentation
- [System Architecture](docs/architecture.md) - High-level system design
- [Database Schema](docs/database-schema.md) - Database design and relationships
- [AI Integration](docs/ai-integration.md) - AI services and prompt engineering

## 🔧 Features

### Core Functionality
- ✅ **Interactive Questionnaires**: Multi-step forms for client data collection
- ✅ **AI Legal Recommendations**: Intelligent suggestions based on client profile
- ✅ **Document Generation**: Automated creation of 8+ legal document types
- ✅ **Client Management**: Comprehensive client data management system
- ✅ **Data Security**: Multi-level encryption for sensitive information

### Legal Services
- ✅ **Estate Planning**: Wills, trusts, and succession planning
- ✅ **Business Succession**: Corporate succession and ownership transfer
- ✅ **Asset Declaration**: Comprehensive asset and liability documentation
- ✅ **Legal Opinions**: Professional legal analysis and recommendations
- ✅ **Kenya Law Integration**: Real legal references and statutory compliance

### System Features
- ✅ **Authentication & Authorization**: Role-based access control
- ✅ **Session Management**: Secure session handling with Redis
- ✅ **Data Export**: PDF and Excel report generation
- ✅ **Search & Retrieval**: Advanced client and case search
- ✅ **Audit Logging**: Comprehensive activity tracking

## 🛠️ Technology Stack

### Frontend Technologies
- **Next.js 15.5.0** - React framework with App Router
- **TypeScript** - Type-safe JavaScript development
- **Tailwind CSS** - Utility-first CSS framework
- **React Hook Form** - Form handling and validation
- **Axios** - HTTP client for API communication

### Backend Technologies
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Python SQL toolkit and ORM
- **PostgreSQL** - Relational database
- **Redis** - In-memory data store for sessions and caching
- **Alembic** - Database migration tool

### AI & Document Services
- **Cerebras AI SDK** - AI model integration
- **Jinja2** - Template engine for document generation
- **ReportLab** - PDF generation library
- **OpenPyXL** - Excel file manipulation

### Security & Infrastructure
- **Cryptography** - Advanced encryption library
- **JWT** - JSON Web Tokens for authentication
- **Docker** - Containerization platform
- **Nginx** - Web server and reverse proxy

## 📊 System Requirements

### Development Environment
- **CPU**: 2+ cores
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux

### Production Environment
- **CPU**: 4+ cores
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 100GB+ SSD
- **Database**: PostgreSQL 12+
- **Cache**: Redis 6+

## 🔒 Security Features

### Data Protection
- **Multi-Level Encryption**: AES-256-GCM with RSA for maximum security
- **Category-Based Security**: Different encryption levels for different data types
- **Key Management**: Secure key generation and rotation
- **Data Classification**: Automatic classification of sensitive information

### Access Control
- **Role-Based Permissions**: Granular permission system
- **Session Security**: Secure session management with Redis
- **JWT Authentication**: Token-based authentication
- **Activity Monitoring**: Comprehensive audit logging

### Compliance
- **Data Privacy**: GDPR-compliant data handling
- **Legal Standards**: Adherence to legal industry standards
- **Encryption Standards**: Industry-standard encryption algorithms
- **Audit Trail**: Complete activity tracking and logging

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Component and service testing
- **Integration Tests**: API and database testing
- **Security Tests**: Encryption and authentication testing
- **Performance Tests**: Load and stress testing

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test

# Test specific services
python test_encryption.py
python test_document_templates.py
python test_kenya_law.py
python test_ai_prompt.py
```

## 📈 Performance

### System Metrics
- **Response Time**: < 200ms for most API calls
- **Concurrent Users**: Supports 100+ concurrent users
- **Document Generation**: < 5 seconds for complex documents
- **Database Performance**: Optimized queries with indexing

### Optimization Features
- **Caching**: Redis-based caching for frequent queries
- **Compression**: Gzip compression for API responses
- **CDN Ready**: Static asset optimization
- **Database Indexing**: Optimized database queries

## 🔄 Maintenance

### Regular Tasks
- **Database Backups**: Automated daily backups
- **Log Rotation**: Automatic log management
- **Security Updates**: Regular dependency updates
- **Performance Monitoring**: System health checks

### Health Checks
```bash
# Check system status
curl http://localhost:8000/health

# Check database connection
curl http://localhost:8000/health/db

# Check Redis connection
curl http://localhost:8000/health/redis
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Run the test suite
6. Submit a pull request

### Code Standards
- **Python**: PEP 8 compliance
- **TypeScript**: ESLint and Prettier formatting
- **Git**: Conventional commit messages
- **Documentation**: Update docs for new features

## 📞 Support

### Getting Help
- **Documentation**: Check the docs/ directory
- **Issues**: Report bugs and feature requests
- **Community**: Join our discussion forums
- **Professional Support**: Contact for enterprise support

### Troubleshooting
- [Common Issues](docs/troubleshooting.md)
- [Error Codes](docs/error-codes.md)
- [Performance Tuning](docs/performance-tuning.md)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- Kenya Law database integration
- Cerebras AI for intelligent recommendations
- Open source community for excellent libraries
- Legal professionals for domain expertise

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Maintainer**: HNC Development Team