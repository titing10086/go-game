"""
围棋 AI Agent

使用 OpenAI 兼容接口为当前局面选择最佳落点。
"""
import re
import time
from typing import Optional, Tuple
from openai import AsyncOpenAI
from ..schemas import GameState, LLMConfig, AIResponse
from ..engine.go_rules import GoRules


class GoAgent:
    """
    围棋 AI Agent

    负责：
    - 构建围棋局面 prompt
    - 调用 LLM API 获取着法
    - 解析返回的坐标
    """

    # 列字母映射（与 GoRules 一致）
    COLUMN_LABELS = 'ABCDEFGHJKLMNOPQRST'

    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None

    async def get_move(
        self,
        game_state: GameState,
        llm_config: LLMConfig,
        mode: str = "play"
    ) -> AIResponse:
        """
        获取 AI 着法

        Args:
            game_state: 当前游戏状态（包含棋盘）
            llm_config: LLM 配置
            mode: "play"（着法）或 "analyze"（分析）

        Returns:
            AIResponse: 包含着法和可能的分析
        """
        # 初始化客户端（如有必要）
        if self.client is None:
            self.client = AsyncOpenAI(
                api_key=llm_config.api_key,
                base_url=llm_config.api_base
            )

        # 构建 prompt
        prompt = self._build_prompt(game_state, mode)

        try:
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=llm_config.model,
                messages=[
                    {"role": "system", "content": "You are a professional Go player."},
                    {"role": "user", "content": prompt}
                ],
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            )
            thinking_time = time.time() - start_time
            text = response.choices[0].message.content.strip()
        except Exception as e:
            # 发生错误时返回空 move 并将错误信息放入 analysis
            return AIResponse(
                move="",
                analysis=f"AI request failed: {str(e)}",
                thinking_time=0.0
            )

        # 解析坐标
        move = self._extract_coordinate(text)

        # 分析模式下返回完整响应作为分析内容
        analysis = text if mode == "analyze" else None

        return AIResponse(
            move=move,
            analysis=analysis,
            thinking_time=thinking_time
        )

    def _build_prompt(self, game_state: GameState, mode: str) -> str:
        """
        构建 prompt

        包含：
        - 当前执子方
        - 棋盘状态（ASCII 网格）
        - 最近 N 步（可选）
        - 指令
        """
        current_player = game_state.current_player  # "B" or "W"
        player_name = "Black" if current_player == "B" else "White"
        board_size = game_state.board_size

        # 获取棋盘 2D 数组
        board = game_state.board
        if board is None:
            raise ValueError("Game state must include board array")

        # 构建 ASCII 棋盘（19x19）
        lines = []
        # 列标题
        col_header = "    " + " ".join(self.COLUMN_LABELS[:board_size])
        lines.append(col_header)
        for y in range(board_size):
            row_num = f"{y+1:>2}"
            row_str = f"{row_num}  "
            for x in range(board_size):
                cell = board[x][y]
                if cell == "B":
                    row_str += "B "
                elif cell == "W":
                    row_str += "W "
                else:
                    row_str += ". "
            lines.append(row_str.rstrip())

        board_str = "\n".join(lines)

        # 历史着法（最近 10 步）
        history = game_state.history[-10:] if game_state.history else []
        history_str = ", ".join(
            f"{m.coordinate}" for m in history
        ) if history else "none"

        # 提子数
        captured = game_state.captured_stones

        if mode == "play":
            instruction = (
                "It's your turn. You are playing as {player}. "
                "Analyze the board and provide your next move in the format: "
                "`<coordinate>` (e.g., 'D4' or 'Q16'). "
                "Respond with only the coordinate, nothing else."
            ).format(player=player_name)
        else:  # analyze
            instruction = (
                "You are a professional Go commentator. "
                "Analyze the current position and suggest the best move. "
                "Include evaluation and reasoning."
            )

        prompt = f"""You are a professional Go AI. Current game state:

- Board size: {board_size}x{board_size}
- Current player: {player_name} ({current_player})
- Captured stones: Black {captured['B']}, White {captured['W']}
- Recent moves: {history_str}

Board (rows 1-19, columns A-{self.COLUMN_LABELS[board_size-1]}):
{board_str}

{instruction}
"""
        return prompt.strip()

    def _extract_coordinate(self, text: str) -> str:
        """
        从 LLM 响应中提取围棋坐标

        匹配模式如 "D4", "Q16", "k10" 等
        """
        # 移除 markdown 反引号
        text = text.strip("` ").upper()
        # 正则：列字母 (A-H,J-T) + 行号 (1-19)
        pattern = r'([A-HJ-T][1-9]|1[0-9])'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        # 如果没找到，尝试匹配更宽松的格式
        match = re.search(r'([A-HJ-T])([1-9]|1[0-9])', text)
        if match:
            return f"{match.group(1)}{match.group(2)}"
        return ""  # 无法解析
