# README.md content
readme_content = '''
# Event Manager - Hexagonal Architecture

A Python FastAPI-based event processing system built with Hexagonal Architecture principles, supporting multiple input adapters (HTTP, Kafka, Celery) with unified business logic.

## 🏗️ Architecture

This project implements the Hexagonal Architecture (Ports and Adapters) pattern:

- **Application Core**: Pure business logic with handlers
- **Input Adapters**: HTTP (FastAPI), Kafka Consumer, Celery Tasks
- **Output Adapters**: Database repositories, External APIs, Message publishers
- **Dependency Injection**: Clean separation of concerns

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Redis (for Celery)
- Kafka (optional, for Kafka adapter)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd event-manager
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment variables:
```bash
cp .env.example .env
```

### Running the Application

#### HTTP Only Mode (Default)
```bash
python main.py --adapters http
```

#### Multiple Adapters
```bash
python main.py --adapters http celery kafka
```

#### Development Mode
```bash
python main.py --adapters http --debug
```

## 📡 API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Create User
```bash
curl -X POST http://localhost:8000/users \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
  }'
```

### Process Payment
```bash
curl -X POST http://localhost:8000/payments \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "user_123",
    "amount": 100.50,
    "currency": "USD",
    "payment_method": "credit_card"
  }'
```

### Send Notification
```bash
curl -X POST http://localhost:8000/notifications \\
  -H "Content-Type: application/json" \\
  -d '{
    "recipient": "user@example.com",
    "subject": "Welcome!",
    "body": "Welcome to our service",
    "channel": "email"
  }'
```

### Generic Event Processing
```bash
curl -X POST http://localhost:8000/events \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_type": "user.create",
    "data": {
      "name": "Jane Doe",
      "email": "jane@example.com"
    },
    "correlation_id": "optional-correlation-id"
  }'
```

## 🔧 Configuration

Configuration is handled through YAML files and environment variables:

- `config/handlers.yaml`: Handler configurations
- `config/development.yaml`: Development environment settings
- `.env`: Environment variables

## 🧪 Testing

Run tests with pytest:

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only  
pytest tests/integration/

# With coverage
pytest --cov=. --cov-report=html
```

## 📁 Project Structure

```
event-manager/
├── adapters/           # Input adapters (HTTP, Kafka, Celery)
├── handlers/          # Business logic handlers
├── services/          # Output adapters (Database, External APIs)
├── core/             # Application core (DI, Registry, Config)
├── config/           # Configuration files
├── tests/            # Test suite
└── main.py          # Application entry point
```

## 🔌 Extending the System

### Adding a New Handler

1. Create handler class inheriting from `BaseHandler`
2. Implement the `handle` method
3. Register in `main.py` or use auto-discovery
4. Add configuration in `config/handlers.yaml`

### Adding a New Adapter

1. Create adapter class inheriting from `BaseAdapter`  
2. Implement `start` and `stop` methods
3. Add to `EventManagerApp.start_adapters`

### Adding a New Service

1. Create service class with appropriate interface
2. Register in DI container in `main.py`
3. Inject into handlers as needed

## 📊 Monitoring & Logging

The application uses structured logging with Loguru:

- Console output in development
- File logging in production
- Request/response logging middleware
- Handler execution metrics

## 🐳 Docker Support

```yaml
# docker-compose.yml example
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
    depends_on:
      - redis
      - kafka
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
'''