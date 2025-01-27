from fastapi import Request
from app.utils.logger import get_logger
import time

logger = get_logger()

async def request_logger(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"完成处理，耗时: {process_time:.2f}秒"
    )
    return response 