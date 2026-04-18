/**
 * 围棋游戏类型定义
 */

export interface Stone {
  x: number;      // 0-18
  y: number;      // 0-18
  color: 'B' | 'W' | null;
}

export interface Move {
  color: 'B' | 'W';
  coordinate: string; // e.g., "Q16"
  analysis?: string;
  timestamp: number;
}

export interface GameState {
  gameId?: string;
  boardSize: number;
  board: Stone[][];
  currentPlayer: 'B' | 'W';
  history: Move[];
  capturedStones: { B: number; W: number };
  isGameOver: boolean;
  winner?: 'B' | 'W';
  komi?: number;
}

export interface LLMConfig {
  apiKey: string;
  apiBase: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

export interface GameMode {
  id: 'pve' | 'aivsai' | 'review';
  name: string;
  description: string;
}

export const GAME_MODES: GameMode[] = [
  { id: 'pve', name: '人机对战', description: '玩家 vs AI' },
  { id: 'aivsai', name: 'AI 对弈', description: 'AI vs AI' },
  { id: 'review', name: '棋局复盘', description: 'AI 实时点评' },
];
