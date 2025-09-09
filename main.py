# main.py
import asyncio
import sys
import argparse
from typing import List
from loguru import logger

from config.settings import get_settings
from adapters.inbound.http.app import create_app
from adapters.inbound.kafka.consumer import KafkaConsumerAdapter
from adapters.inbound.celery.worker import celery_app


class Application:
    """Main application orchestrator"""
    
    def __init__(self):
        self.settings = get_settings()
        self.adapters = []
        self.running = False
    
    async def run_http(self) -> None:
        """Run HTTP server"""
        import uvicorn
        
        app = create_app()
        
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level=self.settings.log_level.lower(),
            reload=self.settings.debug
        )
        
        server = uvicorn.Server(config)
        logger.info("Starting HTTP server on port 8000...")
        await server.serve()
    
    async def run_kafka(self) -> None:
        """Run Kafka consumer"""
        consumer = KafkaConsumerAdapter()
        self.adapters.append(consumer)
        
        try:
            await consumer.start()
            logger.info("Kafka consumer started, waiting for messages...")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await consumer.stop()
    
    def run_celery(self) -> None:
        """Run Celery worker"""
        logger.info("Starting Celery worker...")
        
        # Run celery worker
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--queues=default,users,payments'
        ])
    
    async def run_combined(self, adapters: List[str]) -> None:
        """Run multiple adapters together"""
        tasks = []
        
        if "kafka" in adapters:
            consumer = KafkaConsumerAdapter()
            self.adapters.append(consumer)
            await consumer.start()
            logger.info("Kafka consumer started")
        
        if "http" in adapters:
            # For combined mode, we'll run HTTP in the background
            import uvicorn
            app = create_app()
            
            config = uvicorn.Config(
                app,
                host="0.0.0.0", 
                port=8000,
                log_level=self.settings.log_level.lower()
            )
            
            server = uvicorn.Server(config)
            tasks.append(asyncio.create_task(server.serve()))
            logger.info("HTTP server started on port 8000")
        
        if tasks:
            try:
                # Wait for all tasks
                await asyncio.gather(*tasks)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
            finally:
                # Cleanup adapters
                for adapter in self.adapters:
                    if hasattr(adapter, 'stop'):
                        await adapter.stop()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="FastAPI Hexagonal Architecture")
    parser.add_argument(
        "--adapter",
        choices=["http", "kafka", "celery", "combined"],
        default="http",
        help="Adapter to run (default: http)"
    )
    parser.add_argument(
        "--combined-adapters",
        nargs="+",
        choices=["http", "kafka"],
        default=["http", "kafka"],
        help="Adapters to run in combined mode"
    )
    
    args = parser.parse_args()
    
    app = Application()
    
    try:
        if args.adapter == "http":
            await app.run_http()
        elif args.adapter == "kafka":
            await app.run_kafka()
        elif args.adapter == "celery":
            app.run_celery()  # Celery runs synchronously
        elif args.adapter == "combined":
            await app.run_combined(args.combined_adapters)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())