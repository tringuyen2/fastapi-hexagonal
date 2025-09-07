from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime

from .base_repository import BaseRepository


class User:
    """User model"""
    def __init__(self, user_id: str, name: str, email: str, age: Optional[int] = None, 
                 metadata: Dict[str, Any] = None, created_at: datetime = None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.age = age
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()


class UserRepository(BaseRepository):
    """User repository implementation (In-memory for demo)"""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._email_index: Dict[str, str] = {}  # email -> user_id
    
    async def create_user(self, name: str, email: str, age: Optional[int] = None, 
                         metadata: Dict[str, Any] = None) -> str:
        """Create a new user"""
        user_id = self.generate_id()
        user = User(user_id, name, email, age, metadata)
        
        self._users[user_id] = user
        self._email_index[email] = user_id
        
        # Simulate async operation
        await asyncio.sleep(0.01)
        
        return user_id
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        await asyncio.sleep(0.01)  # Simulate async operation
        return self._users.get(user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        await asyncio.sleep(0.01)  # Simulate async operation
        user_id = self._email_index.get(email)
        return self._users.get(user_id) if user_id else None
    
    async def update_user(self, user_id: str, **updates) -> bool:
        """Update user"""
        user = self._users.get(user_id)
        if not user:
            return False
        
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await asyncio.sleep(0.01)  # Simulate async operation
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        user = self._users.get(user_id)
        if not user:
            return False
        
        del self._users[user_id]
        del self._email_index[user.email]
        
        await asyncio.sleep(0.01)  # Simulate async operation
        return True
