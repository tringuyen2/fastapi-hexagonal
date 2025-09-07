.PHONY: help install test run clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  test        Run tests"
	@echo "  run         Run application (HTTP only)"
	@echo "  run-mongo   Run with MongoDB"
	@echo "  run-pg      Run with PostgreSQL"
	@echo "  run-full    Run with all adapters"
	@echo "  clean       Clean up"
	@echo "  docker-up   Start Docker stack"
	@echo "  docker-down Stop Docker stack"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=.

run:
	python main.py --adapters http --debug

run-mongo:
	python main.py --adapters http --database mongodb --debug

run-pg:
	python main.py --adapters http --database postgresql --debug

run-full:
	python main.py --adapters http celery kafka --database postgresql

clean:
	find . -type d -name "__pycache__" -delete
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf *.egg-info

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down -v

docker-logs:
	docker-compose logs -f app