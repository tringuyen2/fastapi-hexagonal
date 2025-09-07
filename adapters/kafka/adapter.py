# adapters/kafka/adapter.py
import json
import asyncio
from typing import Dict, Any, Optional, List
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import threading

from adapters.base_adapter import BaseAdapter
from adapters.kafka.config import KafkaConsumerConfig
from core.models import EventType, HandlerResult
from core.config import load_config
from loguru import logger


class KafkaAdapter(BaseAdapter):
    """Kafka adapter for event stream processing"""
    
    def __init__(self):
        super().__init__("kafka")
        self.config = load_config()
        self.kafka_config = KafkaConsumerConfig(
            bootstrap_servers=self.config.kafka.bootstrap_servers,
            group_id=self.config.kafka.group_id,
            auto_offset_reset=self.config.kafka.auto_offset_reset
        )
        
        self.consumer = None
        self.producer = None
        self.consumer_thread = None
        self.running = False
    
    async def start(self) -> None:
        """Start Kafka consumer"""
        try:
            # Initialize consumer
            self.consumer = KafkaConsumer(
                *list(self.kafka_config.topic_mappings.keys()),
                bootstrap_servers=self.kafka_config.bootstrap_servers,
                group_id=self.kafka_config.group_id,
                auto_offset_reset=self.kafka_config.auto_offset_reset,
                enable_auto_commit=self.kafka_config.enable_auto_commit,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
            
            # Initialize producer for publishing results
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None
            )
            
            self.running = True
            
            # Start consumer in separate thread
            self.consumer_thread = threading.Thread(
                target=self._consume_messages,
                daemon=True
            )
            self.consumer_thread.start()
            
            logger.info("Kafka adapter started")
            
        except KafkaError as e:
            logger.error(f"Failed to start Kafka adapter: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop Kafka consumer"""
        self.running = False
        
        if self.consumer:
            self.consumer.close()
        
        if self.producer:
            self.producer.close()
        
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
        
        logger.info("Kafka adapter stopped")
    
    def _consume_messages(self):
        """Consume messages from Kafka topics"""
        logger.info("Starting Kafka message consumption...")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                asyncio.run(self._process_kafka_message(message))
                
        except Exception as e:
            logger.error(f"Error in Kafka message consumption: {e}")
        finally:
            logger.info("Kafka message consumption stopped")
    
    async def _process_kafka_message(self, message):
        """Process individual Kafka message"""
        try:
            topic = message.topic
            key = message.key
            value = message.value
            
            logger.info(f"Received Kafka message from topic {topic}: {key}")
            
            # Determine event type from topic
            event_type_str = self.kafka_config.topic_mappings.get(topic)
            if not event_type_str:
                logger.warning(f"No event type mapping found for topic {topic}")
                return
            
            event_type = EventType(event_type_str)
            
            # Extract data from message
            data = value.get('data', {}) if isinstance(value, dict) else {}
            correlation_id = value.get('correlation_id') if isinstance(value, dict) else key
            metadata = value.get('metadata', {}) if isinstance(value, dict) else {}
            
            # Process event
            result = await self.process_event(
                event_type=event_type,
                data=data,
                correlation_id=correlation_id,
                metadata=metadata
            )
            
            # Publish result to result topic
            await self._publish_result(topic, key, result)
            
        except Exception as e:
            logger.error(f"Error processing Kafka message: {e}")
    
    async def _publish_result(self, original_topic: str, key: str, result: HandlerResult):
        """Publish processing result to Kafka"""
        try:
            result_topic = f"{original_topic}.results"
            
            result_data = {
                "success": result.success,
                "status": result.status.value,
                "message": result.message,
                "data": result.data,
                "error_code": result.error_code,
                "execution_time_ms": result.execution_time_ms
            }
            
            # Send result asynchronously
            future = self.producer.send(result_topic, key=key, value=result_data)
            
            # Don't block on result, just log
            try:
                record_metadata = future.get(timeout=1)
                logger.info(f"Published result to {result_topic}: {record_metadata}")
            except Exception as e:
                logger.warning(f"Could not confirm result publication: {e}")
                
        except Exception as e:
            logger.error(f"Error publishing result to Kafka: {e}")
    
    def publish_event(
        self,
        topic: str,
        event_type: EventType,
        data: Dict[str, Any],
        key: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Publish event to Kafka topic"""
        try:
            event_data = {
                "event_type": event_type.value,
                "data": data,
                "correlation_id": correlation_id,
                "metadata": metadata or {}
            }
            
            future = self.producer.send(
                topic,
                key=key,
                value=event_data
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=5)
            logger.info(f"Published event to {topic}: {record_metadata}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing event to Kafka: {e}")
            return False