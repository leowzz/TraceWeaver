#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import logger
from app.core.context import ctx


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理 HTTPException 异常
    """
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}"
    )
    
    try:
        trace_id = ctx.trace_id
    except RuntimeError:
        trace_id = None
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "detail": exc.detail,  # Add for backward compatibility with tests
            "status_code": exc.status_code,
            "trace_id": trace_id,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求验证错误（Pydantic ValidationError）
    """
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        error_messages.append(f"{loc}: {msg}")
    
    error_detail = "; ".join(error_messages)
    
    logger.warning(
        f"Validation error: {error_detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        }
    )
    
    try:
        trace_id = ctx.trace_id
    except RuntimeError:
        trace_id = None
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation error",
            "detail": errors,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "trace_id": trace_id,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未预期的通用异常
    """
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
    )
    
    # 在生产环境中，不暴露详细的错误信息
    message = "Internal server error"
    detail = None
    
    from app.core.config import settings
    if settings.ENVIRONMENT == "local":
        detail = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
    
    try:
        trace_id = ctx.trace_id
    except RuntimeError:
        trace_id = None
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": message,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "trace_id": trace_id,
            **({"detail": detail} if detail else {}),
        },
    )

