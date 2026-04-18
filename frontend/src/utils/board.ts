/**
 * 棋盘逻辑工具
 */

import { Stone, GameState, Move } from '../types';

export const BOARD_SIZE = 19;

// 坐标系转换
export const columnLabels = 'ABCDEFGHJKLMNOPQRST'; // I 跳过，传统围棋棋盘
// 注意：实际棋盘是 19x19，所以使用前19个字母

export function coordinateToPosition(coord: string): [number, number] | null {
  /**
   * 将围棋坐标转换为数组索引
   * 输入: "Q16" -> 返回: [15, 15] (列索引, 行索引)
   */
  const match = coord.match(/^([A-HJ-T])([1-9]|1[0-9])$/);
  if (!match) return null;

  const colChar = match[1];
  const row = parseInt(match[2], 10);

  const colIndex = columnLabels.indexOf(colChar);
  const rowIndex = row - 1;

  if (colIndex === -1 || rowIndex < 0 || rowIndex >= BOARD_SIZE) {
    return null;
  }

  return [colIndex, rowIndex];
}

export function positionToCoordinate(x: number, y: number): string {
  /**
   * 将数组索引转换为围棋坐标
   */
  if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) {
    throw new Error('Invalid position');
  }
  return `${columnLabels[x]}${y + 1}`;
}

export function createEmptyBoard(): Stone[][] => {
  return Array.from({ length: BOARD_SIZE }, () =>
    Array.from({ length: BOARD_SIZE }, () => ({ x: 0, y: 0, color: null }))
  );
}

export function createInitialGameState(): GameState {
  return {
    boardSize: BOARD_SIZE,
    board: createEmptyBoard(),
    currentPlayer: 'B',
    history: [],
    capturedStones: { B: 0, W: 0 },
    isGameOver: false,
  };
}

export function placeStone(
  state: GameState,
  x: number,
  y: number
): { success: boolean; captured: Stone[]; error?: string } {
  /**
   * 尝试在 (x, y) 落子
   * 需要实现完整规则：气、提子、打劫、自杀禁止等
   * 目前为简化版本，仅检查位置是否为空
   */
  if (state.board[x][y].color !== null) {
    return { success: false, captured: [], error: 'Position already occupied' };
  }

  // TODO: 完整的围棋规则引擎
  // 这里先做简单落子，返回空数组表示无提子
  const newBoard = state.board.map(row => row.map(cell => ({ ...cell })));
  newBoard[x][y].color = state.currentPlayer;

  // 更新游戏状态
  state.board = newBoard;
  const move: Move = {
    color: state.currentPlayer,
    coordinate: positionToCoordinate(x, y),
    timestamp: Date.now(),
  };
  state.history.push(move);
  state.currentPlayer = state.currentPlayer === 'B' ? 'W' : 'B';

  return { success: true, captured: [] };
}

export function formatBoardForSGF(state: GameState): string {
  /**
   * 将当前棋盘格式化为 SGF 风格的棋谱
   */
  let sgf = `(;GM[1]SZ[${state.boardSize}]`;
  sgf += `PB[Black]PW[White]`; // 可以设置为 AI 或玩家名称

  for (const move of state.history) {
    const [x, y] = coordinateToPosition(move.coordinate)!;
    const colorChar = move.color === 'B' ? 'B' : 'W';
    // SGF 使用字母表示列，但要注意 I 被跳过
    const colChar = columnLabels[x];
    const rowNum = y + 1;
    sgf += `;${colorChar}[${colChar}${rowNum}]`;
  }

  sgf += ')';
  return sgf;
}
