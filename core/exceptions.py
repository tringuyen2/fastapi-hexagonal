class EventManagerException(Exception):
    """Base exception for event manager"""
    def __init__(self, message: str, error_code: str = "GENERAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class HandlerNotFoundException(EventManagerException):
    """Handler not found for event type"""
    def __init__(self, event_type: str):
        super().__init__(
            f"No handler found for event type: {event_type}",
            "HANDLER_NOT_FOUND"
        )


class HandlerExecutionException(EventManagerException):
    """Handler execution failed"""
    def __init__(self, handler_name: str, original_error: str):
        super().__init__(
            f"Handler {handler_name} execution failed: {original_error}",
            "HANDLER_EXECUTION_FAILED"
        )


class ValidationException(EventManagerException):
    """Data validation failed"""
    def __init__(self, validation_errors: str):
        super().__init__(
            f"Validation failed: {validation_errors}",
            "VALIDATION_ERROR"
        )


class ServiceUnavailableException(EventManagerException):
    """External service unavailable"""
    def __init__(self, service_name: str):
        super().__init__(
            f"Service {service_name} is unavailable",
            "SERVICE_UNAVAILABLE"
        )