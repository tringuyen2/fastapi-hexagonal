# services/database/postgresql_adapter.py
from typing import Optional, List, Dict, Any, Type
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, select, update, delete, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .interfaces import IUserRepository, IPaymentRepository, INotificationRepository
from core.exceptions import ValidationException, ServiceUnavailableException
from loguru import logger


# SQLAlchemy Models
class Base(DeclarativeBase):
    """Base model class"""
    pass


class UserModel(Base):
    """User SQLAlchemy model"""
    __tablename__ = "users"
    
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "age": self.age,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PaymentModel(Base):
    """Payment SQLAlchemy model"""
    __tablename__ = "payments"
    
    payment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "transaction_id": self.transaction_id,
            "status": self.status,
            "payment_method": self.payment_method,
            "reference": self.reference,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class NotificationModel(Base):
    """Notification SQLAlchemy model"""
    __tablename__ = "notifications"
    
    notification_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    template_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "notification_id": self.notification_id,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "channel": self.channel,
            "status": self.status,
            "template_id": self.template_id,
            "message_id": self.message_id,
            "meta_data": self.meta_data,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PostgreSQLConfig:
    """PostgreSQL configuration"""
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "event_manager",
                 username: str = "postgres",
                 password: str = "postgres",
                 pool_size: int = 10,
                 max_overflow: int = 20):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
    
    @property
    def connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class PostgreSQLAdapter:
    """PostgreSQL connection adapter"""
    
    def __init__(self, config: PostgreSQLConfig):
        self.config = config
        self.engine = None
        self.session_factory = None
    
    async def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.engine = create_async_engine(
                self.config.connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                echo=False  # Set to True for SQL debugging
            )
            
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.run_sync(lambda _: None)
            
            logger.info(f"Connected to PostgreSQL: {self.config.database}")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ServiceUnavailableException("PostgreSQL")
    
    async def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Disconnected from PostgreSQL")
    
    async def create_tables(self):
        """Create all tables"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.meta_data.create_all)
            logger.info("Created PostgreSQL tables")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            raise ServiceUnavailableException("PostgreSQL")
        return self.session_factory()


class PostgreSQLUserRepository(IUserRepository):
    """PostgreSQL User Repository implementation"""
    
    def __init__(self, postgresql_adapter: PostgreSQLAdapter):
        self.adapter = postgresql_adapter
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create new user"""
        async with self.adapter.get_session() as session:
            try:
                user = UserModel(**entity)
                session.add(user)
                await session.commit()
                
                logger.info(f"Created user: {user.user_id}")
                return user.user_id
                
            except IntegrityError as e:
                await session.rollback()
                if "unique constraint" in str(e).lower():
                    raise ValidationException("User with this email already exists")
                raise ValidationException(f"Database constraint error: {e}")
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error creating user: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by ID"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.payment_id == entity_id)
                result = await session.execute(stmt)
                payment = result.scalar_one_or_none()
                
                return payment.to_dict() if payment else None
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error getting payment by ID: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get payments by user ID"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.user_id == user_id).order_by(PaymentModel.created_at.desc())
                result = await session.execute(stmt)
                payments = result.scalars().all()
                
                return [payment.to_dict() for payment in payments]
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error getting payments by user: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by transaction ID"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.transaction_id == transaction_id)
                result = await session.execute(stmt)
                payment = result.scalar_one_or_none()
                
                return payment.to_dict() if payment else None
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error getting payment by transaction ID: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def create_payment(self, user_id: str, amount: float, currency: str,
                           transaction_id: str, status: str, meta_data: Dict[str, Any] = None) -> str:
        """Create payment record"""
        payment_data = {
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "transaction_id": transaction_id,
            "status": status,
            "meta_data": meta_data or {}
        }
        return await self.create(payment_data)
    
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update payment"""
        async with self.adapter.get_session() as session:
            try:
                updates["updated_at"] = datetime.utcnow()
                
                stmt = update(PaymentModel).where(PaymentModel.payment_id == entity_id).values(**updates)
                result = await session.execute(stmt)
                await session.commit()
                
                return result.rowcount > 0
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error updating payment: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def delete(self, entity_id: str) -> bool:
        """Delete payment"""
        async with self.adapter.get_session() as session:
            try:
                stmt = delete(PaymentModel).where(PaymentModel.payment_id == entity_id)
                result = await session.execute(stmt)
                await session.commit()
                
                return result.rowcount > 0
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error deleting payment: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List payments with pagination"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(PaymentModel)
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if hasattr(PaymentModel, key):
                            stmt = stmt.where(getattr(PaymentModel, key) == value)
                
                stmt = stmt.offset(offset).limit(limit).order_by(PaymentModel.created_at.desc())
                
                result = await session.execute(stmt)
                payments = result.scalars().all()
                
                return [payment.to_dict() for payment in payments]
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error listing payments: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count payments"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(func.count(PaymentModel.payment_id))
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if hasattr(PaymentModel, key):
                            stmt = stmt.where(getattr(PaymentModel, key) == value)
                
                result = await session.execute(stmt)
                return result.scalar()
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error counting payments: {e}")
                raise ServiceUnavailableException("PostgreSQL")


class PostgreSQLNotificationRepository(INotificationRepository):
    """PostgreSQL Notification Repository implementation"""
    
    def __init__(self, postgresql_adapter: PostgreSQLAdapter):
        self.adapter = postgresql_adapter
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create notification"""
        async with self.adapter.get_session() as session:
            try:
                notification = NotificationModel(**entity)
                session.add(notification)
                await session.commit()
                
                logger.info(f"Created notification: {notification.notification_id}")
                return notification.notification_id
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error creating notification: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get notification by ID"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(NotificationModel).where(NotificationModel.notification_id == entity_id)
                result = await session.execute(stmt)
                notification = result.scalar_one_or_none()
                
                return notification.to_dict() if notification else None
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error getting notification by ID: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def get_by_recipient(self, recipient: str) -> List[Dict[str, Any]]:
        """Get notifications by recipient"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(NotificationModel).where(NotificationModel.recipient == recipient).order_by(NotificationModel.created_at.desc())
                result = await session.execute(stmt)
                notifications = result.scalars().all()
                
                return [notification.to_dict() for notification in notifications]
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error getting notifications by recipient: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def create_notification(self, recipient: str, subject: str, body: str,
                                channel: str, status: str, meta_data: Dict[str, Any] = None) -> str:
        """Create notification record"""
        notification_data = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "channel": channel,
            "status": status,
            "meta_data": meta_data or {}
        }
        return await self.create(notification_data)
    
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update notification"""
        async with self.adapter.get_session() as session:
            try:
                updates["updated_at"] = datetime.utcnow()
                
                stmt = update(NotificationModel).where(NotificationModel.notification_id == entity_id).values(**updates)
                result = await session.execute(stmt)
                await session.commit()
                
                return result.rowcount > 0
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error updating notification: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def delete(self, entity_id: str) -> bool:
        """Delete notification"""
        async with self.adapter.get_session() as session:
            try:
                stmt = delete(NotificationModel).where(NotificationModel.notification_id == entity_id)
                result = await session.execute(stmt)
                await session.commit()
                
                return result.rowcount > 0
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error deleting notification: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List notifications with pagination"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(NotificationModel)
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if hasattr(NotificationModel, key):
                            stmt = stmt.where(getattr(NotificationModel, key) == value)
                
                stmt = stmt.offset(offset).limit(limit).order_by(NotificationModel.created_at.desc())
                
                result = await session.execute(stmt)
                notifications = result.scalars().all()
                
                return [notification.to_dict() for notification in notifications]
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error listing notifications: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count notifications"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(func.count(NotificationModel.notification_id))
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if hasattr(NotificationModel, key):
                            stmt = stmt.where(getattr(NotificationModel, key) == value)
                
                result = await session.execute(stmt)
                return result.scalar()
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error counting notifications: {e}")
                raise ServiceUnavailableException("PostgreSQL") 
        """Get user by ID"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(UserModel).where(UserModel.user_id == entity_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                return user.to_dict() if user else None
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error getting user by ID: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(UserModel).where(UserModel.email == email)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                return user.to_dict() if user else None
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error getting user by email: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def create_user(self, name: str, email: str, age: Optional[int] = None,
                         meta_data: Dict[str, Any] = None) -> str:
        """Create user with specific fields"""
        user_data = {
            "name": name,
            "email": email,
            "age": age,
            "meta_data": meta_data or {}
        }
        return await self.create(user_data)
    
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update user"""
        async with self.adapter.get_session() as session:
            try:
                updates["updated_at"] = datetime.utcnow()
                
                stmt = update(UserModel).where(UserModel.user_id == entity_id).values(**updates)
                result = await session.execute(stmt)
                await session.commit()
                
                return result.rowcount > 0
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error updating user: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def delete(self, entity_id: str) -> bool:
        """Delete user"""
        async with self.adapter.get_session() as session:
            try:
                stmt = delete(UserModel).where(UserModel.user_id == entity_id)
                result = await session.execute(stmt)
                await session.commit()
                
                return result.rowcount > 0
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error deleting user: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def list(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List users with pagination"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(UserModel)
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if hasattr(UserModel, key):
                            stmt = stmt.where(getattr(UserModel, key) == value)
                
                stmt = stmt.offset(offset).limit(limit).order_by(UserModel.created_at.desc())
                
                result = await session.execute(stmt)
                users = result.scalars().all()
                
                return [user.to_dict() for user in users]
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error listing users: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """Count users"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(func.count(UserModel.user_id))
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if hasattr(UserModel, key):
                            stmt = stmt.where(getattr(UserModel, key) == value)
                
                result = await session.execute(stmt)
                return result.scalar()
                
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL error counting users: {e}")
                raise ServiceUnavailableException("PostgreSQL")


class PostgreSQLPaymentRepository(IPaymentRepository):
    """PostgreSQL Payment Repository implementation"""
    
    def __init__(self, postgresql_adapter: PostgreSQLAdapter):
        self.adapter = postgresql_adapter
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create payment"""
        async with self.adapter.get_session() as session:
            try:
                payment = PaymentModel(**entity)
                session.add(payment)
                await session.commit()
                
                logger.info(f"Created payment: {payment.payment_id}")
                return payment.payment_id
                
            except IntegrityError as e:
                await session.rollback()
                raise ValidationException(f"Database constraint error: {e}")
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"PostgreSQL error creating payment: {e}")
                raise ServiceUnavailableException("PostgreSQL")
    
