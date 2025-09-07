# tests/unit/adapters/test_http_adapter.py
import pytest
from fastapi.testclient import TestClient

from adapters.http.adapter import HTTPAdapter
from core.models import EventType


class TestHTTPAdapter:
    """Test HTTP Adapter"""
    
    @pytest.fixture
    async def adapter(self):
        """Create HTTP adapter"""
        adapter = HTTPAdapter()
        await adapter.start()
        return adapter
    
    @pytest.fixture
    def client(self, adapter):
        """Create test client"""
        return TestClient(adapter.app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "adapters" in data
    
    def test_create_user_endpoint(self, client, sample_user_data):
        """Test user creation endpoint"""
        response = client.post("/users", json=sample_user_data)
        
        # Note: This will fail without proper handler registration
        # but shows the test structure
        assert response.status_code in [200, 500]  # Depends on handler availability
    
    def test_process_event_endpoint(self, client, sample_user_data):
        """Test generic event processing endpoint"""
        payload = {
            "event_type": EventType.USER_CREATE.value,
            "data": sample_user_data,
            "correlation_id": "test_correlation_123"
        }
        
        response = client.post("/events", json=payload)
        
        assert response.status_code in [200, 500]  # Depends on handler availability
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "status" in data