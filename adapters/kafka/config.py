# adapters/kafka/config.py
from typing import List, Dict, Any
from pydantic import BaseModel


class KafkaConsumerConfig(BaseModel):
    """Kafka consumer configuration"""
    bootstrap_servers: List[str]
    group_id: str
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 1000
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 3000
    max_poll_records: int = 500
    
    # Topic mappings
    topic_mappings: Dict[str, str] = {
        "user.events": "user.create",
        "payment.events": "payment.process", 
        "notification.events": "notification.send"
    }