"""
围棋棋盘状态表示

Phase 2: 实现完整的围棋规则引擎
- 气 (liberties)
- 提子 (capture)
- 打劫 (ko)
- 自杀禁止
"""

from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field
from copy import deepcopy
from datetime import datetime

# 常量定义
BOARD_SIZE = 19

# 玩家颜色
Player = str  # "B" (黑) 或 "W" (白)

# 坐标类型
Position = Tuple[int, int]  # (x, y)，范围 0-18


@dataclass
class Stone:
    """棋子"""
    color: Player
    x: int
    y: int


@dataclass
class Chain:
    """相连的棋串"""
    stones: List[Stone] = field(default_factory=list)
    liberties: Set[Position] = field(default_factory=set)

    def __len__(self) -> int:
        return len(self.stones)


class Board:
    """
    围棋棋盘状态

    核心功能：
    - 落子验证
    - 气的计算
    - 提子逻辑
    - 打劫检测
    - 自杀规则
    """

    def __init__(self, size: int = 19):
        self.size = size
        # 棋盘: None=空, "B"=黑, "W"=白
        self.grid: List[List[Optional[Player]]] = [
            [None for _ in range(size)] for _ in range(size)
        ]
        # 移动历史（用于复盘和统计）
        self.moves: List[MoveRecord] = []
        # 棋盘快照历史（用于打劫检测）
        self.snapshots: List[BoardSnapshot] = []

    def copy(self) -> 'Board':
        """深拷贝棋盘状态"""
        new_board = Board(self.size)
        new_board.grid = [row[:] for row in self.grid]
        return new_board

    def is_on_board(self, x: int, y: int) -> bool:
        """检查坐标是否在棋盘内"""
        return 0 <= x < self.size and 0 <= y < self.size

    def get(self, x: int, y: int) -> Optional[Player]:
        """获取指定位置棋子颜色"""
        if not self.is_on_board(x, y):
            return None
        return self.grid[x][y]

    def set(self, x: int, y: int, color: Optional[Player]) -> None:
        """设置指定位置棋子"""
        self.grid[x][y] = color

    def is_empty(self, x: int, y: int) -> bool:
        """检查位置是否为空"""
        return self.get(x, y) is None

    def get_neighbors(self, x: int, y: int) -> List[Position]:
        """获取相邻的四个位置（上下左右）"""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.is_on_board(nx, ny):
                neighbors.append((nx, ny))
        return neighbors

    def find_chain(self, start_x: int, start_y: int) -> Chain:
        """
         flood fill 查找相连的同色棋子串

        Returns:
            Chain: 包含所有相连棋子及其气的集合
        """
        start_color = self.get(start_x, start_y)
        if start_color is None:
            return Chain()

        visited: Set[Position] = set()
        chain_stones: List[Stone] = []
        liberties: Set[Position] = set()

        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            stone = Stone(color=start_color, x=x, y=y)
            chain_stones.append(stone)

            # 检查相邻位置
            for nx, ny in self.get_neighbors(x, y):
                neighbor_color = self.get(nx, ny)
                if neighbor_color is None:
                    # 空点是气
                    liberties.add((nx, ny))
                elif neighbor_color == start_color and (nx, ny) not in visited:
                    # 同色棋子继续搜索
                    stack.append((nx, ny))

        return Chain(stones=chain_stones, liberties=liberties)

    def get_chain_liberties(self, x: int, y: int) -> int:
        """获取指定位置棋子串的气数"""
        chain = self.find_chain(x, y)
        return len(chain.liberties)

    def remove_chain(self, x: int, y: int) -> List[Position]:
        """
        提掉指定位置的整个棋串

        Returns:
            被提掉的所有棋子位置列表
        """
        chain = self.find_chain(x, y)
        removed_positions = []

        for stone in chain.stones:
            self.set(stone.x, stone.y, None)
            removed_positions.append((stone.x, stone.y))

        return removed_positions

    def find_all_chains_of_color(self, color: Player) -> List[Chain]:
        """查找所有指定颜色的棋串（用于自杀检测）"""
        visited: Set[Position] = set()
        chains: List[Chain] = []

        for x in range(self.size):
            for y in range(self.size):
                if self.get(x, y) == color and (x, y) not in visited:
                    chain = self.find_chain(x, y)
                    # 标记已访问
                    for stone in chain.stones:
                        visited.add((stone.x, stone.y))
                    chains.append(chain)

        return chains

    def would_suicide(self, x: int, y: int, color: Player) -> bool:
        """
        检查落子是否会导致自杀（自己的气为 0）

        规则：落子后，如果自己的棋子串气为 0 且没有提掉对手棋子，则非法
        """
        # 模拟落子
        self.set(x, y, color)

        # 查找刚落子形成的棋串
        chain = self.find_chain(x, y)

        # 检查是否有气
        has_liberties = len(chain.liberties) > 0

        # 检查是否提掉了对手棋子
        opponent = "W" if color == "B" else "B"
        opponent_chains = self.find_all_chains_of_color(opponent)
        captured_any = any(len(c.liberties) == 0 for c in opponent_chains)

        # 恢复（不实际修改）
        self.set(x, y, None)

        # 自杀规则：无气且未提子
        return not has_liberties and not captured_any

    def would_violate_ko(self, x: int, y: int, color: Player) -> bool:
        """
        检查是否违反打劫规则

        简单打劫：不能回恢复到对手上一步之前的棋盘状态
        """
        # 需要至少两步历史才能检查打劫
        if len(self.snapshots) < 2:
            return False

        # 模拟落子并提子
        saved = self.copy()
        self.set(x, y, color)

        # 检查对手棋串是否被提
        opponent = "W" if color == "B" else "B"
        captured = []

        for nx, ny in self.get_neighbors(x, y):
            if self.get(nx, ny) == opponent:
                chain = self.find_chain(nx, ny)
                if len(chain.liberties) == 0:
                    captured.extend(chain.stones)

        # 提掉对手棋子
        for stone in captured:
            self.set(stone.x, stone.y, None)

        # 检查是否与上上一步棋盘完全相同（即回到对手上一步前的状态）
        previous_board = self.snapshots[-2]
        if self.equals(previous_board):
            # 恢复
            self.grid = saved.grid
            return True

        # 恢复
        self.grid = saved.grid
        return False

    def is_valid_move(self, x: int, y: int, color: Player) -> Tuple[bool, Optional[str]]:
        """
        验证落子是否合法（考虑提子后的气）

        Returns:
            (是否合法, 错误信息)
        """
        # 1. 位置是否在棋盘内
        if not self.is_on_board(x, y):
            return False, "Position out of bounds"

        # 2. 位置是否为空
        if not self.is_empty(x, y):
            return False, "Position already occupied"

        # 3. 模拟落子并处理提子，然后检查自杀
        saved = self.copy()
        self.set(x, y, color)

        # 检查并移除被提的对手棋串
        opponent = "W" if color == "B" else "B"
        captured = []
        for nx, ny in self.get_neighbors(x, y):
            if self.get(nx, ny) == opponent:
                chain = self.find_chain(nx, ny)
                if len(chain.liberties) == 0:
                    captured.extend(chain.stones)
        for stone in captured:
            self.set(stone.x, stone.y, None)

        # 检查己方棋串（刚落子形成的棋串）是否还有气
        chain = self.find_chain(x, y)
        has_liberties = len(chain.liberties) > 0

        # 恢复棋盘状态
        self.grid = saved.grid

        if not has_liberties:
            return False, "Suicide: no liberties"

        # 4. 打劫规则
        if self.would_violate_ko(x, y, color):
            return False, "Ko rule violation"

        return True, None

    def place(self, x: int, y: int, color: Player) -> List[Position]:
        """
        执行落子（假设已经通过 is_valid_move 验证）

        Returns:
            本轮被提掉的棋子位置列表
        """
        # 落子
        self.set(x, y, color)

        captured = []
        opponent = "W" if color == "B" else "B"

        # 检查对手棋串是否被提
        for nx, ny in self.get_neighbors(x, y):
            if self.get(nx, ny) == opponent:
                chain = self.find_chain(nx, ny)
                if len(chain.liberties) == 0:
                    # 提掉这个棋串
                    removed = self.remove_chain(nx, ny)
                    captured.extend(removed)

        # 记录移动
        move_record = MoveRecord(
            color=color,
            x=x,
            y=y,
            captured=captured.copy(),
            timestamp=datetime.now()
        )
        self.moves.append(move_record)

        # 保存当前快照到历史（用于打劫检测）
        snapshot = self.create_snapshot()
        self.snapshots.append(snapshot)

        # 保持历史长度合理（例如最多 1000 步，或实现 full superko 时可能需要更复杂）
        if len(self.snapshots) > 1000:
            self.snapshots.pop(0)

        return captured

    def create_snapshot(self) -> 'BoardSnapshot':
        """创建棋盘快照（用于打劫检测）"""
        return BoardSnapshot(
            grid=[row[:] for row in self.grid],
            size=self.size
        )

    def equals(self, other: 'BoardSnapshot') -> bool:
        """检查是否与另一个快照完全相同"""
        if self.size != other.size:
            return False
        for x in range(self.size):
            for y in range(self.size):
                if self.grid[x][y] != other.grid[x][y]:
                    return False
        return True

    def to_grid_array(self) -> List[List[Optional[Player]]]:
        """获取网格数组（用于 API 响应）"""
        return [row[:] for row in self.grid]

    def count_stones(self) -> dict:
        """统计黑子和白子数量"""
        counts = {"B": 0, "W": 0}
        for x in range(self.size):
            for y in range(self.size):
                color = self.grid[x][y]
                if color in counts:
                    counts[color] += 1
        return counts


@dataclass
class MoveRecord:
    """落子记录"""
    color: Player
    x: int
    y: int
    captured: List[Position]
    timestamp: datetime


@dataclass
class BoardSnapshot:
    """棋盘快照（不包含历史引用，轻量级）"""
    grid: List[List[Optional[Player]]]
    size: int
