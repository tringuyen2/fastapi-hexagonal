# services/database/factory.py
from typing import Literal, Dict, Any, Optional
from enum import Enum

from .interfaces import IUserRepository, IPaymentRepository, INotificationRepository
from .mongodb_adapter import MongoDBAdapter, MongoDBConfig, MongoUserRepository, MongoPaymentRepository
from .postgresql_adapter import PostgreSQLAdapter, PostgreSQLConfig, PostgreSQLUserRepository, PostgreSQLPaymentRepository, PostgreSQLNotificationRepository
from core.exceptions import ValidationException
from loguru import logger


class DatabaseType(str, Enum):
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"  # Keep existing in-memory for testing


class DatabaseFactory:
    """Factory for creating database adapters and repositories"""
    
    @staticmethod
    async def create_user_repository(
        db_type: DatabaseType,
        config: Dict[str, Any]
    ) -> IUserRepository:
        """Create user repository based on database type"""
        
        if db_type == DatabaseType.MONGODB:
            mongo_config = MongoDBConfig(
                connection_string=config.get("connection_string", "mongodb://localhost:27017"),
                database_name=config.get("database_name", "event_manager")
            )
            adapter = MongoDBAdapter(mongo_config)
            await adapter.connect()
            return MongoUserRepository(adapter)
            
        elif db_type == DatabaseType.POSTGRESQL:
            pg_config = PostgreSQLConfig(
                host=config.get("host", "localhost"),
                port=config.get("port", 5432),
                database=config.get("database", "event_manager"),
                username=config.get("username", "postgres"),
                password=config.get("password", "postgres")
            )
            adapter = PostgreSQLAdapter(pg_config)
            await adapter.connect()
            await adapter.create_tables()  # Ensure tables exist
            return PostgreSQLUserRepository(adapter)
            
        elif db_type == DatabaseType.SQLITE:
            # Keep original in-memory implementation for backward compatibility
            from .user_repository import UserRepository
            return UserRepository()
            
        else:
            raise ValidationException(f"Unsupported database type: {db_type}")
    
    @staticmethod
    async def create_payment_repository(
        db_type: DatabaseType,
        config: Dict[str, Any]
    ) -> IPaymentRepository:
        """Create payment repository based on database type"""
        
        if db_type == DatabaseType.MONGODB:
            mongo_config = MongoDBConfig(
                connection_string=config.get("connection_string", "mongodb://localhost:27017"),
                database_name=config.get("database_name", "event_manager")
            )
            adapter = MongoDBAdapter(mongo_config)
            await adapter.connect()
            return MongoPaymentRepository(adapter)
            
        elif db_type == DatabaseType.POSTGRESQL:
            pg_config = PostgreSQLConfig(
                host=config.get("host", "localhost"),
                port=config.get("port", 5432),
                database=config.get("database", "event_manager"),
                username=config.get("username", "postgres"),
                password=config.get("password", "postgres")
            )
            adapter = PostgreSQLAdapter(pg_config)
            await adapter.connect()
            await adapter.create_tables()
            return PostgreSQLPaymentRepository(adapter)
            
        elif db_type == DatabaseType.SQLITE:
            # Create a mock payment repository for SQLite
            from .sqlite_repositories import SQLitePaymentRepository
            return SQLitePaymentRepository()
            
        else:
            raise ValidationException(f"Unsupported database type: {db_type}")
    
    @staticmethod
    async def create_notification_repository(
        db_type: DatabaseType,
        config: Dict[str, Any]
    ) -> INotificationRepository:
        """Create notification repository based on database type"""
        
        if db_type == DatabaseType.MONGODB:
            mongo_config = MongoDBConfig(
                connection_string=config.get("connection_string", "mongodb://localhost:27017"),
                database_name=config.get("database_name", "event_manager")
            )
            adapter = MongoDBAdapter(mongo_config)
            await adapter.connect()
            from .mongodb_adapter import MongoNotificationRepository
            return MongoNotificationRepository(adapter)
            
        elif db_type == DatabaseType.POSTGRESQL:
            pg_config = PostgreSQLConfig(
                host=config.get("host", "localhost"),
                port=config.get("port", 5432),
                database=config.get("database", "event_manager"),
                username=config.get("username", "postgres"),
                password=config.get("password", "postgres")
            )
            adapter = PostgreSQLAdapter(pg_config)
            await adapter.connect()
            await adapter.create_tables()
            return PostgreSQLNotificationRepository(adapter)
            
        elif db_type == DatabaseType.SQLITE:
            from .sqlite_repositories import SQLiteNotificationRepository
            return SQLiteNotificationRepository()
            
        else:
            raise ValidationException(f"Unsupported database type: {db_type}")
