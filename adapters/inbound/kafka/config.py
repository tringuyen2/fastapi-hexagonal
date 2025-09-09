# adapters/inbound/kafka/config.py
from typing import List, Dict
from pydantic import BaseModel


class KafkaConsumerConfig(BaseModel):
    """Kafka consumer configuration"""
    bootstrap_servers: List[str]
    group_id: str
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 3000
    
    # Topic to operation mapping
    topic_mappings: Dict[str, str] = {
        "user.commands": "create_user",
        "payment.commands": "process_payment"
    }
