# services/database/sqlite_repositories.py
"""SQLite/In-memory repositories for backward compatibility and testing"""
from typing import Optional, List, Dict, Any
import asyncio
import uuid
from datetime import datetime

from .interfaces import IPaymentRepository, INotificationRepository


class SQLitePaymentRepository(IPaymentRepository):
    """In-memory Payment Repository (for testing/SQLite compatibility)"""
    
    def __init__(self):
        self._payments: Dict[str, Dict[str, Any]] = {}
        self._user_index: Dict[str, List[str]] = {}  # user_id -> payment_ids
        self._transaction_index: Dict[str, str] = {}  # transaction_id -> payment_id
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create payment"""
        payment_id = str(uuid.uuid4())
        payment = {
            "payment_id": payment_id,
            **entity,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self._payments[payment_id] = payment
        
        # Update indexes
        user_id = entity.get("user_id")
        if user_id:
            if user_id not in self._user_index:
                self._user_index[user_id] = []
            self._user_index[user_id].append(payment_id)
        
        transaction_id = entity.get("transaction_id")
        if transaction_id:
            self._transaction_index[transaction_id] = payment_id
        
        await asyncio.sleep(0.01)  # Simulate async operation
        return payment_id
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by ID"""
        await asyncio.sleep(0.01)
        return self._payments.get(entity_id)
    
    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get payments by user ID"""
        await asyncio.sleep(0.01)
        payment_ids = self._user_index.get(user_id, [])
        return [self._payments[pid] for pid in payment_ids if pid in self._payments]
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by transaction ID"""
        await asyncio.sleep(0.01)
        payment_id = self._transaction_index.get(transaction_id)
        return self._payments.get(payment_id) if payment_id else None
    
    async def create_payment(self, user_id: str, amount: float, currency: str,
                           transaction_id: str, status: str, metadata: Dict[str, Any] = None) -> str:
        """Create payment record"""
        payment_data = {
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "transaction_id": transaction_id,
            "status": status,
            "metadata": metadata or {}
        }
        return await self.create(payment_data)
    
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update payment"""
        if entity_id not in self._payments:
            return False
        
        self._payments[entity_id].update(updates)
        self._payments[entity_id]["updated_at"] = datetime.utcnow().isoformat()
        
        await asyncio.sleep(0.01)
        return True
    
    async def delete(self, entity_id: str) -> bool:
        """Delete payment"""
        if entity_id not in self._payments:
            return False
        
        payment = self._payments[entity_id]
        
        # Clean up indexes
        user_id = payment.get("user_id")
        if user_id and user_id in self._user_index:
            if entity_id in self._user_index[user_id]:
                self._user_index[user_id].remove(entity_id)
        
        transaction_id = payment.get("transaction_id")
        if transaction_id and transaction_id in self._transaction_index:
            del self._transaction_index[transaction_id]
        
        del self._payments[entity_id]
        
        await asyncio.sleep(0.01)
        return True
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List payments"""
        payments = list(self._payments.values())
        
        # Apply filters
        if filters:
            filtered_payments = []
            for payment in payments:
                match = True
                for key, value in filters.items():
                    if payment.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_payments.append(payment)
            payments = filtered_payments
        
        # Sort by created_at desc
        payments.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        await asyncio.sleep(0.01)
        return payments[offset:offset + limit]
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count payments"""
        if not filters:
            return len(self._payments)
        
        count = 0
        for payment in self._payments.values():
            match = True
            for key, value in filters.items():
                if payment.get(key) != value:
                    match = False
                    break
            if match:
                count += 1
        
        await asyncio.sleep(0.01)
        return count


class SQLiteNotificationRepository(INotificationRepository):
    """In-memory Notification Repository (for testing/SQLite compatibility)"""
    
    def __init__(self):
        self._notifications: Dict[str, Dict[str, Any]] = {}
        self._recipient_index: Dict[str, List[str]] = {}  # recipient -> notification_ids
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create notification"""
        notification_id = str(uuid.uuid4())
        notification = {
            "notification_id": notification_id,
            **entity,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self._notifications[notification_id] = notification
        
        # Update recipient index
        recipient = entity.get("recipient")
        if recipient:
            if recipient not in self._recipient_index:
                self._recipient_index[recipient] = []
            self._recipient_index[recipient].append(notification_id)
        
        await asyncio.sleep(0.01)
        return notification_id
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get notification by ID"""
        await asyncio.sleep(0.01)
        return self._notifications.get(entity_id)
    
    async def get_by_recipient(self, recipient: str) -> List[Dict[str, Any]]:
        """Get notifications by recipient"""
        await asyncio.sleep(0.01)
        notification_ids = self._recipient_index.get(recipient, [])
        return [self._notifications[nid] for nid in notification_ids if nid in self._notifications]
    
    async def create_notification(self, recipient: str, subject: str, body: str,
                                channel: str, status: str, metadata: Dict[str, Any] = None) -> str:
        """Create notification record"""
        notification_data = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "channel": channel,
            "status": status,
            "metadata": metadata or {}
        }
        return await self.create(notification_data)
    
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update notification"""
        if entity_id not in self._notifications:
            return False
        
        self._notifications[entity_id].update(updates)
        self._notifications[entity_id]["updated_at"] = datetime.utcnow().isoformat()
        
        await asyncio.sleep(0.01)
        return True
    
    async def delete(self, entity_id: str) -> bool:
        """Delete notification"""
        if entity_id not in self._notifications:
            return False
        
        notification = self._notifications[entity_id]
        
        # Clean up recipient index
        recipient = notification.get("recipient")
        if recipient and recipient in self._recipient_index:
            if entity_id in self._recipient_index[recipient]:
                self._recipient_index[recipient].remove(entity_id)
        
        del self._notifications[entity_id]
        
        await asyncio.sleep(0.01)
        return True
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List notifications"""
        notifications = list(self._notifications.values())
        
        # Apply filters
        if filters:
            filtered_notifications = []
            for notification in notifications:
                match = True
                for key, value in filters.items():
                    if notification.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_notifications.append(notification)
            notifications = filtered_notifications
        
        # Sort by created_at desc
        notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        await asyncio.sleep(0.01)
        return notifications[offset:offset + limit]
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count notifications"""
        if not filters:
            return len(self._notifications)
        
        count = 0
        for notification in self._notifications.values():
            match = True
            for key, value in filters.items():
                if notification.get(key) != value:
                    match = False
                    break
            if match:
                count += 1
        
        await asyncio.sleep(0.01)
        return count
