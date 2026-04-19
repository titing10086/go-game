"""
SGF (Smart Game Format) 导入/导出

支持：
- 导出当前游戏状态为 SGF 格式
- 导入 SGF 文件并重建游戏（支持简单线性棋谱）
"""
import re
from typing import List, Tuple, Optional
from datetime import datetime
from .engine.go_rules import GoRules


# SGF 属性：坐标映射
COLUMN_LABELS = 'ABCDEFGHJKLMNOPQRST'
ROW_LABELS = 'abcdefghijklmnopqrst'  # SGF 使用小写字母表示行（1-19）


def coord_to_sgf(x: int, y: int) -> str:
    """将 (x,y) 转换为 SGF 坐标字符串，如 (3,3) -> 'dd'"""
    return f"{COLUMN_LABELS[x].lower()}{ROW_LABELS[y]}"


def sgf_to_coord(s: str) -> Tuple[int, int]:
    """将 SGF 坐标转换为 (x,y) 索引"""
    if len(s) != 2:
        raise ValueError(f"Invalid SGF coordinate: {s}")
    col = s[0].upper()
    row = s[1]
    x = COLUMN_LABELS.index(col)
    y = ROW_LABELS.index(row)
    return (x, y)


def export_game_to_sgf(
    rules: GoRules,
    black_player: str = "Player",
    white_player: str = "AI",
    result: Optional[str] = None,
    date: Optional[datetime] = None,
) -> str:
    """
    导出游戏为 SGF 格式

    Args:
        rules: GoRules 实例（包含完整历史）
        black_player: 黑方名称
        white_player: 白方名称
        result: 对局结果，如 "B+R" (黑方中盘胜) 等
        date: 对局日期

    Returns:
        SGF 字符串
    """
    if date is None:
        date = datetime.now()

    # 游戏信息
    size = rules.board.size
    moves = rules.board.moves

    # 构建 SGF 头部
    sgf = f"(;GM[1]SZ[{size}]"
    sgf += f"DT[{date.strftime('%Y-%m-%d')}]"
    sgf += f"PB[{black_player}]PW[{white_player}]"
    if result:
        sgf += f"RE[{result}]"

    # 添加着法
    for move in moves:
        color_char = 'B' if move.color == 'B' else 'W'
        coord = coord_to_sgf(move.x, move.y)
        sgf += f";{color_char}[{coord}]"

    sgf += ")"
    return sgf


def import_sgf_to_rules(sgf_content: str, board_size: int = 19) -> GoRules:
    """
    从 SGF 内容导入游戏状态

    仅支持简单的线性序列（无分支、无评论）

    Args:
        sgf_content: SGF 文件内容
        board_size: 棋盘大小（默认为19）

    Returns:
        GoRules 实例，包含重建的游戏状态
    """
    rules = GoRules(board_size=board_size)

    # 去除换行和多余空格
    sgf = sgf_content.strip()

    # 简单解析：提取所有 ;B[...] 和 ;W[...] 动作
    pattern = re.compile(r';(B|W)\[([a-z]{2})\]')
    matches = pattern.findall(sgf)

    for color_char, coord in matches:
        color = "B" if color_char == "B" else "W"
        try:
            x, y = sgf_to_coord(coord)
            # 直接调用 play_move_by_coord，它内部会处理规则
            success, captured, msg = rules.play_move_by_coord(f"{COLUMN_LABELS[x]}{y+1}")
            if not success:
                raise ValueError(f"Invalid move {coord}: {msg}")
        except Exception as e:
            raise ValueError(f"Failed to parse move {color_char}[{coord}]: {e}")

    return rules


def parse_sgf_header(sgf_content: str) -> dict:
    """解析 SGF 头部信息"""
    header = {}
    # 提取 GM, SZ, PB, PW, DT, RE 等
    patterns = {
        'GM': r'GM\[(\d+)\]',
        'SZ': r'SZ\[(\d+)\]',
        'PB': r'PB\[([^\]]*)\]',
        'PW': r'PW\[([^\]]*)\]',
        'DT': r'DT\[([^\]]*)\]',
        'RE': r'RE\[([^\]]*)\]',
    }
    for key, pat in patterns.items():
        m = re.search(pat, sgf_content)
        if m:
            header[key] = m.group(1)
    return header
