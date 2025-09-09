# domain/users/entities.py
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from .value_objects import UserId, UserName, Email, Age


@dataclass
class User:
    """User domain entity"""
    user_id: UserId
    name: UserName
    email: Email
    age: Optional[Age] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update_name(self, new_name: UserName) -> None:
        """Update user name"""
        self.name = new_name
        self.updated_at = datetime.utcnow()
    
    def update_age(self, new_age: Age) -> None:
        """Update user age"""
        self.age = new_age
        self.updated_at = datetime.utcnow()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": str(self.user_id),
            "name": str(self.name),
            "email": str(self.email),
            "age": int(self.age) if self.age else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create from dictionary"""
        return cls(
            user_id=UserId(data["user_id"]),
            name=UserName(data["name"]),
            email=Email(data["email"]),
            age=Age(data["age"]) if data.get("age") is not None else None,
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow()
        )
