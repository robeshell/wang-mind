from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from app.config.settings import settings
from app.utils.logger import get_logger
import httpx

logger = get_logger()

def get_llm(temperature: float = None):
    """获取 LLM 实例"""
    try:
        if settings.LLM_TYPE == "ollama":
            logger.info(f"使用 Ollama 模型: {settings.OLLAMA_MODEL}")
            logger.info(f"Ollama Base URL: {settings.OLLAMA_API_BASE}")
            
            return ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_API_BASE,
                temperature=temperature if temperature is not None else settings.TEMPERATURE_MINDMAP,
                num_predict=settings.LLM_MAX_TOKENS
            )
        else:
            logger.info(f"使用模型: {settings.OPENAI_MODEL}")
            logger.info(f"API Base URL: {settings.OPENAI_API_BASE}")
            logger.info(f"API Key: {settings.OPENAI_API_KEY[:8]}...{settings.OPENAI_API_KEY[-4:]}")
            
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
                
            if not settings.OPENAI_API_KEY.startswith("sk-"):
                raise ValueError("Invalid OPENAI_API_KEY format")
            
            return ChatOpenAI(
                model_name=settings.OPENAI_MODEL,
                temperature=temperature if temperature is not None else settings.TEMPERATURE_MINDMAP,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base=settings.OPENAI_API_BASE,
                max_retries=settings.MAX_RETRIES,
                request_timeout=settings.REQUEST_TIMEOUT
            )
            
    except httpx.ConnectError as e:
        logger.error(f"连接 LLM 服务失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"初始化 LLM 失败: {str(e)}")
        raise 