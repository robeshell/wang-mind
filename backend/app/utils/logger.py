from loguru import logger
import sys

# 配置日志
logger.remove()  # 删除默认处理器
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG"
)
logger.add(
    "logs/file_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

def get_logger():
    return logger 