# adapters/outbound/message_broker/kafka_producer.py
from typing import Dict, Any, Optional
import json
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from loguru import logger

from config.settings import KafkaConfig
from core.exceptions import MessageBrokerException


class KafkaProducerAdapter:
    """Kafka producer adapter for publishing events"""
    
    def __init__(self, config: KafkaConfig):
        self.config = config
        self.producer: Optional[KafkaProducer] = None
    
    async def connect(self) -> None:
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                max_in_flight_requests_per_connection=1  # Ensure ordering
            )
            logger.info("Connected to Kafka for producing events")
            
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise MessageBrokerException("connect", str(e))
    
    async def disconnect(self) -> None:
        """Disconnect from Kafka"""
        if self.producer:
            self.producer.close()
            logger.info("Disconnected from Kafka producer")
    
    async def publish_event(
        self,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        key: Optional[str] = None
    ) -> None:
        """Publish event to Kafka topic"""
        if not self.producer:
            raise MessageBrokerException("publish", "Producer not connected")
        
        try:
            event = {
                "event_type": event_type,
                "data": data,
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "fastapi-hexagonal"
            }
            
            # Send event
            future = self.producer.send(
                topic=topic,
                key=key,
                value=event
            )
            
            # Wait for result (blocking operation)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Published event to {topic}: {event_type} (offset: {record_metadata.offset})")
            
        except KafkaError as e:
            logger.error(f"Failed to publish event to Kafka: {e}")
            raise MessageBrokerException("publish", str(e))
        except Exception as e:
            logger.error(f"Unexpected error publishing to Kafka: {e}")
            raise MessageBrokerException("publish", str(e))