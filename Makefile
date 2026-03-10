.PHONY: up down restart test lint start stop logs clean build

# Default target
all: up

# Start all services
up:
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Stop all services
down:
	docker-compose down

# Restart all services
restart: down up

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && python -m pytest -v
	@echo "Running frontend lint..."
	cd frontend && npm run lint

# Run lint
lint:
	@echo "Running backend lint..."
	cd backend && python -m ruff check app/
	@echo "Running frontend lint..."
	cd frontend && npm run lint

# Start services (alias for up)
start: up

# Stop services (alias for down)
stop: down

# View logs
logs:
	docker-compose logs -f

# View logs for specific service
logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-db:
	docker-compose logs -f db

# Clean up containers and volumes
clean:
	docker-compose down -v
	@echo "Cleaned up containers and volumes"

# Build images (without starting)
build:
	docker-compose build

# Rebuild images
rebuild:
	docker-compose build --no-cache

# Run backend tests only
test-backend:
	cd backend && python -m pytest -v

# Run frontend tests/lint only
test-frontend:
	cd frontend && npm run lint

# Database migration
migrate:
	cd backend && alembic upgrade head

# Database reset
reset-db:
	docker-compose down -v
	docker-compose up -d
	sleep 5
	docker-compose exec backend alembic upgrade head
