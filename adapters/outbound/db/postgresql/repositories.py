# adapters/outbound/db/postgresql/repositories.py
from typing import Optional
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from decimal import Decimal

from domain.users.entities import User
from domain.users.value_objects import UserId, UserName, Email, Age
from domain.payments.entities import Payment, PaymentStatus
from domain.payments.value_objects import PaymentId, TransactionId, Money, PaymentMethod
from domain.notifications.entities import Notification, NotificationStatus
from domain.notifications.value_objects import NotificationId, Recipient, NotificationContent, NotificationChannel
from core.exceptions import InfrastructureException, NotFoundError, AlreadyExistsError
from .adapter import PostgreSQLAdapter, UserModel, PaymentModel, NotificationModel


class PostgreSQLUserRepository:
    """PostgreSQL implementation of User repository"""
    
    def __init__(self, adapter: PostgreSQLAdapter):
        self.adapter = adapter
    
    async def create(self, user: User) -> None:
        """Create user in database"""
        async with self.adapter.get_session() as session:
            try:
                user_model = UserModel(
                    user_id=str(user.user_id),
                    name=str(user.name),
                    email=str(user.email),
                    age=int(user.age) if user.age else None,
                    metadata=user.metadata,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
                
                session.add(user_model)
                await session.commit()
                
            except IntegrityError as e:
                await session.rollback()
                if "unique constraint" in str(e).lower():
                    raise AlreadyExistsError("User", f"email={user.email}")
                raise InfrastructureException(f"Database constraint error: {e}")
                
            except SQLAlchemyError as e:
                await session.rollback()
                raise InfrastructureException(f"Database error: {e}")
    
    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get user by ID"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(UserModel).where(UserModel.user_id == str(user_id))
                result = await session.execute(stmt)
                user_model = result.scalar_one_or_none()
                
                if not user_model:
                    return None
                
                return self._model_to_entity(user_model)
                
            except SQLAlchemyError as e:
                raise InfrastructureException(f"Database error: {e}")
    
    async def get_by_email(self, email: Email) -> Optional[User]:
        """Get user by email"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(UserModel).where(UserModel.email == str(email))
                result = await session.execute(stmt)
                user_model = result.scalar_one_or_none()
                
                if not user_model:
                    return None
                
                return self._model_to_entity(user_model)
                
            except SQLAlchemyError as e:
                raise InfrastructureException(f"Database error: {e}")
    
    async def update(self, user: User) -> None:
        """Update user in database"""
        async with self.adapter.get_session() as session:
            try:
                stmt = update(UserModel).where(UserModel.user_id == str(user.user_id)).values(
                    name=str(user.name),
                    age=int(user.age) if user.age else None,
                    metadata=user.metadata,
                    updated_at=user.updated_at
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount == 0:
                    raise NotFoundError("User", str(user.user_id))
                
            except SQLAlchemyError as e:
                await session.rollback()
                raise InfrastructureException(f"Database error: {e}")
    
    async def delete(self, user_id: UserId) -> None:
        """Delete user from database"""
        async with self.adapter.get_session() as session:
            try:
                stmt = delete(UserModel).where(UserModel.user_id == str(user_id))
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount == 0:
                    raise NotFoundError("User", str(user_id))
                
            except SQLAlchemyError as e:
                await session.rollback()
                raise InfrastructureException(f"Database error: {e}")
    
    def _model_to_entity(self, model: UserModel) -> User:
        """Convert database model to domain entity"""
        return User(
            user_id=UserId(model.user_id),
            name=UserName(model.name),
            email=Email(model.email),
            age=Age(model.age) if model.age is not None else None,
            metadata=model.metadata,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class PostgreSQLPaymentRepository:
    """PostgreSQL implementation of Payment repository"""
    
    def __init__(self, adapter: PostgreSQLAdapter):
        self.adapter = adapter
    
    async def create(self, payment: Payment) -> None:
        """Create payment in database"""
        async with self.adapter.get_session() as session:
            try:
                payment_model = PaymentModel(
                    payment_id=str(payment.payment_id),
                    user_id=str(payment.user_id),
                    amount=float(payment.money.amount),
                    currency=payment.money.currency,
                    payment_method=str(payment.payment_method),
                    status=payment.status.value,
                    transaction_id=str(payment.transaction_id) if payment.transaction_id else None,
                    reference=payment.reference,
                    failure_reason=payment.failure_reason,
                    metadata=payment.metadata,
                    created_at=payment.created_at,
                    updated_at=payment.updated_at
                )
                
                session.add(payment_model)
                await session.commit()
                
            except SQLAlchemyError as e:
                await session.rollback()
                raise InfrastructureException(f"Database error: {e}")
    
    async def get_by_id(self, payment_id: PaymentId) -> Optional[Payment]:
        """Get payment by ID"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(PaymentModel).where(PaymentModel.payment_id == str(payment_id))
                result = await session.execute(stmt)
                payment_model = result.scalar_one_or_none()
                
                if not payment_model:
                    return None
                
                return self._model_to_entity(payment_model)
                
            except SQLAlchemyError as e:
                raise InfrastructureException(f"Database error: {e}")
    
    async def update(self, payment: Payment) -> None:
        """Update payment in database"""
        async with self.adapter.get_session() as session:
            try:
                stmt = update(PaymentModel).where(PaymentModel.payment_id == str(payment.payment_id)).values(
                    status=payment.status.value,
                    transaction_id=str(payment.transaction_id) if payment.transaction_id else None,
                    failure_reason=payment.failure_reason,
                    metadata=payment.metadata,
                    updated_at=payment.updated_at
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount == 0:
                    raise NotFoundError("Payment", str(payment.payment_id))
                
            except SQLAlchemyError as e:
                await session.rollback()
                raise InfrastructureException(f"Database error: {e}")
    
    def _model_to_entity(self, model: PaymentModel) -> Payment:
        """Convert database model to domain entity"""
        return Payment(
            payment_id=PaymentId(model.payment_id),
            user_id=UserId(model.user_id),
            money=Money(Decimal(str(model.amount)), model.currency),
            payment_method=PaymentMethod(model.payment_method),
            status=PaymentStatus(model.status),
            transaction_id=TransactionId(model.transaction_id) if model.transaction_id else None,
            reference=model.reference,
            failure_reason=model.failure_reason,
            metadata=model.metadata,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class PostgreSQLNotificationRepository:
    """PostgreSQL implementation of Notification repository"""
    
    def __init__(self, adapter: PostgreSQLAdapter):
        self.adapter = adapter
    
    async def create(self, notification: Notification) -> None:
        """Create notification in database"""
        async with self.adapter.get_session() as session:
            try:
                notification_model = NotificationModel(
                    notification_id=str(notification.notification_id),
                    recipient=str(notification.recipient),
                    channel=notification.recipient.channel.value,
                    subject=notification.content.subject,
                    body=notification.content.body,
                    user_id=str(notification.user_id) if notification.user_id else None,
                    status=notification.status.value,
                    external_id=notification.external_id,
                    template_id=notification.content.template_id,
                    failure_reason=notification.failure_reason,
                    metadata=notification.metadata,
                    sent_at=notification.sent_at,
                    created_at=notification.created_at,
                    updated_at=notification.updated_at
                )
                
                session.add(notification_model)
                await session.commit()
                
            except SQLAlchemyError as e:
                await session.rollback()
                raise InfrastructureException(f"Database error: {e}")
    
    async def get_by_id(self, notification_id: NotificationId) -> Optional[Notification]:
        """Get notification by ID"""
        async with self.adapter.get_session() as session:
            try:
                stmt = select(NotificationModel).where(NotificationModel.notification_id == str(notification_id))
                result = await session.execute(stmt)
                notification_model = result.scalar_one_or_none()
                
                if not notification_model:
                    return None
                
                return self._model_to_entity(notification_model)
                
            except SQLAlchemyError as e:
                raise InfrastructureException(f"Database error: {e}")
    
    async def update(self, notification: Notification) -> None:
        """Update notification in database"""
        async with self.adapter.get_session() as session:
            try:
                stmt = update(NotificationModel).where(NotificationModel.notification_id == str(notification.notification_id)).values(
                    status=notification.status.value,
                    external_id=notification.external_id,
                    failure_reason=notification.failure_reason,
                    sent_at=notification.sent_at,
                    updated_at=notification.updated_at
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount == 0:
                    raise NotFoundError("Notification", str(notification.notification_id))
                
            except SQLAlchemyError as e:
                await session.rollback()
                raise InfrastructureException(f"Database error: {e}")
    
    def _model_to_entity(self, model: NotificationModel) -> Notification:
        """Convert database model to domain entity"""
        from domain.users.value_objects import UserId
        
        return Notification(
            notification_id=NotificationId(model.notification_id),
            recipient=Recipient(model.recipient, NotificationChannel(model.channel)),
            content=NotificationContent(
                subject=model.subject,
                body=model.body,
                template_id=model.template_id
            ),
            user_id=UserId(model.user_id) if model.user_id else None,
            status=NotificationStatus(model.status),
            external_id=model.external_id,
            failure_reason=model.failure_reason,
            metadata=model.metadata,
            sent_at=model.sent_at,
            created_at=model.created_at,
            updated_at=model.updated_at