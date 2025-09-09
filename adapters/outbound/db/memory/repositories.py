# adapters/outbound/db/memory/repositories.py
"""In-memory repository implementations for testing"""
from typing import Dict, List, Optional
import asyncio
from datetime import datetime

from domain.users.entities import User
from domain.users.value_objects import UserId, Email
from domain.payments.entities import Payment
from domain.payments.value_objects import PaymentId
from domain.notifications.entities import Notification
from domain.notifications.value_objects import NotificationId
from core.exceptions import NotFoundError, AlreadyExistsError


class MemoryUserRepository:
    """In-memory user repository for testing"""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._email_index: Dict[str, str] = {}
    
    async def create(self, user: User) -> None:
        """Create user in memory"""
        user_id_str = str(user.user_id)
        email_str = str(user.email)
        
        # Check for duplicate email
        if email_str in self._email_index:
            raise AlreadyExistsError("User", f"email={email_str}")
        
        self._users[user_id_str] = user
        self._email_index[email_str] = user_id_str
        
        # Simulate async operation
        await asyncio.sleep(0.001)
    
    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get user by ID"""
        await asyncio.sleep(0.001)
        return self._users.get(str(user_id))
    
    async def get_by_email(self, email: Email) -> Optional[User]:
        """Get user by email"""
        await asyncio.sleep(0.001)
        user_id_str = self._email_index.get(str(email))
        return self._users.get(user_id_str) if user_id_str else None
    
    async def update(self, user: User) -> None:
        """Update user in memory"""
        user_id_str = str(user.user_id)
        
        if user_id_str not in self._users:
            raise NotFoundError("User", user_id_str)
        
        # Update email index if email changed
        old_user = self._users[user_id_str]
        old_email = str(old_user.email)
        new_email = str(user.email)
        
        if old_email != new_email:
            # Check for duplicate new email
            if new_email in self._email_index:
                raise AlreadyExistsError("User", f"email={new_email}")
            
            # Update index
            del self._email_index[old_email]
            self._email_index[new_email] = user_id_str
        
        self._users[user_id_str] = user
        await asyncio.sleep(0.001)
    
    async def delete(self, user_id: UserId) -> None:
        """Delete user from memory"""
        user_id_str = str(user_id)
        
        if user_id_str not in self._users:
            raise NotFoundError("User", user_id_str)
        
        user = self._users[user_id_str]
        email_str = str(user.email)
        
        del self._users[user_id_str]
        del self._email_index[email_str]
        
        await asyncio.sleep(0.001)


class MemoryPaymentRepository:
    """In-memory payment repository for testing"""
    
    def __init__(self):
        self._payments: Dict[str, Payment] = {}
    
    async def create(self, payment: Payment) -> None:
        """Create payment in memory"""
        payment_id_str = str(payment.payment_id)
        self._payments[payment_id_str] = payment
        await asyncio.sleep(0.001)
    
    async def get_by_id(self, payment_id: PaymentId) -> Optional[Payment]:
        """Get payment by ID"""
        await asyncio.sleep(0.001)
        return self._payments.get(str(payment_id))
    
    async def update(self, payment: Payment) -> None:
        """Update payment in memory"""
        payment_id_str = str(payment.payment_id)
        
        if payment_id_str not in self._payments:
            raise NotFoundError("Payment", payment_id_str)
        
        self._payments[payment_id_str] = payment
        await asyncio.sleep(0.001)


class MemoryNotificationRepository:
    """In-memory notification repository for testing"""
    
    def __init__(self):
        self._notifications: Dict[str, Notification] = {}
    
    async def create(self, notification: Notification) -> None:
        """Create notification in memory"""
        notification_id_str = str(notification.notification_id)
        self._notifications[notification_id_str] = notification
        await asyncio.sleep(0.001)
    
    async def get_by_id(self, notification_id: NotificationId) -> Optional[Notification]:
        """Get notification by ID"""
        await asyncio.sleep(0.001)
        return self._notifications.get(str(notification_id))
    
    async def update(self, notification: Notification) -> None:
        """Update notification in memory"""
        notification_id_str = str(notification.notification_id)
        
        if notification_id_str not in self._notifications:
            raise NotFoundError("Notification", notification_id_str)
        
        self._notifications[notification_id_str] = notification
        await asyncio.sleep(0.001)
            