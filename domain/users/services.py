# domain/users/services.py
from typing import Protocol, Optional
from abc import abstractmethod

from .entities import User
from .value_objects import UserId, Email
from core.exceptions import AlreadyExistsError, NotFoundError


class UserRepository(Protocol):
    """User repository port"""
    
    @abstractmethod
    async def create(self, user: User) -> None:
        """Create user"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> None:
        """Update user"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: UserId) -> None:
        """Delete user"""
        pass


class UserDomainService:
    """User domain service"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def ensure_unique_email(self, email: Email, exclude_user_id: Optional[UserId] = None) -> None:
        """Ensure email is unique"""
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user and (exclude_user_id is None or existing_user.user_id != exclude_user_id):
            raise AlreadyExistsError("User", f"email={email}")
    
    async def ensure_user_exists(self, user_id: UserId) -> User:
        """Ensure user exists and return it"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        return user
