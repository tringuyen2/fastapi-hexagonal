# config/settings.py
from typing import Dict, Any, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import yaml
import os
from pathlib import Path


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    type: str = Field(default="sqlite")
    
    # PostgreSQL
    pg_host: str = Field(default="localhost")
    pg_port: int = Field(default=5432)
    pg_database: str = Field(default="fastapi_hexagonal")
    pg_username: str = Field(default="postgres")
    pg_password: str = Field(default="postgres")
    pg_pool_size: int = Field(default=10)
    
    # MongoDB
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    mongodb_database: str = Field(default="fastapi_hexagonal")
    
    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379/0")
    max_connections: int = Field(default=20)
    
    class Config:
        env_prefix = "REDIS_"


class KafkaConfig(BaseSettings):
    """Kafka configuration"""
    bootstrap_servers: List[str] = Field(default=["localhost:9092"])
    group_id: str = Field(default="fastapi-hexagonal")
    auto_offset_reset: str = Field(default="latest")
    
    class Config:
        env_prefix = "KAFKA_"


class AppSettings(BaseSettings):
    """Main application settings"""
    name: str = Field(default="FastAPI Hexagonal")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")
    
    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    
    # External services
    email_service_api_key: str = Field(default="mock_key")
    payment_gateway_api_key: str = Field(default="mock_key")
    payment_gateway_url: str = Field(default="https://mock-payment.example.com")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            # Load environment-specific YAML config
            def yaml_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
                config_path = Path(f"config/environments/{settings.environment}.yaml")
                if config_path.exists():
                    with open(config_path, 'r') as file:
                        return yaml.safe_load(file) or {}
                return {}
            
            return (
                init_settings,
                yaml_config_settings_source,
                env_settings,
                file_secret_settings,
            )


def get_settings() -> AppSettings:
    """Get application settings instance"""
    return AppSettings()