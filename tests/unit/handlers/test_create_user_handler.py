# tests/unit/handlers/test_create_user_handler.py
import pytest
from unittest.mock import AsyncMock

from handlers.user.create_user import CreateUserHandler
from core.models import EventMessage, EventType, EventStatus
from services.database.user_repository import UserRepository
from services.messaging.event_publisher import EventPublisher


class TestCreateUserHandler:
    """Test CreateUserHandler"""
    
    @pytest.fixture
    async def handler(self):
        """Create handler with mock dependencies"""
        user_repo = AsyncMock(spec=UserRepository)
        event_publisher = AsyncMock(spec=EventPublisher)
        return CreateUserHandler(user_repo, event_publisher)
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, handler, sample_user_data):
        """Test successful user creation"""
        # Setup mocks
        handler.user_repository.get_by_email.return_value = None
        handler.user_repository.create_user.return_value = "user_123"
        handler.event_publisher.publish_event.return_value = True
        
        # Create event
        event = EventMessage(
            event_id="test_001",
            event_type=EventType.USER_CREATE,
            source="test",
            data=sample_user_data
        )
        
        # Execute handler
        result = await handler.handle(event)
        
        # Assertions
        assert result.success is True
        assert result.status == EventStatus.SUCCESS
        assert result.data["user_id"] == "user_123"
        
        # Verify calls
        handler.user_repository.get_by_email.assert_called_once_with("john.doe@example.com")
        handler.user_repository.create_user.assert_called_once()
        handler.event_publisher.publish_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, handler, sample_user_data):
        """Test user creation when user already exists"""
        # Setup mocks
        handler.user_repository.get_by_email.return_value = {"user_id": "existing_user"}
        
        # Create event
        event = EventMessage(
            event_id="test_002",
            event_type=EventType.USER_CREATE,
            source="test",
            data=sample_user_data
        )
        
        # Execute handler
        result = await handler.handle(event)
        
        # Assertions
        assert result.success is False
        assert result.status == EventStatus.FAILED
        assert result.error_code == "USER_ALREADY_EXISTS"
        assert "already exists" in result.message
        
        # Verify no creation was attempted
        handler.user_repository.create_user.assert_not_called()
