"""
Phase 2 规则引擎测试

测试用例：
1. 基本落子
2. 提子（吃子）
3. 自杀禁止
4. 打劫规则
5. 气和棋串
"""

import sys
sys.path.insert(0, '/root/go-game/backend/src')

from engine.go_rules import GoRules

def test_basic_placement():
    print("Test 1: 基本落子")
    rules = GoRules(19)
    rules.play_move(3, 3)  # 黑 D4
    assert rules.board.get(3, 3) == "B"
    assert rules.current_player == "W"
    print("✓ 基本落子 OK")

def test_capture():
    print("Test 2: 提子")
    from engine.board import Board
    b = Board(19)
    # 手动设置局面：黑 C5, D4, D6；白 D5
    b.place(2, 4, 'B')   # C5
    b.place(3, 4, 'W')   # D5
    b.place(3, 3, 'B')   # D4
    b.place(3, 5, 'B')   # D6
    # 此时白 D5 只有一气 E5
    captured = b.place(4, 4, 'B')  # 黑 E5，应提掉白 D5
    assert (3, 4) in captured  # D5 已被提
    assert b.get(3, 4) is None
    print("✓ 提子 OK")

def test_suicide():
    print("Test 3: 自杀禁止")
    rules = GoRules(19)
    # 构造自杀局面：(10,10) 周围全是白子，且白子都有至少一气（不会被提）
    # 黑方尝试落子 (10,10)
    rules.board.set(9, 10, "W")   # 左
    rules.board.set(11, 10, "W")  # 右
    rules.board.set(10, 9, "W")   # 上
    rules.board.set(10, 11, "W")  # 下
    # 现在 (10,10) 四个邻居都是白，且白棋各自有其他气
    valid, reason = rules.is_valid_move(10, 10)
    assert not valid, "应该禁止自杀"
    assert reason == "Suicide: no liberties"
    print("✓ 自杀禁止 OK")

def test_ko():
    print("Test 4: 打劫规则")
    from engine.board import Board

    # 手动构造一个打劫情景
    rules = GoRules(19)
    # 设置当前玩家为白（模拟黑方刚下完一步捕获）
    rules.current_player = "W"
    board = rules.board

    # 构造 S_curr：当前棋盘状态（黑方刚下完一步捕获）
    # 黑子位置 Y = (2,1)，我们需要它的唯一空邻居是 X=(1,1)
    # 用白子占据 Y 的其他邻居，使 Y 除了 X 外没有其他空点
    board.set(2, 1, "B")   # 黑子 Y
    board.set(2, 0, "W")   # 用白子占据 (2,0)，不是黑子，避免扩大黑集团
    board.set(2, 2, "W")   # (2,2) 白
    board.set(3, 1, "W")   # (3,1) 白
    board.set(1, 1, None)  # X 为空（原白子被提）
    # 给 X 一个额外的空邻居以避免 Suicide
    board.set(1, 0, None)  # (1,0) 保持空

    # 记录 S_curr 快照
    S_curr = board.create_snapshot()

    # 构造 S_prev：两步前的棋盘状态
    board.set(1, 1, "W")   # 白子在 (1,1)
    board.set(2, 1, None)  # (2,1) 为空
    # 其他黑子保持不变
    S_prev = board.create_snapshot()

    # 恢复当前棋盘到 S_curr（即黑方刚下完的状态）
    board.grid = [row[:] for row in S_curr.grid]
    # 设置快照历史：先 S_prev 后 S_curr
    board.snapshots = [S_prev, S_curr]

    # 现在测试：白方在 (1,1) 落子应触发打劫违规
    valid, reason = rules.is_valid_move(1, 1)
    assert not valid, "应因打劫禁止回提"
    assert reason == "Ko rule violation", f"期望 Ko rule violation, 实际 {reason}"
    print("✓ 打劫规则 OK")

def test_liberties():
    print("Test 5: 气计算")
    rules = GoRules(19)
    rules.play_move_by_coord("D4")  # 黑
    rules.play_move_by_coord("Q16")  # 白
    # 黑子 D4 应该有 4 气
    libs = rules.get_liberties(3, 3)
    assert libs == 4, f"Expected 4 liberties, got {libs}"
    # 再下 C4 形成两子相连
    rules.play_move_by_coord("C4")
    # 此时 D4 和 C4 是连在一起的，应该有 6 气（两子连接会共享一些气）
    libs_d4 = rules.get_liberties(3, 3)
    libs_c4 = rules.get_liberties(2, 3)
    assert libs_d4 == libs_c4, "相连棋串应有相同的气数"
    print(f"✓ 气计算 OK (D4:{libs_d4}, C4:{libs_c4})")

if __name__ == "__main__":
    print("Running Phase 2 tests...\n")
    test_basic_placement()
    test_capture()
    test_suicide()
    test_ko()
    test_liberties()
    print("\n✅ All tests passed!")
