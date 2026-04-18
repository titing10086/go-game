"""
配置管理：环境变量、API 设置等
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # LLM API 配置
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    DEFAULT_MODEL: str = "gpt-4"

    # 游戏配置
    BOARD_SIZE: int = 19
    MAX_RECENT_MOVES: int = 10  # prompt 中最近手数限制

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
