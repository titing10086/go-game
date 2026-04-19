"""
Pydantic 数据模型
"""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


def to_camel_case(string: str) -> str:
    """将 snake_case 转换为 camelCase"""
    parts = string.split('_')
    return parts[0] + ''.join(word.title() for word in parts[1:])


class Move(BaseModel):
    """单步棋"""
    color: str  # "B" 或 "W"
    coordinate: str  # 如 "Q16"
    analysis: Optional[str] = None
    timestamp: Optional[datetime] = None

    # 启用 camelCase 输出
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel_case)


class GameState(BaseModel):
    """游戏状态"""
    game_id: str
    board_size: int = 19
    current_player: str = "B"  # 当前轮到谁
    history: List[Move] = []
    captured_stones: Dict[str, int] = {"B": 0, "W": 0}  # 提子数
    is_game_over: bool = False
    winner: Optional[str] = None
    board: Optional[List[List[Optional[str]]]] = None  # 棋盘状态：null/"B"/"W"

    # 启用 camelCase 输出
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel_case)


class LLMConfig(BaseModel):
    """LLM 配置"""
    api_key: str
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 512

    # 启用 camelCase 输入/输出
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel_case)


class AIRequest(BaseModel):
    """AI 走棋请求"""
    game_state: GameState
    mode: str = "play"  # "play" 或 "analyze"
    llm_config: Optional[LLMConfig] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel_case)


class AIResponse(BaseModel):
    """AI 走棋响应"""
    move: str
    analysis: Optional[str] = None
    thinking_time: float = 0.0

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel_case)


class WSMessage(BaseModel):
    """WebSocket 消息"""
    type: str  # "move", "ai_thinking", "game_over", "error"
    data: Dict[str, Any]
