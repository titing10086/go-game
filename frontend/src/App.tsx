import { useState, useCallback, useEffect, useRef } from 'react';
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

  // AI 配置：分开存储黑方和白方
  const [blackAiConfig, setBlackAiConfig] = useState<LLMConfig>({
    apiKey: '',
    apiBase: 'https://api.openai.com/v1',
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 512,
  });
  const [whiteAiConfig, setWhiteAiConfig] = useState<LLMConfig>({
    apiKey: '',
    apiBase: 'https://api.openai.com/v1',
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 512,
  });

  const [aiThinking, setAiThinking] = useState<boolean>(false);
  const [gameId, setGameId] = useState<string | null>(null);
  const prevPlayerRef = useRef<string | null>(null);

  // 复盘模式状态
  const [reviewState, setReviewState] = useState<GameState | null>(null);
  const [reviewIndex, setReviewIndex] = useState<number>(-1); // -1 表示最新
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 获取当前应使用的 AI 配置
  const getCurrentAiConfig = useCallback((): LLMConfig | null => {
    if (mode === 'pve') {
      return whiteAiConfig; // PVE: AI 作白方
    } else if (mode === 'aivsai') {
      return gameState.currentPlayer === 'B' ? blackAiConfig : whiteAiConfig;
    }
    return null;
  }, [mode, gameState.currentPlayer, blackAiConfig, whiteAiConfig]);

  // 玩家手动落子
  const handleStonePlaced = useCallback(
    async (x: number, y: number) => {
      if (!gameId) {
        alert('请先开始游戏');
        return;
      }

      const coord = positionToCoordinate(x, y);
      if (!coord) return;

      try {
        const response = await fetch(`/api/game/${gameId}/move`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ coordinate: coord, player: gameState.currentPlayer }),
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

  // 触发生 AI 落子（自动调用）
  const triggerAiMove = useCallback(async () => {
    const config = getCurrentAiConfig();
    if (aiThinking || !config || !config.apiKey || !gameId || gameState.isGameOver) {
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
          llm_config: config,
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
            console.warn('Invalid AI move:', move);
          }
        } else {
          console.warn('AI returned no move');
        }
      } else {
        const err = await response.json();
        console.error('AI move request failed:', err);
        // 不弹出提示，避免打扰
      }
    } catch (error) {
      console.error('AI move failed:', error);
    } finally {
      setAiThinking(false);
    }
  }, [aiThinking, gameId, gameState.isGameOver, gameState, handleStonePlaced, getCurrentAiConfig]);

  // 启用自动对战：监听从黑方轮到白方或反之
  useEffect(() => {
    const prev = prevPlayerRef.current;

    // 需要满足：不在思考中、游戏未结束、gameId 存在
    if (aiThinking || !gameId || gameState.isGameOver) {
      prevPlayerRef.current = gameState.currentPlayer;
      return;
    }

    let shouldTrigger = false;

    if (mode === 'pve' && prev === 'B' && gameState.currentPlayer === 'W' && whiteAiConfig.apiKey) {
      shouldTrigger = true;
    } else if (mode === 'aivsai') {
      if (prev === 'B' && gameState.currentPlayer === 'W' && whiteAiConfig.apiKey) {
        shouldTrigger = true;
      } else if (prev === 'W' && gameState.currentPlayer === 'B' && blackAiConfig.apiKey) {
        shouldTrigger = true;
      }
    }

    if (shouldTrigger) {
      const timer = setTimeout(() => {
        triggerAiMove();
      }, 500); // 稍微长一点的延迟，避免 GPU 限制
      return () => clearTimeout(timer);
    }

    // 更新上一玩家记录
    prevPlayerRef.current = gameState.currentPlayer;
  }, [
    gameState.currentPlayer,
    mode,
    aiThinking,
    gameState.isGameOver,
    gameId,
    blackAiConfig.apiKey,
    whiteAiConfig.apiKey,
    triggerAiMove,
  ]);

  const startNewGame = async (selectedMode: string) => {
    try {
      const response = await fetch('/api/game/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: selectedMode, board_size: 19 }),
      });

      if (response.ok) {
        const data = await response.json();
        setGameId(data.gameId || data.game_id);
        setGameState(data.state);
        setMode(selectedMode);
        setAiThinking(false);
        prevPlayerRef.current = data.state.currentPlayer;

        // 重置复盘相关状态
        setReviewState(null);
        setReviewIndex(-1);
        setAnalysis(null);

        // AI vs AI 模式：若黑方 AI 配置已填，自动开始
        if (selectedMode === 'aivsai' && blackAiConfig.apiKey) {
          setTimeout(() => triggerAiMove(), 300);
        }
      } else {
        alert('无法开始新游戏');
      }
    } catch (error) {
      console.error('Start game failed:', error);
      alert('网络错误');
    }
  };

  const handleUndo = () => {
    alert('悔棋功能开发中');
  };

  // 导入 SGF 文件
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      const response = await fetch('/api/game/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sgf_content: text,
          black_name: 'Black',
          white_name: 'White',
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setGameId(data.game_id);
        setGameState(data.state);
        setMode('review'); // 自动进入复盘模式
        setReviewIndex(-1);
        setReviewState(data.state);
        setAnalysis(null);
        alert('SGF 导入成功！');
      } else {
        const err = await response.json();
        alert('导入失败: ' + (err.detail || '未知错误'));
      }
    } catch (error) {
      console.error('SGF import failed:', error);
      alert('导入失败，请重试');
    } finally {
      // 清空 input 以允许重复选择同一文件
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // 导出 SGF
  const exportSGF = async () => {
    if (!gameId) return;
    try {
      const response = await fetch(`/api/game/${gameId}/sgf?black_player=Black&white_player=White`);
      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([data.sgf], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `game_${gameId}.sgf`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        alert('导出失败');
      }
    } catch (error) {
      console.error('SGF export failed:', error);
      alert('导出失败');
    }
  };

  // 获取历史状态（用于复盘）
  const fetchReviewState = useCallback(async (index: number) => {
    if (!gameId) return;
    const url = index < 0
      ? `/api/game/${gameId}/state`
      : `/api/game/${gameId}/state?move_index=${index}`;
    try {
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setReviewState(data);
      }
    } catch (error) {
      console.error('Failed to fetch review state:', error);
    }
  }, [gameId]);

  // 监听复盘索引变化
  useEffect(() => {
    if (mode === 'review' && gameId) {
      fetchReviewState(reviewIndex);
    }
  }, [mode, gameId, reviewIndex, fetchReviewState]);

  // AI 分析（复盘模式）
  const runAnalysis = async () => {
    if (!reviewState) return;
    const config = whiteAiConfig.apiKey ? whiteAiConfig : blackAiConfig;
    if (!config.apiKey) {
      alert('请先配置 AI');
      return;
    }
    setIsAnalyzing(true);
    try {
      const response = await fetch('/api/ai/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_state: reviewState,
          mode: 'analyze',
          llm_config: config,
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setAnalysis(data.analysis || '无分析结果');
      } else {
        alert('分析失败');
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('分析失败');
    } finally {
      setIsAnalyzing(false);
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
            <button onClick={() => startNewGame(mode)}>重新开始</button>
            <button onClick={handleUndo} disabled={gameState.history.length === 0}>
              悔棋
            </button>
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
            {mode === 'aivsai' ? (
              <>
                <div className="form-group">
                  <label>黑方 AI</label>
                  <input
                    type="password"
                    value={blackAiConfig.apiKey}
                    onChange={e => setBlackAiConfig({ ...blackAiConfig, apiKey: e.target.value })}
                    placeholder="sk-..."
                  />
                  <input
                    value={blackAiConfig.apiBase}
                    onChange={e => setBlackAiConfig({ ...blackAiConfig, apiBase: e.target.value })}
                  />
                  <input
                    value={blackAiConfig.model}
                    onChange={e => setBlackAiConfig({ ...blackAiConfig, model: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>白方 AI</label>
                  <input
                    type="password"
                    value={whiteAiConfig.apiKey}
                    onChange={e => setWhiteAiConfig({ ...whiteAiConfig, apiKey: e.target.value })}
                    placeholder="sk-..."
                  />
                  <input
                    value={whiteAiConfig.apiBase}
                    onChange={e => setWhiteAiConfig({ ...whiteAiConfig, apiBase: e.target.value })}
                  />
                  <input
                    value={whiteAiConfig.model}
                    onChange={e => setWhiteAiConfig({ ...whiteAiConfig, model: e.target.value })}
                  />
                </div>
              </>
            ) : (
              <div className="form-group">
                <label>AI 配置 (白方)</label>
                <input
                  type="password"
                  value={whiteAiConfig.apiKey}
                  onChange={e => setWhiteAiConfig({ ...whiteAiConfig, apiKey: e.target.value })}
                  placeholder="sk-..."
                />
                <input
                  value={whiteAiConfig.apiBase}
                  onChange={e => setWhiteAiConfig({ ...whiteAiConfig, apiBase: e.target.value })}
                />
                <input
                  value={whiteAiConfig.model}
                  onChange={e => setWhiteAiConfig({ ...whiteAiConfig, model: e.target.value })}
                />
              </div>
            )}
          </div>

          {/* SGF 操作面板 */}
          <div className="panel">
            <h3>SGF 操作</h3>
            <button onClick={() => fileInputRef.current?.click()}>导入 SGF</button>
            <input
              type="file"
              accept=".sgf"
              style={{ display: 'none' }}
              ref={fileInputRef}
              onChange={handleFileChange}
            />
            <button onClick={exportSGF} disabled={!gameId}>导出 SGF</button>
          </div>

          {/* 复盘控制面板 (仅在复盘模式显示) */}
          {mode === 'review' && (
            <div className="panel">
              <h3>复盘控制</h3>
              <div>
                <label>步数: {reviewIndex + 1} / {gameState.history.length}</label><br/>
                <input
                  type="range"
                  min="-1"
                  max={gameState.history.length - 1}
                  value={reviewIndex}
                  onChange={e => setReviewIndex(parseInt(e.target.value))}
                  disabled={!gameState.history.length}
                  style={{ width: '100%' }}
                />
              </div>
              <button onClick={runAnalysis} disabled={!reviewState || isAnalyzing} style={{ marginTop: '8px' }}>
                {isAnalyzing ? '分析中...' : 'AI 分析'}
              </button>
              {analysis && (
                <div className="analysis-output" style={{ marginTop: '8px' }}>
                  <pre>{analysis}</pre>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="board-area">
          <Board
            gameState={mode === 'review' && reviewState ? reviewState : gameState}
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
