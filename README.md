# FastAPI Hexagonal Architecture

A production-ready FastAPI application built with **Hexagonal Architecture** (Ports and Adapters) principles, supporting multiple input adapters and output integrations.

## 🏗️ Architecture Overview

This project implements a true Hexagonal Architecture with clear separation of concerns:

- **Domain Layer**: Pure business logic, entities, value objects, and domain services
- **Application Layer**: Use cases, command handlers, and orchestration logic  
- **Adapters Layer**: Input (HTTP, Kafka, Celery) and Output (Database, External APIs, Message Broker) adapters
- **Core**: Dependency injection, configuration, and cross-cutting concerns

![Architecture](images\hexagonal-architecture-diagram.jpg)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL or MongoDB (optional, defaults to SQLite)
- Redis (for Celery)
- Kafka (optional, for event streaming)

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd fastapi-hexagonal
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment setup:**
```bash
cp docker/.env.example .env
# Edit .env with your configuration
```

### Running the Application

#### HTTP Server Only
```bash
python main.py --adapter http
# or
make run-http
```

#### Kafka Consumer
```bash  
python main.py --adapter kafka
# or
make run-kafka
```

#### Celery Worker
```bash
python main.py --adapter celery
# or  
make run-celery
```

#### Combined Mode (HTTP + Kafka)
```bash
python main.py --adapter combined --combined-adapters http kafka
# or
make run-combined
```

#### Full Docker Stack
```bash
make docker-up
# Services available at:
# - HTTP API: http://localhost:8000
# - Kafka UI: http://localhost:8080  
# - Flower (Celery): http://localhost:5555
```

## 📡 API Usage Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Create User
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com", 
    "age": 30,
    "metadata": {"department": "Engineering"}
  }'
```

### Process Payment
```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "amount": "99.99",
    "currency": "USD",
    "payment_method": "credit_card",
    "reference": "order_456"
  }'
```

### Send Notification
```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "john@example.com",
    "channel": "email",
    "subject": "Welcome!",
    "body": "Hello {name}, welcome!",
    "variables": {"name": "John"}
  }'
```

## 🏗️ Project Structure

```
fastapi-hexagonal/
├── main.py                    # Application entry point
├── config/                    # Configuration management
│   ├── settings.py           # Pydantic settings
│   └── environments/         # Environment-specific configs
├── core/                      # Application core
│   ├── di/                   # Dependency injection
│   ├── exceptions.py         # Domain exceptions
│   ├── registry.py          # Handler registry
│   └── bootstrap.py         # Application bootstrap
├── domain/                    # Domain layer
│   ├── users/               # User domain
│   │   ├── entities.py      # User entity
│   │   ├── value_objects.py # Email, UserId, etc.
│   │   └── services.py      # Domain services
│   ├── payments/            # Payment domain
│   └── notifications/       # Notification domain
├── application/              # Application layer  
│   ├── users/               # User use cases
│   │   ├── commands.py      # Command DTOs
│   │   ├── use_cases.py     # Business orchestration
│   │   └── handlers.py      # Command handlers
│   ├── payments/           # Payment use cases
│   └── notifications/      # Notification use cases
├── adapters/                # Adapters layer
│   ├── inbound/            # Input adapters
│   │   ├── http/           # FastAPI routes & handlers
│   │   ├── kafka/          # Kafka consumers
│   │   └── celery/         # Celery tasks
│   └── outbound/           # Output adapters
│       ├── db/             # Database repositories
│       ├── external_api/   # External service clients
│       └── message_broker/ # Event publishers
├── tests/                   # Test suite
├── docker/                  # Docker configuration
└── logs/                   # Application logs
```

## 🔧 Key Features

### Multiple Input Adapters
- **HTTP**: RESTful API with FastAPI
- **Kafka**: Event-driven message consumption  
- **Celery**: Distributed task processing
- **Pluggable**: Easy to add new adapters (gRPC, GraphQL, etc.)

### Multiple Database Support
- **PostgreSQL**: Production-grade RDBMS
- **MongoDB**: Document-based NoSQL
- **SQLite**: Development and testing
- **Switchable**: Change databases via configuration

### Production Ready
- ✅ Structured logging with Loguru
- ✅ Health and readiness checks
- ✅ Docker containerization
- ✅ Comprehensive error handling
- ✅ Request tracing and monitoring
- ✅ Graceful shutdown handling

### Testing Support
- ✅ Unit tests for domain logic
- ✅ Integration tests for adapters
- ✅ In-memory repositories for testing
- ✅ Mocked external services

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

## 🚀 Deployment

### Docker Compose (Recommended)
```bash
make docker-up
```

### Manual Deployment
1. Set production environment variables
2. Run database migrations (if using PostgreSQL)
3. Start services:
   ```bash
   python main.py --adapter http        # API server
   python main.py --adapter kafka       # Event consumer
   python main.py --adapter celery      # Task worker
   ```

### Kubernetes
- Helm charts available in `deploy/kubernetes/`
- Supports horizontal scaling of each adapter type

## 🔧 Configuration

Configuration is handled through:
1. **Environment variables** (`.env` file)
2. **YAML files** (`config/environments/`)
3. **Pydantic settings** with validation

Example configuration:
```yaml
app:
  name: "FastAPI Hexagonal"
  debug: false
  log_level: "INFO"

database:
  type: "postgresql"
  pg_host: "localhost"
  pg_database: "fastapi_hexagonal"

kafka:
  bootstrap_servers: ["localhost:9092"]
  group_id: "fastapi-hexagonal"
```

## 🏗️ Extending the System

### Adding a New Domain
1. Create domain entities and value objects
2. Implement repository interface
3. Create use cases and commands
4. Add handlers for different adapters

### Adding a New Input Adapter
1. Implement `BaseHandler` interface
2. Register in handler registry
3. Create adapter-specific routing/consumption logic

### Adding a New Output Adapter
1. Define port interface (Protocol)
2. Implement adapter class
3. Register in dependency injection container

## 📚 Architecture Benefits

### Hexagonal Architecture Advantages:
- **Testability**: Easy to unit test business logic in isolation
- **Flexibility**: Swap databases, message brokers, or APIs without changing core logic
- **Maintainability**: Clear separation of concerns
- **Scalability**: Each adapter type can scale independently
- **Technology Agnostic**: Core business logic is framework-independent

### Real-World Benefits:
- **Same Logic, Multiple Inputs**: Create users via HTTP, Kafka, or Celery with identical business rules
- **Easy Migration**: Switch from HTTP to event-driven architecture
- **Database Flexibility**: Move from PostgreSQL to MongoDB without code changes
- **Service Evolution**: Add new integration points without touching existing code

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.