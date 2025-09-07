# services/database/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository interface"""
    
    @abstractmethod
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create new entity, return ID"""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update entity, return success status"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity, return success status"""
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[T]:
        """List entities with optional filters"""
        pass
    
    @abstractmethod
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count entities with optional filters"""
        pass


class IUserRepository(BaseRepository[Dict[str, Any]]):
    """User repository interface"""
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def create_user(self, name: str, email: str, age: Optional[int] = None, 
                         metadata: Dict[str, Any] = None) -> str:
        """Create user with specific fields"""
        pass


class IPaymentRepository(BaseRepository[Dict[str, Any]]):
    """Payment repository interface"""
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get payments by user ID"""
        pass
    
    @abstractmethod
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by transaction ID"""
        pass
    
    @abstractmethod
    async def create_payment(self, user_id: str, amount: float, currency: str,
                           transaction_id: str, status: str, metadata: Dict[str, Any] = None) -> str:
        """Create payment record"""
        pass


class INotificationRepository(BaseRepository[Dict[str, Any]]):
    """Notification repository interface"""
    
    @abstractmethod
    async def get_by_recipient(self, recipient: str) -> List[Dict[str, Any]]:
        """Get notifications by recipient"""
        pass
    
    @abstractmethod
    async def create_notification(self, recipient: str, subject: str, body: str,
                                channel: str, status: str, metadata: Dict[str, Any] = None) -> str:
        """Create notification record"""
        pass