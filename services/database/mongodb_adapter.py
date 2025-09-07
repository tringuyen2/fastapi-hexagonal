# services/database/mongodb_adapter.py
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, PyMongoError

from .interfaces import IUserRepository, IPaymentRepository, INotificationRepository
from core.exceptions import ValidationException, ServiceUnavailableException
from loguru import logger


class MongoDBConfig:
    """MongoDB configuration"""
    def __init__(self, connection_string: str = "mongodb://localhost:27017", 
                 database_name: str = "event_manager"):
        self.connection_string = connection_string
        self.database_name = database_name


class MongoDBAdapter:
    """MongoDB connection adapter"""
    
    def __init__(self, config: MongoDBConfig):
        self.config = config
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.config.connection_string)
            self.database = self.client[self.config.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.config.database_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get collection instance"""
        if not self.database:
            raise ServiceUnavailableException("MongoDB")
        return self.database[collection_name]


class MongoUserRepository(IUserRepository):
    """MongoDB User Repository implementation"""
    
    def __init__(self, mongodb_adapter: MongoDBAdapter):
        self.adapter = mongodb_adapter
        self.collection_name = "users"
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self.adapter.get_collection(self.collection_name)
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create new user document"""
        try:
            entity_id = str(uuid.uuid4())
            document = {
                "_id": entity_id,
                **entity,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.collection.insert_one(document)
            logger.info(f"Created user document: {entity_id}")
            return entity_id
            
        except DuplicateKeyError:
            raise ValidationException(f"Entity with ID already exists")
        except PyMongoError as e:
            logger.error(f"MongoDB error creating user: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            document = await self.collection.find_one({"_id": entity_id})
            if document:
                document["user_id"] = document.pop("_id")
            return document
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting user by ID: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            document = await self.collection.find_one({"email": email})
            if document:
                document["user_id"] = document.pop("_id")
            return document
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting user by email: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def create_user(self, name: str, email: str, age: Optional[int] = None,
                         metadata: Dict[str, Any] = None) -> str:
        """Create user with specific fields"""
        user_data = {
            "name": name,
            "email": email,
            "age": age,
            "metadata": metadata or {}
        }
        
        # Check for existing user
        existing = await self.get_by_email(email)
        if existing:
            raise ValidationException(f"User with email {email} already exists")
        
        return await self.create(user_data)
    
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update user"""
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": entity_id},
                {"$set": updates}
            )
            return result.modified_count > 0
            
        except PyMongoError as e:
            logger.error(f"MongoDB error updating user: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def delete(self, entity_id: str) -> bool:
        """Delete user"""
        try:
            result = await self.collection.delete_one({"_id": entity_id})
            return result.deleted_count > 0
            
        except PyMongoError as e:
            logger.error(f"MongoDB error deleting user: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List users with pagination"""
        try:
            query = filters or {}
            cursor = self.collection.find(query).skip(offset).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            # Transform _id to user_id
            for doc in documents:
                doc["user_id"] = doc.pop("_id")
            
            return documents
            
        except PyMongoError as e:
            logger.error(f"MongoDB error listing users: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count users"""
        try:
            query = filters or {}
            return await self.collection.count_documents(query)
            
        except PyMongoError as e:
            logger.error(f"MongoDB error counting users: {e}")
            raise ServiceUnavailableException("MongoDB")


class MongoPaymentRepository(IPaymentRepository):
    """MongoDB Payment Repository implementation"""
    
    def __init__(self, mongodb_adapter: MongoDBAdapter):
        self.adapter = mongodb_adapter
        self.collection_name = "payments"
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self.adapter.get_collection(self.collection_name)
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create payment document"""
        try:
            entity_id = str(uuid.uuid4())
            document = {
                "_id": entity_id,
                **entity,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.collection.insert_one(document)
            logger.info(f"Created payment document: {entity_id}")
            return entity_id
            
        except PyMongoError as e:
            logger.error(f"MongoDB error creating payment: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by ID"""
        try:
            document = await self.collection.find_one({"_id": entity_id})
            if document:
                document["payment_id"] = document.pop("_id")
            return document
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting payment: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get payments by user ID"""
        try:
            cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            for doc in documents:
                doc["payment_id"] = doc.pop("_id")
            
            return documents
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting payments by user: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by transaction ID"""
        try:
            document = await self.collection.find_one({"transaction_id": transaction_id})
            if document:
                document["payment_id"] = document.pop("_id")
            return document
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting payment by transaction ID: {e}")
            raise ServiceUnavailableException("MongoDB")
    
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
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": entity_id},
                {"$set": updates}
            )
            return result.modified_count > 0
            
        except PyMongoError as e:
            logger.error(f"MongoDB error updating payment: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def delete(self, entity_id: str) -> bool:
        """Delete payment"""
        try:
            result = await self.collection.delete_one({"_id": entity_id})
            return result.deleted_count > 0
            
        except PyMongoError as e:
            logger.error(f"MongoDB error deleting payment: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List payments"""
        try:
            query = filters or {}
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
            documents = await cursor.to_list(length=limit)
            
            for doc in documents:
                doc["payment_id"] = doc.pop("_id")
            
            return documents
            
        except PyMongoError as e:
            logger.error(f"MongoDB error listing payments: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count payments"""
        try:
            query = filters or {}
            return await self.collection.count_documents(query)
            
        except PyMongoError as e:
            logger.error(f"MongoDB error counting payments: {e}")
            raise ServiceUnavailableException("MongoDB")
        

class MongoNotificationRepository(INotificationRepository):
    """MongoDB Notification Repository implementation"""
    
    def __init__(self, mongodb_adapter: MongoDBAdapter):
        self.adapter = mongodb_adapter
        self.collection_name = "notifications"
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self.adapter.get_collection(self.collection_name)
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create notification document"""
        try:
            entity_id = str(uuid.uuid4())
            document = {
                "_id": entity_id,
                **entity,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.collection.insert_one(document)
            logger.info(f"Created notification document: {entity_id}")
            return entity_id
            
        except PyMongoError as e:
            logger.error(f"MongoDB error creating notification: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get notification by ID"""
        try:
            document = await self.collection.find_one({"_id": entity_id})
            if document:
                document["notification_id"] = document.pop("_id")
            return document
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting notification: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def get_by_recipient(self, recipient: str) -> List[Dict[str, Any]]:
        """Get notifications by recipient"""
        try:
            cursor = self.collection.find({"recipient": recipient}).sort("created_at", -1)
            documents = await cursor.to_list(length=None)
            
            for doc in documents:
                doc["notification_id"] = doc.pop("_id")
            
            return documents
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting notifications by recipient: {e}")
            raise ServiceUnavailableException("MongoDB")
    
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
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": entity_id},
                {"$set": updates}
            )
            return result.modified_count > 0
            
        except PyMongoError as e:
            logger.error(f"MongoDB error updating notification: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def delete(self, entity_id: str) -> bool:
        """Delete notification"""
        try:
            result = await self.collection.delete_one({"_id": entity_id})
            return result.deleted_count > 0
            
        except PyMongoError as e:
            logger.error(f"MongoDB error deleting notification: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List notifications"""
        try:
            query = filters or {}
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
            documents = await cursor.to_list(length=limit)
            
            for doc in documents:
                doc["notification_id"] = doc.pop("_id")
            
            return documents
            
        except PyMongoError as e:
            logger.error(f"MongoDB error listing notifications: {e}")
            raise ServiceUnavailableException("MongoDB")
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count notifications"""
        try:
            query = filters or {}
            return await self.collection.count_documents(query)
            
        except PyMongoError as e:
            logger.error(f"MongoDB error counting notifications: {e}")
            raise ServiceUnavailableException("MongoDB")
        