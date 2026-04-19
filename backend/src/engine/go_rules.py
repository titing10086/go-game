"""
围棋规则引擎 (Go Rules Engine)

提供高层 API 用于游戏逻辑：
- 创建游戏棋盘
- 验证并执行落子
- 检测终局（简单占点规则或双方虚手）
"""

from .board import Board, Player, Position, Chain, BoardSnapshot
from typing import List, Tuple, Optional


class RuleViolation(Exception):
    """规则违反异常"""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Rule violation: {reason}")


class GoRules:
    """
    围棋规则管理器

    集成 Board，提供完整的游戏规则接口
    """

    def __init__(self, board_size: int = 19, komi: float = 6.5):
        self.board = Board(board_size)
        self.komi = komi
        self.current_player: Player = "B"  # 黑棋先行
        self.passes_count: int = 0  # 连续虚手次数
        self.is_game_over: bool = False
        self.winner: Optional[Player] = None

        # 围棋坐标映射（列字母 -> 索引）
        self.column_labels = 'ABCDEFGHJKLMNOPQRST'  # 跳过 I

    def coordinate_to_position(self, coord: str) -> Optional[Position]:
        """
        将围棋坐标 (如 "Q16") 转换为 (x, y) 索引

        Returns:
            (x, y) 或 None（如果无效）
        """
        import re
        match = re.match(r'^([A-HJ-T])([1-9]|1[0-9])$', coord.upper())
        if not match:
            return None

        col_char, row_str = match.groups()
        col_index = self.column_labels.find(col_char)
        if col_index == -1 or col_index >= self.board.size:
            return None

        row_index = int(row_str) - 1
        if row_index < 0 or row_index >= self.board.size:
            return None

        return (col_index, row_index)

    def position_to_coordinate(self, x: int, y: int) -> Optional[str]:
        """将索引转换为围棋坐标"""
        if not (0 <= x < self.board.size and 0 <= y < self.board.size):
            return None
        return f"{self.column_labels[x]}{y + 1}"

    def get_board_state(self) -> List[List[Optional[Player]]]:
        """获取当前棋盘"""
        return self.board.to_grid_array()

    def get_current_player(self) -> Player:
        """获取当前轮到谁"""
        return self.current_player

    def is_valid_move(self, x: int, y: int) -> Tuple[bool, Optional[str]]:
        """验证落子是否合法"""
        return self.board.is_valid_move(x, y, self.current_player)

    def play_move(self, x: int, y: int) -> Tuple[bool, List[Position], str]:
        """
        执行落子

        Args:
            x, y: 坐标（0-based）

        Returns:
            (是否成功, 被提掉的棋子列表, 消息/错误)

        Raises:
            RuleViolation: 如果落子违反规则
        """
        valid, reason = self.is_valid_move(x, y)
        if not valid:
            raise RuleViolation(reason)

        # 执行落子
        captured = self.board.place(x, y, self.current_player)

        # 切换玩家
        self.current_player = "W" if self.current_player == "B" else "B"

        return True, captured, f"Move at ({x},{y}) successful"

    def play_pass(self) -> None:
        """虚手（pass）"""
        self.passes_count += 1
        self.current_player = "W" if self.current_player == "B" else "B"

        # 连续两次 pass 结束游戏
        if self.passes_count >= 2:
            self.is_game_over = True
            self._determine_winner()

    def play_move_by_coord(self, coord: str) -> Tuple[bool, List[str], str]:
        """
        通过坐标字符串执行落子（高层 API）

        Args:
            coord: 如 "Q16"

        Returns:
            (成功, 被提掉的棋子坐标列表, 消息)
        """
        pos = self.coordinate_to_position(coord)
        if pos is None:
            raise RuleViolation(f"Invalid coordinate: {coord}")

        x, y = pos
        success, captured, msg = self.play_move(x, y)
        captured_coords = [self.position_to_coordinate(cx, cy) for (cx, cy) in captured]

        # 重置连续 pass 计数
        if success:
            self.passes_count = 0

        return success, captured_coords, msg

    def _determine_winner(self) -> None:
        """
        简单胜负判定：数目法（简化版）

        真实围棋需要：
        - 计算领地（眼）
        - 计算数目（包括 komi）
        - 处理死子
        - 可能需要 TC（ territorial count）或区点规则

        这里采用极简版：直接比较棋子数（这不符合真实围棋，但不影响规则引擎）
        """
        counts = self.board.count_stones()
        black_count = counts["B"]
        white_count = counts["W"] + self.komi  # 白棋加贴目

        if black_count > white_count:
            self.winner = "B"
        elif white_count > black_count:
            self.winner = "W"
        else:
            self.winner = None  # 和棋（罕见）

    def get_score(self) -> dict:
        """获取当前比分（简化版）"""
        counts = self.board.count_stones()
        return {
            "B": counts["B"],
            "W": counts["W"] + self.komi,
            "komi": self.komi,
        }

    def reset(self, board_size: int = 19, komi: float = 6.5) -> None:
        """重置游戏状态"""
        self.board = Board(board_size)
        self.komi = komi
        self.current_player = "B"
        self.passes_count = 0
        self.is_game_over = False
        self.winner = None

    def get_liberties(self, x: int, y: int) -> int:
        """获取指定位置棋子串的气"""
        return self.board.get_chain_liberties(x, y)

    def get_chain(self, x: int, y: int) -> Chain:
        """获取指定位置的棋串"""
        return self.board.find_chain(x, y)

    def is_in_atari(self, x: int, y: int) -> bool:
        """检查棋串是否一气"""
        return self.get_liberties(x, y) == 1

    def get_all_chains(self, color: Player) -> List[Chain]:
        """获取指定颜色的所有棋串"""
        return self.board.find_all_chains_of_color(color)
