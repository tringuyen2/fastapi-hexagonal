# adapters/inbound/http/routers/users.py
from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from core.registry import registry, HandlerType
from ..serializers import APIResponse, CreateUserRequest, UpdateUserRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=APIResponse)
async def create_user(request: CreateUserRequest, http_request: Request):
    """Create a new user"""
    try:
        # Get handler from registry
        handler = registry.get_handler("create_user", HandlerType.HTTP)
        
        # Prepare context
        context = {
            "operation": "create",
            "request_id": getattr(http_request.state, "request_id", None)
        }
        
        # Execute handler
        result = await handler.handle(request.dict(), context)
        
        if result["success"]:
            return APIResponse(
                success=True,
                data=result["data"],
                execution_time_ms=result.get("execution_time_ms")
            )
        else:
            return APIResponse(
                success=False,
                error_code=result.get("error_code"),
                message=result.get("message")
            )
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{user_id}", response_model=APIResponse)
async def update_user(user_id: str, request: UpdateUserRequest, http_request: Request):
    """Update a user"""
    try:
        # Get handler from registry
        handler = registry.get_handler("create_user", HandlerType.HTTP)  # Same handler, different operation
        
        # Prepare context
        context = {
            "operation": "update",
            "user_id": user_id,
            "request_id": getattr(http_request.state, "request_id", None)
        }
        
        # Execute handler
        result = await handler.handle(request.dict(exclude_unset=True), context)
        
        if result["success"]:
            return APIResponse(
                success=True,
                data=result["data"],
                execution_time_ms=result.get("execution_time_ms")
            )
        else:
            return APIResponse(
                success=False,
                error_code=result.get("error_code"),
                message=result.get("message")
            )
            
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user(user_id: str, http_request: Request):
    """Delete a user"""
    try:
        # Get handler from registry
        handler = registry.get_handler("create_user", HandlerType.HTTP)  # Same handler, different operation
        
        # Prepare context
        context = {
            "operation": "delete",
            "user_id": user_id,
            "request_id": getattr(http_request.state, "request_id", None)
        }
        
        # Execute handler
        result = await handler.handle({}, context)
        
        if result["success"]:
            return APIResponse(
                success=True,
                data=result["data"],
                execution_time_ms=result.get("execution_time_ms")
            )
        else:
            return APIResponse(
                success=False,
                error_code=result.get("error_code"),
                message=result.get("message")
            )
            
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
