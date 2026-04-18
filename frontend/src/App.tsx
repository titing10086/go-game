import { useState, useCallback } from 'react';
import Board from './components/Board';
import { createInitialGameState, placeStone, BOARD_SIZE } from './utils/board';
import { GameState, GAME_MODES, LLMConfig } from './types';
import './App.css';

function App() {
  const [gameState, setGameState] = useState<GameState>(createInitialGameState());
  const [mode, setMode] = useState<string>('pve');
  const [llmConfig, setLLMConfig] = useState<LLMConfig>({
    apiKey: '',
    apiBase: 'https://api.openai.com/v1',
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 512,
  });
  const [aiThinking, setAiThinking] = useState<boolean>(false);

  const handleStonePlaced = useCallback(
    (x: number, y: number) => {
      if (gameState.currentPlayer === 'B' || mode !== 'pve') {
        // 玩家执黑或非人机模式，玩家可以落子
        const result = placeStone(gameState, x, y);
        if (result.success) {
          setGameState({ ...gameState });
        } else {
          alert(result.error);
        }
      }
    },
    [gameState, mode]
  );

  const startNewGame = async (selectedMode: string) => {
    setGameState(createInitialGameState());
    setMode(selectedMode);
    setAiThinking(false);
    // TODO: 通知后端开始新游戏（AI mode）
  };

  const requestAiMove = async () => {
    if (aiThinking) return;
    setAiThinking(true);

    try {
      // TODO: 调用后端 AI API
      // const response = await fetch('/api/ai/move', { ... });
      // 暂时使用模拟延迟
      await new Promise(resolve => setTimeout(resolve, 1000));
      // 模拟 AI 落子
      console.log('AI would make a move here');
    } finally {
      setAiThinking(false);
    }
  };

  const handleUndo = () => {
    if (gameState.history.length > 0) {
      const newHistory = [...gameState.history];
      newHistory.pop();
      const newBoard = createInitialGameState().board;
      // 重建棋盘（简化实现）
      for (const move of newHistory) {
        const [x, y] = coordinateToPosition(move.coordinate)!;
        if (newBoard[x][y].color === null) {
          newBoard[x][y].color = move.color;
        }
      }
      const lastMove = newHistory[newHistory.length - 1];
      const nextPlayer = lastMove ? (lastMove.color === 'B' ? 'W' : 'B') : 'B';

      setGameState({
        ...gameState,
        board: newBoard,
        history: newHistory,
        currentPlayer: nextPlayer,
      });
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>大棋局</h1>
        <p>Go Game AI</p>
      </header>

      <main className="app-main">
        <div className="sidebar">
          <div className="panel">
            <h3>游戏模式</h3>
            {GAME_MODES.map(m => (
              <button
                key={m.id}
                className={`mode-btn${mode === m.id ? ' active' : ''}`}
                onClick={() => startNewGame(m.id)}
                disabled={aiThinking}
              >
                {m.name}
                <small>{m.description}</small>
              </button>
            ))}
          </div>

          <div className="panel">
            <h3>游戏控制</h3>
            <button onClick={() => setGameState(createInitialGameState())}>重新开始</button>
            <button onClick={handleUndo} disabled={gameState.history.length === 0}>
              悔棋
            </button>
            {mode === 'pve' && gameState.currentPlayer === 'W' && !aiThinking && (
              <button onClick={requestAiMove}>AI 落子</button>
            )}
            {aiThinking && <span className="thinking">AI 思考中...</span>}
          </div>

          <div className="panel">
            <h3>当前状态</h3>
            <p>轮到: <strong>{gameState.currentPlayer === 'B' ? '黑方' : '白方'}</strong></p>
            <p>已下: {gameState.history.length} 手</p>
            <p>黑提: {gameState.capturedStones.B} / 白提: {gameState.capturedStones.W}</p>
          </div>

          <div className="panel">
            <h3>AI 配置</h3>
            <div className="form-group">
              <label>API Key</label>
              <input
                type="password"
                value={llmConfig.apiKey}
                onChange={e => setLLMConfig({ ...llmConfig, apiKey: e.target.value })}
                placeholder="sk-..."
              />
            </div>
            <div className="form-group">
              <label>Base URL</label>
              <input
                value={llmConfig.apiBase}
                onChange={e => setLLMConfig({ ...llmConfig, apiBase: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Model</label>
              <input
                value={llmConfig.model}
                onChange={e => setLLMConfig({ ...llmConfig, model: e.target.value })}
              />
            </div>
          </div>
        </div>

        <div className="board-area">
          <Board
            gameState={gameState}
            onStonePlaced={handleStonePlaced}
            disabled={aiThinking}
          />
        </div>
      </main>

      <footer className="app-footer">
        <p>大棋局 &copy; 2026 | 基于 React + FastAPI + LLM</p>
      </footer>
    </div>
  );
}

export default App;
