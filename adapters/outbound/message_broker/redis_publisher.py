# adapters/outbound/message_broker/redis_publisher.py
from typing import Dict, Any, Optional
import json
from datetime import datetime
import redis.asyncio as redis
from loguru import logger

from config.settings import RedisConfig
from core.exceptions import MessageBrokerException


class RedisPublisherAdapter:
    """Redis publisher adapter for publishing events"""
    
    def __init__(self, config: RedisConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.config.url,
                max_connections=self.config.max_connections,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis for publishing events")
            
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise MessageBrokerException("connect", str(e))
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis publisher")
    
    async def publish_event(
        self,
        channel: str,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """Publish event to Redis channel"""
        if not self.redis_client:
            raise MessageBrokerException("publish", "Redis client not connected")
        
        try:
            event = {
                "event_type": event_type,
                "data": data,
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "fastapi-hexagonal"
            }
            
            # Publish event
            result = await self.redis_client.publish(
                channel,
                json.dumps(event, default=str)
            )
            
            logger.info(f"Published event to Redis channel {channel}: {event_type} (subscribers: {result})")
            
        except redis.RedisError as e:
            logger.error(f"Failed to publish event to Redis: {e}")
            raise MessageBrokerException("publish", str(e))
        except Exception as e:
            logger.error(f"Unexpected error publishing to Redis: {e}")
            raise MessageBrokerException("publish", str(e))
