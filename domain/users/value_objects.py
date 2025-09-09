# domain/users/value_objects.py
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import re

from core.exceptions import ValidationError


@dataclass(frozen=True)
class Email:
    """Email value object"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValidationError(f"Invalid email format: {self.value}", "email")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class UserId:
    """User ID value object"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValidationError("User ID cannot be empty", "user_id")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class UserName:
    """User name value object"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValidationError("User name cannot be empty", "name")
        if len(self.value) > 100:
            raise ValidationError("User name cannot exceed 100 characters", "name")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Age:
    """Age value object"""
    value: int
    
    def __post_init__(self):
        if self.value < 0:
            raise ValidationError("Age cannot be negative", "age")
        if self.value > 150:
            raise ValidationError("Age cannot exceed 150", "age")
    
    def __int__(self) -> int:
        return self.value