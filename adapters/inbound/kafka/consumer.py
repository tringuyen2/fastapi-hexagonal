# adapters/inbound/kafka/consumer.py
from typing import Dict, Any, Optional
import json
import asyncio
import threading
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from loguru import logger

from config.settings import get_settings
from core.registry import registry, HandlerType
from .config import KafkaConsumerConfig


class KafkaConsumerAdapter:
    """Kafka consumer adapter for handling events"""
    
    def __init__(self):
        self.settings = get_settings()
        self.config = KafkaConsumerConfig(
            bootstrap_servers=self.settings.kafka.bootstrap_servers,
            group_id=self.settings.kafka.group_id,
            auto_offset_reset=self.settings.kafka.auto_offset_reset
        )
        self.consumer: Optional[KafkaConsumer] = None
        self.consumer_thread: Optional[threading.Thread] = None
        self.running = False
    
    async def start(self) -> None:
        """Start Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                *list(self.config.topic_mappings.keys()),
                bootstrap_servers=self.config.bootstrap_servers,
                group_id=self.config.group_id,
                auto_offset_reset=self.config.auto_offset_reset,
                enable_auto_commit=self.config.enable_auto_commit,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
            
            self.running = True
            
            # Start consumer in separate thread
            self.consumer_thread = threading.Thread(
                target=self._consume_messages,
                daemon=True
            )
            self.consumer_thread.start()
            
            logger.info("Kafka consumer started")
            
        except KafkaError as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop Kafka consumer"""
        self.running = False
        
        if self.consumer:
            self.consumer.close()
        
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
        
        logger.info("Kafka consumer stopped")
    
    def _consume_messages(self) -> None:
        """Consume messages from Kafka topics"""
        logger.info("Starting Kafka message consumption...")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                # Process message in async context
                asyncio.run(self._process_message(message))
                
        except Exception as e:
            logger.error(f"Error in Kafka message consumption: {e}")
        finally:
            logger.info("Kafka message consumption stopped")
    
    async def _process_message(self, message) -> None:
        """Process individual Kafka message"""
        try:
            topic = message.topic
            key = message.key
            value = message.value
            
            logger.info(f"Processing Kafka message from topic {topic}: {key}")
            
            # Get operation from topic mapping
            operation = self.config.topic_mappings.get(topic)
            if not operation:
                logger.warning(f"No operation mapping found for topic: {topic}")
                return
            
            # Get handler from registry
            handler = registry.get_handler(operation, HandlerType.KAFKA)
            
            # Prepare context
            context = {
                "topic": topic,
                "key": key,
                "offset": message.offset,
                "partition": message.partition,
                "correlation_id": value.get("correlation_id") if isinstance(value, dict) else key
            }
            
            # Extract data from message
            data = value.get("data", {}) if isinstance(value, dict) else value or {}
            
            # Execute handler
            result = await handler.handle(data, context)
            
            if result["success"]:
                logger.info(f"Kafka message processed successfully: {key}")
            else:
                logger.warning(f"Kafka message processing failed: {key} - {result.get('message')}")
                
        except Exception as e:
            logger.error(f"Error processing Kafka message: {e}")