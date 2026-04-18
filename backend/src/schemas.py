"""
Pydantic 数据模型
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class Move(BaseModel):
    """单步棋"""
    color: str  # "B" 或 "W"
    coordinate: str  # 如 "Q16"
    analysis: Optional[str] = None
    timestamp: Optional[datetime] = None


class GameState(BaseModel):
    """游戏状态"""
    game_id: str
    board_size: int = 19
    current_player: str = "B"  # 当前轮到谁
    history: List[Move] = []
    captured_stones: Dict[str, int] = {"B": 0, "W": 0}  # 提子数
    is_game_over: bool = False
    winner: Optional[str] = None


class LLMConfig(BaseModel):
    """LLM 配置"""
    api_key: str
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 512


class AIRequest(BaseModel):
    """AI 走棋请求"""
    game_state: GameState
    mode: str = "play"  # "play" 或 "analyze"
    llm_config: Optional[LLMConfig] = None


class AIResponse(BaseModel):
    """AI 走棋响应"""
    move: str
    analysis: Optional[str] = None
    thinking_time: float = 0.0


class WSMessage(BaseModel):
    """WebSocket 消息"""
    type: str  # "move", "ai_thinking", "game_over", "error"
    data: Dict[str, Any]
