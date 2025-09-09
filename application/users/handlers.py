# application/users/handlers.py
from typing import Dict, Any
import time
from loguru import logger

from .use_cases import CreateUserUseCase, UpdateUserUseCase, DeleteUserUseCase
from .commands import CreateUserCommand, UpdateUserCommand, DeleteUserCommand
from core.exceptions import DomainException, ApplicationException


class UserCommandHandler:
    """Handler for user commands"""
    
    def __init__(
        self,
        create_user_use_case: CreateUserUseCase,
        update_user_use_case: UpdateUserUseCase,
        delete_user_use_case: DeleteUserUseCase
    ):
        self.create_user_use_case = create_user_use_case
        self.update_user_use_case = update_user_use_case
        self.delete_user_use_case = delete_user_use_case
    
    async def handle_create_user(self, command: CreateUserCommand) -> Dict[str, Any]:
        """Handle create user command"""
        start_time = time.time()
        
        try:
            logger.info(f"Handling create user command for email: {command.email}")
            
            user = await self.create_user_use_case.execute(command)
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"User created successfully: {user.user_id} in {execution_time:.2f}ms")
            
            return {
                "success": True,
                "data": user.to_dict(),
                "execution_time_ms": execution_time
            }
            
        except DomainException as e:
            execution_time = (time.time() - start_time) * 1000
            logger.warning(f"Domain error creating user: {e.message}")
            
            return {
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error creating user: {e}")
            
            return {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "execution_time_ms": execution_time
            }
    
    async def handle_update_user(self, command: UpdateUserCommand) -> Dict[str, Any]:
        """Handle update user command"""
        start_time = time.time()
        
        try:
            logger.info(f"Handling update user command for ID: {command.user_id}")
            
            user = await self.update_user_use_case.execute(command)
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"User updated successfully: {user.user_id} in {execution_time:.2f}ms")
            
            return {
                "success": True,
                "data": user.to_dict(),
                "execution_time_ms": execution_time
            }
            
        except DomainException as e:
            execution_time = (time.time() - start_time) * 1000
            logger.warning(f"Domain error updating user: {e.message}")
            
            return {
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error updating user: {e}")
            
            return {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "execution_time_ms": execution_time
            }
    
    async def handle_delete_user(self, command: DeleteUserCommand) -> Dict[str, Any]:
        """Handle delete user command"""
        start_time = time.time()
        
        try:
            logger.info(f"Handling delete user command for ID: {command.user_id}")
            
            await self.delete_user_use_case.execute(command)
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"User deleted successfully: {command.user_id} in {execution_time:.2f}ms")
            
            return {
                "success": True,
                "data": {"user_id": command.user_id},
                "execution_time_ms": execution_time
            }
            
        except DomainException as e:
            execution_time = (time.time() - start_time) * 1000
            logger.warning(f"Domain error deleting user: {e.message}")
            
            return {
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error deleting user: {e}")
            
            return {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "execution_time_ms": execution_time
            }