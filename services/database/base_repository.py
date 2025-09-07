from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import uuid


class BaseRepository(ABC):
    """Base repository interface"""
    
    def generate_id(self) -> str:
        """Generate unique ID"""
        return str(uuid.uuid4())