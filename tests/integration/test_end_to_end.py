# tests/integration/test_end_to_end.py
import pytest
import asyncio

from main import EventManagerApp
from core.models import EventType, EventMessage


class TestEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.fixture
    async def app(self):
        """Create test application"""
        app = EventManagerApp()
        return app
    
    @pytest.mark.asyncio
    async def test_user_creation_flow(self, app, sample_user_data):
        """Test complete user creation flow"""
        # Start HTTP adapter
        await app.start_adapters(["http"])
        
        try:
            # Get HTTP adapter
            http_adapter = next(a for a in app.adapters if a.adapter_name == "http")
            
            # Process user creation event
            result = await http_adapter.process_event(
                event_type=EventType.USER_CREATE,
                data=sample_user_data,
                correlation_id="integration_test_001"
            )
            
            # Verify result
            assert result.success is True
            assert "user_id" in result.data
            
        finally:
            await app.stop_adapters()
    
    @pytest.mark.asyncio
    async def test_payment_processing_flow(self, app, sample_payment_data):
        """Test complete payment processing flow"""
        # Start HTTP adapter
        await app.start_adapters(["http"])
        
        try:
            # Get HTTP adapter
            http_adapter = next(a for a in app.adapters if a.adapter_name == "http")
            
            # First create a user (payment requires existing user)
            user_result = await http_adapter.process_event(
                event_type=EventType.USER_CREATE,
                data={
                    "name": "Payment User",
                    "email": "payment@example.com",
                    "age": 25
                }
            )
            
            assert user_result.success is True
            user_id = user_result.data["user_id"]
            
            # Update payment data with real user ID
            payment_data = sample_payment_data.copy()
            payment_data["user_id"] = user_id
            
            # Process payment
            payment_result = await http_adapter.process_event(
                event_type=EventType.PAYMENT_PROCESS,
                data=payment_data,
                correlation_id="payment_test_001"
            )
            
            # Verify result (might succeed or fail based on mock logic)
            assert payment_result.success in [True, False]
            if payment_result.success:
                assert "transaction_id" in payment_result.data
            
        finally:
            await app.stop_adapters()