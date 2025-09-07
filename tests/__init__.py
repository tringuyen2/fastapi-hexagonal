# tests/__init__.py
"""Test package for Event Manager"""


# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator

from core.dependency_injection import DIContainer
from services.database.user_repository import UserRepository
from services.external.email_service import EmailService
from services.external.payment_gateway import PaymentGateway
from services.messaging.event_publisher import EventPublisher


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_container() -> AsyncGenerator[DIContainer, None]:
    """Create test DI container with mock services"""
    container = DIContainer()
    
    # Register test services
    container.register_singleton(UserRepository, UserRepository())
    container.register_singleton(EmailService, EmailService())
    container.register_singleton(PaymentGateway, PaymentGateway())
    container.register_singleton(EventPublisher, EventPublisher())
    
    yield container


@pytest.fixture
async def sample_user_data():
    """Sample user data for testing"""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 30,
        "metadata": {"source": "test"}
    }


@pytest.fixture
async def sample_payment_data():
    """Sample payment data for testing"""
    return {
        "user_id": "user_123",
        "amount": 100.50,
        "currency": "USD",
        "payment_method": "credit_card",
        "reference": "test_payment_001"
    }
