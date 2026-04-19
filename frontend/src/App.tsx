import { useState, useCallback } from 'react';
import Board from './components/Board';
import { createInitialGameState, positionToCoordinate } from './utils/board';
import { GameState, GAME_MODES, LLMConfig } from './types';
import './App.css';

const COLUMN_LABELS = 'ABCDEFGHJKLMNOPQRST';

function coordinateToPosition(coord: string): [number, number] | null {
  const match = coord.match(/^([A-HJ-T])([1-9]|1[0-9])$/i);
  if (!match) return null;
  const col = match[1].toUpperCase();
  const row = parseInt(match[2], 10);
  const x = COLUMN_LABELS.indexOf(col);
  if (x === -1) return null;
  const y = row - 1;
  if (y < 0 || y >= 19) return null;
  return [x, y];
}

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
  const [gameId, setGameId] = useState<string | null>(null);

  const handleStonePlaced = useCallback(
    async (x: number, y: number) => {
      if (!gameId) {
        alert('请先开始游戏');
        return;
      }

      // 将索引转换为围棋坐标
      const coord = positionToCoordinate(x, y);
      if (!coord) return;

      try {
        const response = await fetch(`/api/game/${gameId}/move`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ coordinate: coord }),
        });
        if (response.ok) {
          const newState = await response.json();
          setGameState(newState);
        } else {
          const err = await response.json();
          alert(err.detail || '落子失败');
        }
      } catch (error) {
        console.error('Move failed:', error);
        alert('网络错误，请重试');
      }
    },
    [gameId]
  );

  const startNewGame = async (selectedMode: string) => {
    try {
      const response = await fetch('/api/game/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: selectedMode, board_size: 19 }),
      });

      if (response.ok) {
        const data = await response.json();
        setGameId(data.game_id);
        setGameState(data.state);
        setMode(selectedMode);
        setAiThinking(false);
      } else {
        alert('无法开始新游戏');
      }
    } catch (error) {
      console.error('Start game failed:', error);
      alert('网络错误，请重试');
    }
  };

  const requestAiMove = async () => {
    if (aiThinking) return;
    if (!llmConfig.apiKey) {
      alert('请先填写 API Key');
      return;
    }
    setAiThinking(true);
    try {
      const response = await fetch('/api/ai/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_state: gameState,
          mode: 'play',
          llm_config: llmConfig,
        }),
      });
      if (response.ok) {
        const data = await response.json();
        const move = data.move;
        if (move) {
          const pos = coordinateToPosition(move);
          if (pos) {
            const [x, y] = pos;
            await handleStonePlaced(x, y);
          } else {
            alert(`AI 返回了无效坐标: ${move}`);
          }
        } else {
          alert('AI 未返回有效着法');
        }
      } else {
        const err = await response.json();
        alert(err.detail || 'AI 请求失败');
      }
    } catch (error) {
      console.error('AI move failed:', error);
      alert('网络错误');
    } finally {
      setAiThinking(false);
    }
  };

  const handleUndo = () => {
    // TODO: 后端实现悔棋 API 后启用
    alert('悔棋功能开发中');
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
            <button onClick={() => startNewGame(mode)}>重新开始</button>
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
