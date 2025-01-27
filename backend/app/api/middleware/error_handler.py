from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.utils.logger import get_logger

logger = get_logger()

async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"请求处理失败: {str(e)}")
        if isinstance(e, HTTPException):
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": str(e.detail)}
            )
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误"}
        ) 