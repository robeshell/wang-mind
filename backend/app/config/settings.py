from pydantic_settings import BaseSettings
from typing import Dict, Optional
import os

class Settings(BaseSettings):
    # 基础配置
    APP_NAME: str = "AI MindMap"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # OpenAI 配置
    OPENAI_API_KEY: str = ""  # 从环境变量获取
    OPENAI_API_BASE: str = "https://api.openai.com/v1"  # 默认 API 地址
    OPENAI_MODEL: str = "gpt-4-1106-preview"  # 使用 GPT-4
    
    # LangChain配置
    CHUNK_SIZE: int = 12000  # 更大的块大小
    CHUNK_OVERLAP: int = 200  # 更小的重叠度
    TEMPERATURE: float = 0.7  # 默认温度
    
    # 场景温度配置
    TEMPERATURE_MINDMAP: float = 0.8  # 思维导图生成的温度
    TEMPERATURE_SUMMARY: float = 1.0      # 摘要生成 - 数据抽取/分析
    TEMPERATURE_STRUCTURE: float = 1.0    # 文档结构分析 - 数据抽取/分析
    TEMPERATURE_ABSTRACT: float = 1.0     # 摘要部分处理 - 数据抽取/分析
    TEMPERATURE_INTRODUCTION: float = 1.0  # 引言部分处理 - 数据抽取/分析
    TEMPERATURE_METHOD: float = 1.0       # 方法部分处理 - 数据抽取/分析
    TEMPERATURE_RESULT: float = 1.0       # 结果部分处理 - 数据抽取/分析
    TEMPERATURE_CONCLUSION: float = 1.0    # 结论部分处理 - 数据抽取/分析
    TEMPERATURE_GENERAL: float = 1.0      # 通用内容处理 - 数据抽取/分析
    TEMPERATURE_RELATIONSHIP: float = 1.3  # 关系分析 - 需要一定创造性
    
    # LLM 配置
    TIMEOUT: int = 30  # 减少超时时间到 30 秒
    MAX_RETRIES: int = 3  # 最大重试次数
    REQUEST_TIMEOUT: int = 120  # 请求超时时间(秒)
    
    # API 配置
    API_TIMEOUT: int = 1800  # 30分钟超时
    API_MAX_RETRIES: int = 3
    API_RETRY_DELAY: float = 1.0
    API_KEEPALIVE_TIMEOUT: int = 60  # 1分钟无内容超时
    API_MAX_EMPTY_LINES: int = 100  # 最大连续空行数
    
    # 流式输出配置
    STREAM_CHUNK_SIZE: int = 100
    STREAM_PROGRESS_INTERVAL: int = 5  # 每5秒更新一次进度
    
    # LLM 质量控制配置
    TOP_P: float = 0.7  # 控制输出的多样性
    PRESENCE_PENALTY: float = 0.0  # 控制话题重复度
    FREQUENCY_PENALTY: float = 0.0  # 控制词语重复度
    
    # 文本处理配置
    MIN_CHUNK_LENGTH: int = 2000  # 最小块长度
    MAX_SUMMARY_LENGTH: int = 5000  # 最大摘要长度
    MAX_MINDMAP_DEPTH: int = 3  # 思维导图最大深度
    
    # 缓存配置
    CACHE_EXPIRE_TIME: int = 3600  # 缓存过期时间（秒）
    MAX_CACHE_ITEMS: int = 1000  # 最大缓存条目数
    
    # 并发配置
    MAX_CONCURRENT_REQUESTS: int = 3  # 并发限制
    MAX_WORKERS: int = 5  # 最大工作线程数
    CHUNK_BATCH_SIZE: int = 3  # 批处理大小
    
    # 文本处理配置
    MAX_INPUT_TOKENS: int = 128000  # GPT-4 最大输入长度限制
    CHINESE_CHARS_PER_TOKEN: float = 0.7  # 中文字符到 token 的估算比例（GPT-4）
    
    # LLM 生成参数
    LLM_TEMPERATURE: float = 0.6  # 降低温度以增加专业性
    LLM_PRESENCE_PENALTY: float = 0.3  # 增加惩罚以避免重复
    LLM_FREQUENCY_PENALTY: float = 0.3  # 进一步鼓励使用专业术语
    LLM_TOP_P: float = 0.7  # 降低采样范围以增加确定性
    LLM_MAX_TOKENS: int = 4000  # 进一步增加长度限制
    
    # 文本处理参数
    TEXT_HEAD_RATIO: float = 0.8  # 增加前文本的比例
    TEXT_TAIL_RATIO: float = 0.2  # 减少后文本的比例
    CACHE_KEY_LENGTH: int = 1000  # 缓存键的文本长度
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"
    }

# 创建单例实例
settings = Settings()

# 确保导出 settings 实例
__all__ = ['settings']

# 验证必要的配置
assert settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"), (
    "Invalid OPENAI_API_KEY format. It should start with 'sk-'"
) 