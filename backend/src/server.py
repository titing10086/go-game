"""
FastAPI 服务器：主入口
"""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import settings
from .schemas import GameState, Move, AIRequest, AIResponse, WSMessage

# 导入游戏引擎（稍后实现）
# from .engine.go_rules import Board

# 全局游戏状态存储（简单实现，生产环境应使用 Redis/DB）
games: Dict[str, GameState] = {}
active_connections: Dict[str, List[WebSocket]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🚀 Go Game Backend starting...")
    yield
    print("🛑 Go Game Backend shutting down...")


app = FastAPI(
    title="大棋局 - Go Game AI",
    description="围棋游戏后端，支持 AI 对弈",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """健康检查"""
    return {"message": "大棋局 API", "status": "ok"}


@app.post("/api/game/start")
async def start_game(
    mode: str = "pve",  # "pve" 或 "aivsai"
    board_size: int = 19,
    black_ai_config: Optional[dict] = None,
    white_ai_config: Optional[dict] = None,
):
    """
    开始新游戏

    Args:
        mode: 游戏模式
        board_size: 棋盘大小
        black_ai_config: 黑方 AI 配置
        white_ai_config: 白方 AI 配置

    Returns:
        游戏 ID 和初始状态
    """
    import uuid

    game_id = str(uuid.uuid4())[:8]

    game_state = GameState(
        game_id=game_id,
        board_size=board_size,
        current_player="B",  # 黑棋先行
        history=[],
        captured_stones={"B": 0, "W": 0},
        is_game_over=False,
    )

    games[game_id] = game_state

    return {
        "game_id": game_id,
        "state": game_state.model_dump(),
        "mode": mode,
    }


@app.get("/api/game/{game_id}/state")
async def get_game_state(game_id: str):
    """获取当前游戏状态"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    return games[game_id].model_dump()


@app.post("/api/game/{game_id}/move")
async def make_move(game_id: str, coordinate: str, player: str):
    """
    执行落子（玩家操作）

    Args:
        coordinate: 坐标，如 "Q16"
        player: "B" 或 "W"

    Returns:
        更新后的游戏状态
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[game_id]

    # TODO: 使用规则引擎验证落子合法性
    # board.place(x, y, player)

    # 临时：直接记录
    move = Move(color=player, coordinate=coordinate, timestamp=datetime.now())
    game.history.append(move)

    # 切换玩家
    game.current_player = "W" if player == "B" else "B"

    return game.model_dump()


@app.websocket("/ws/game/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """
    WebSocket 连接：实时推送游戏状态

    消息类型：
    - client -> server: {"type": "move", "data": {"coordinate": "Q16"}}
    - server -> client: {"type": "move", "data": {"color": "B", "coordinate": "Q16"}}
    """
    await websocket.accept()

    if game_id not in games:
        await websocket.send_json({"type": "error", "data": {"message": "Game not found"}})
        await websocket.close()
        return

    # 记录连接
    if game_id not in active_connections:
        active_connections[game_id] = []
    active_connections[game_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "move":
                # 处理落子
                coordinate = data["data"]["coordinate"]
                player = games[game_id].current_player

                # 更新状态
                move = Move(color=player, coordinate=coordinate)
                games[game_id].history.append(move)
                games[game_id].current_player = "W" if player == "B" else "B"

                # 广播给所有连接
                await broadcast_move(game_id, player, coordinate)

            elif message_type == "ai_analyze":
                # 请求 AI 分析（暂不实现）
                pass

    except WebSocketDisconnect:
        active_connections[game_id].remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")


async def broadcast_move(game_id: str, player: str, coordinate: str):
    """广播落子消息给该游戏的所有客户端"""
    message = WSMessage(type="move", data={"color": player, "coordinate": coordinate})

    if game_id in active_connections:
        for ws in active_connections[game_id]:
            try:
                await ws.send_json(message.model_dump())
            except:
                pass  # 客户端断开则忽略


if __name__ == "__main__":
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
