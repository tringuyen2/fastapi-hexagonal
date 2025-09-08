from typing import Dict, Any, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import yaml
import os


class DatabaseConfig(BaseSettings):
    url: str = Field(default="sqlite:///./event_manager.db")
    echo: bool = Field(default=False)
    
    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    url: str = Field(default="redis://localhost:6379/0")
    max_connections: int = Field(default=20)
    
    class Config:
        env_prefix = "REDIS_"


class KafkaConfig(BaseSettings):
    bootstrap_servers: List[str] = Field(default=["localhost:9092"])
    group_id: str = Field(default="event-manager")
    auto_offset_reset: str = Field(default="latest")
    
    class Config:
        env_prefix = "KAFKA_"


class AppConfig(BaseSettings):
    name: str = Field(default="Event Manager")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Service configs
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    
    # Handler configurations
    handlers_config_path: str = Field(default="config/handlers.yaml")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config() -> AppConfig:
    """Load application configuration"""
    return AppConfig()


def load_handlers_config(config_path: str) -> Dict[str, Any]:
    """Load handlers configuration from YAML"""
    if not os.path.exists(config_path):
        return {}
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file) or {}