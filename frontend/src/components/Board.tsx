import React, { useState, useCallback } from 'react';
import { BOARD_SIZE, columnLabels, coordinateToPosition, Stone } from '../utils/board';
import { GameState } from '../types';
import './Board.css';

interface BoardProps {
  gameState: GameState;
  onStonePlaced: (x: number, y: number) => void;
  disabled?: boolean; // 禁用落子（如 AI 思考时）
}

const BoardComponent: React.FC<BoardProps> = ({
  gameState,
  onStonePlaced,
  disabled = false,
}) => {
  const [hoverPos, setHoverPos] = useState<[number, number] | null>(null);

  const handleClick = useCallback(
    (x: number, y: number) => {
      if (disabled) return;
      if (gameState.board[x][y].color !== null) return;
      onStonePlaced(x, y);
    },
    [disabled, onStonePlaced, gameState.board]
  );

  const isCurrentPlayerStone = (color: 'B' | 'W' | null) => {
    return color === gameState.currentPlayer;
  };

  const renderBoard = () => {
    const cells = [];

    for (let y = 0; y < BOARD_SIZE; y++) {
      for (let x = 0; x < BOARD_SIZE; x++) {
        const stone = gameState.board[x][y];
        const isHover = hoverPos && hoverPos[0] === x && hoverPos[1] === y;
        const isLastMove =
          gameState.history.length > 0 &&
          gameState.history[gameState.history.length - 1].coordinate ===
            `${columnLabels[x]}${y + 1}`;

        cells.push(
          <div
            key={`${x}-${y}`}
            className={`board-cell ${stone.color ? 'occupied' : ''} ${isHover ? 'hover' : ''}`}
            onClick={() => handleClick(x, y)}
            onMouseEnter={() => setHoverPos([x, y])}
            onMouseLeave={() => setHoverPos(null)}
          >
            {/* 棋盘网格线 */}
            <div className="grid-line horizontal" />
            <div className="grid-line vertical" />

            {/* 棋子 */}
            {stone.color && (
              <div
                className={`stone ${stone.color} ${isLastMove ? 'last-move' : ''} ${isCurrentPlayerStone(stone.color) ? 'current-turn' : ''}`}
              />
            )}

            {/* 星位（天元和四角星） */}
            {isStarPoint(x, y) && <div className="star-point" />}
          </div>
        );
      }
    }

    return cells;
  };

  const isStarPoint = (x: number, y: number): boolean => {
    const stars = [
      [3, 3],
      [9, 3],
      [15, 3],
      [3, 9],
      [9, 9],
      [15, 9],
      [3, 15],
      [9, 15],
      [15, 15],
    ];
    return stars.some(([sx, sy]) => sx === x && sy === y);
  };

  // 坐标标签（左侧和底部）
  const renderCoordinates = () => {
    const leftLabels = [];
    const bottomLabels = [];

    for (let i = 0; i < BOARD_SIZE; i++) {
      leftLabels.push(
        <div key={i} className="coord-label left">
          {BOARD_SIZE - i}
        </div>
      );
      bottomLabels.push(
        <div key={i} className="coord-label bottom">
          {columnLabels[i]}
        </div>
      );
    }

    return { leftLabels, bottomLabels };
  };

  const { leftLabels, bottomLabels } = renderCoordinates();

  return (
    <div className="go-board-container">
      <div className="coordinates-left">{leftLabels}</div>
      <div className="board-wrapper">
        <div className="board-grid">{renderBoard()}</div>
        <div className="coordinates-bottom">{bottomLabels}</div>
      </div>
    </div>
  );
};

export default BoardComponent;
