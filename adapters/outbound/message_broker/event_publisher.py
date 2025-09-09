# adapters/outbound/message_broker/event_publisher.py
from typing import Dict, Any, Optional
from loguru import logger

from config.settings import KafkaConfig, RedisConfig
from .kafka_producer import KafkaProducerAdapter
from .redis_publisher import RedisPublisherAdapter


class EventPublisherAdapter:
    """Unified event publisher adapter"""
    
    def __init__(self, kafka_config: KafkaConfig, redis_config: Optional[RedisConfig] = None):
        self.kafka_producer = KafkaProducerAdapter(kafka_config)
        self.redis_publisher = RedisPublisherAdapter(redis_config) if redis_config else None
    
    async def connect(self) -> None:
        """Connect to message brokers"""
        await self.kafka_producer.connect()
        
        if self.redis_publisher:
            await self.redis_publisher.connect()
        
        logger.info("Event publisher connected")
    
    async def disconnect(self) -> None:
        """Disconnect from message brokers"""
        await self.kafka_producer.disconnect()
        
        if self.redis_publisher:
            await self.redis_publisher.disconnect()
        
        logger.info("Event publisher disconnected")
    
    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """Publish event to appropriate channels"""
        try:
            # Determine topic/channel based on event type
            topic = self._get_topic_for_event_type(event_type)
            
            # Publish to Kafka
            await self.kafka_producer.publish_event(
                topic=topic,
                event_type=event_type,
                data=data,
                correlation_id=correlation_id,
                key=correlation_id  # Use correlation_id as key for partitioning
            )
            
            # Also publish to Redis if available (for real-time updates)
            if self.redis_publisher:
                await self.redis_publisher.publish_event(
                    channel=f"events.{event_type}",
                    event_type=event_type,
                    data=data,
                    correlation_id=correlation_id
                )
            
            logger.debug(f"Published event: {event_type}")
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            raise
    
    def _get_topic_for_event_type(self, event_type: str) -> str:
        """Get Kafka topic for event type"""
        if event_type.startswith("user."):
            return "user.events"
        elif event_type.startswith("payment."):
            return "payment.events"
        elif event_type.startswith("notification."):
            return "notification.events"
        else:
            return "general.events"