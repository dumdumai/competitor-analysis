# Competitor Analysis System - Makefile

.PHONY: help install build up down restart logs clean test

# Default target
help:
	@echo "Competitor Analysis System - Available Commands:"
	@echo "================================================"
	@echo "  make install    - Install all dependencies"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View container logs"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make test       - Run tests"
	@echo "  make dev        - Start development environment"
	@echo "  make prod       - Start production environment"
	@echo "  make local      - Run backend locally with uvicorn"
	@echo "  make local-full - Run full stack locally (backend + frontend)"

# Install dependencies
install:
	@echo "Setting up Python 3.12 virtual environment..."
	python3.12 -m venv venv || python3 -m venv venv
	@echo "Installing backend dependencies..."
	source venv/bin/activate && pip install --upgrade pip && pip install -r backend/requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Dependencies installed successfully!"

# Build Docker images
build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "Build complete!"

# Start services
up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

# Stop services
down:
	@echo "Stopping services..."
	docker-compose down
	@echo "Services stopped!"

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart
	@echo "Services restarted!"

# View logs
logs:
	docker-compose logs -f

# View specific service logs
logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-mongodb:
	docker-compose logs -f mongodb

logs-redis:
	docker-compose logs -f redis

# Clean up
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	@echo "Cleanup complete!"

# Run tests
test:
	@echo "Running backend tests..."
	source venv/bin/activate && cd backend && pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test

# Development environment
dev:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production environment
prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Database operations
db-shell:
	docker exec -it competitor-analysis-mongodb mongosh

redis-cli:
	docker exec -it competitor-analysis-redis redis-cli

# Check service health
health-check:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health || echo "Backend is not responding"
	@curl -s http://localhost:3000 || echo "Frontend is not responding"

# Local development (backend only)
local:
	@echo "Starting backend locally..."
	source venv/bin/activate && python run.py

# Local development (full stack)
local-full: 
	@echo "Starting full stack locally..."
	@echo "Starting databases with Docker..."
	docker-compose up -d mongodb redis
	@echo "Starting backend locally..."
	source venv/bin/activate && python run.py &
	@echo "Starting frontend..."
	cd frontend && npm start

# Initialize project
init:
	@echo "Initializing project..."
	cp backend/.env.example backend/.env
	@echo "Please add your API keys to backend/.env"
	make install
	make build
	@echo "Project initialized! Run 'make up' to start."