# core/exceptions.py
from typing import Optional, Dict, Any


class DomainException(Exception):
    """Base domain exception"""
    def __init__(self, message: str, error_code: str = "DOMAIN_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(DomainException):
    """Domain validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(DomainException):
    """Entity not found error"""
    def __init__(self, entity_type: str, entity_id: str):
        message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(message, "NOT_FOUND")


class AlreadyExistsError(DomainException):
    """Entity already exists error"""
    def __init__(self, entity_type: str, identifier: str):
        message = f"{entity_type} with {identifier} already exists"
        super().__init__(message, "ALREADY_EXISTS")


class BusinessRuleViolationError(DomainException):
    """Business rule violation error"""
    def __init__(self, rule: str, details: Optional[str] = None):
        message = f"Business rule violation: {rule}"
        if details:
            message += f" - {details}"
        super().__init__(message, "BUSINESS_RULE_VIOLATION")


# Application layer exceptions
class ApplicationException(Exception):
    """Base application exception"""
    def __init__(self, message: str, error_code: str = "APPLICATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class UseCaseException(ApplicationException):
    """Use case execution error"""
    pass


class CommandValidationError(ApplicationException):
    """Command validation error"""
    def __init__(self, errors: Dict[str, Any]):
        self.errors = errors
        message = f"Command validation failed: {errors}"
        super().__init__(message, "COMMAND_VALIDATION_ERROR")


# Infrastructure exceptions
class InfrastructureException(Exception):
    """Base infrastructure exception"""
    def __init__(self, message: str, error_code: str = "INFRASTRUCTURE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class DatabaseException(InfrastructureException):
    """Database operation error"""
    def __init__(self, operation: str, details: str):
        message = f"Database {operation} failed: {details}"
        super().__init__(message, "DATABASE_ERROR")


class ExternalServiceException(InfrastructureException):
    """External service error"""
    def __init__(self, service_name: str, details: str):
        message = f"External service {service_name} error: {details}"
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")


class MessageBrokerException(InfrastructureException):
    """Message broker error"""
    def __init__(self, operation: str, details: str):
        message = f"Message broker {operation} failed: {details}"
        super().__init__(message, "MESSAGE_BROKER_ERROR")