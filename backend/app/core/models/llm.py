from langchain_openai import ChatOpenAI
from app.config.settings import settings
from app.utils.logger import get_logger
import httpx

logger = get_logger()

def get_llm(temperature: float = None):
    """获取 LLM 实例"""
    try:
        logger.info(f"使用模型: {settings.OPENAI_MODEL}")
        logger.info(f"API Base URL: {settings.OPENAI_API_BASE}")
        logger.info(f"API Key: {settings.OPENAI_API_KEY[:8]}...{settings.OPENAI_API_KEY[-4:]}")
        
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
            
        if not settings.OPENAI_API_KEY.startswith("sk-"):
            raise ValueError("Invalid OPENAI_API_KEY format")
        
        llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            temperature=temperature if temperature is not None else settings.TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            max_retries=settings.MAX_RETRIES,
            request_timeout=settings.REQUEST_TIMEOUT,
            streaming=False,
            http_client=httpx.Client(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=30.0,
                    write=30.0,
                    pool=30.0
                ),
                verify=False  # 临时禁用 SSL 验证以便调试
            )
        )
        
        return llm
        
    except Exception as e:
        logger.error(f"初始化 LLM 失败: {str(e)}")
        raise 