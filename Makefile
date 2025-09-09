# Makefile
.PHONY: help install test run clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install       Install dependencies"
	@echo "  test          Run tests"
	@echo "  run-http      Run HTTP server"
	@echo "  run-kafka     Run Kafka consumer"
	@echo "  run-celery    Run Celery worker"
	@echo "  run-combined  Run HTTP + Kafka"
	@echo "  lint          Run code linting"
	@echo "  format        Format code"
	@echo "  clean         Clean up"
	@echo "  docker-up     Start Docker stack"
	@echo "  docker-down   Stop Docker stack"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=.

run-http:
	python main.py --adapter http

run-kafka:
	python main.py --adapter kafka

run-celery:
	python main.py --adapter celery

run-combined:
	python main.py --adapter combined --combined-adapters http kafka

lint:
	mypy .
	black --check .
	isort --check-only .

format:
	black .
	isort .

clean:
	find . -type d -name "__pycache__" -delete
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf *.egg-info

docker-up:
	cd docker && docker-compose up -d

docker-down:
	cd docker && docker-compose down -v

docker-logs:
	cd docker && docker-compose logs -f

docker-rebuild:
	cd docker && docker-compose build --no-cache