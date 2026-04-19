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

# 导入游戏引擎
from .engine.go_rules import GoRules, RuleViolation

# 全局游戏状态存储（简单实现，生产环境应使用 Redis/DB）
# 现在存储 GoRules 引擎实例
games: Dict[str, GoRules] = {}
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

    # 创建规则引擎实例
    game_rules = GoRules(board_size=board_size)

    games[game_id] = game_rules

    # 返回初始状态（使用 GameState 模型以兼容前端）
    initial_state = GameState(
        game_id=game_id,
        board_size=board_size,
        current_player=game_rules.current_player,
        history=[],
        captured_stones={"B": 0, "W": 0},
        is_game_over=False,
    )

    return {
        "game_id": game_id,
        "state": initial_state.model_dump(),
        "mode": mode,
    }


@app.get("/api/game/{game_id}/state")
async def get_game_state(game_id: str):
    """获取当前游戏状态（从 GoRules 引擎重建 GameState）"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    rules = games[game_id]
    board_state = rules.board

    # 从 board.moves 重建历史
    history = []
    captured_B = 0
    captured_W = 0
    for move in board_state.moves:
        # 将 (x,y) 转换为坐标字符串
        coord = rules.position_to_coordinate(move.x, move.y)
        move_item = Move(
            color=move.color,
            coordinate=coord,
            timestamp=move.timestamp
        )
        history.append(move_item)

        # 累计提子数
        if move.color == "B":
            captured_W += len(move.captured)
        else:
            captured_B += len(move.captured)

    # 构建 GameState 返回
    state = GameState(
        game_id=game_id,
        board_size=rules.board.size,
        current_player=rules.current_player,
        history=history,
        captured_stones={"B": captured_B, "W": captured_W},
        is_game_over=rules.is_game_over,
        winner=rules.winner,
        board=rules.board.to_grid_array(),  # 包含棋盘状态
    )

    return state.model_dump()


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

    rules = games[game_id]

    # 确保 player 是当前回合的玩家（可选，严格模式）
    if player != rules.current_player:
        raise HTTPException(status_code=400, detail=f"Not {player}'s turn")

    try:
        # 使用规则引擎执行落子
        success, captured_coords, msg = rules.play_move_by_coord(coordinate)
        return await get_game_state(game_id)  # 返回完整状态
    except RuleViolation as e:
        raise HTTPException(status_code=400, detail=e.reason)


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
                rules = games[game_id]
                player = rules.current_player

                try:
                    # 使用规则引擎落子
                    success, captured_coords, msg = rules.play_move_by_coord(coordinate)

                    # 广播落子消息
                    await broadcast_move(game_id, player, coordinate)

                    # 广播提子信息（可选）
                    if captured_coords:
                        await broadcast_message(game_id, "capture", {
                            "player": player,
                            "stones": captured_coords
                        })

                except RuleViolation as e:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": e.reason}
                    })

            elif message_type == "pass":
                # 虚手
                rules = games[game_id]
                rules.play_pass()
                # 广播
                await broadcast_message(game_id, "pass", {
                    "player": rules.current_player
                })
                # 检查游戏是否结束
                if rules.is_game_over:
                    await broadcast_game_over(game_id, rules.winner)

            elif message_type == "ai_analyze":
                # 请求 AI 分析（暂不实现）
                pass

    except WebSocketDisconnect:
        if game_id in active_connections and websocket in active_connections[game_id]:
            active_connections[game_id].remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")


async def broadcast_message(game_id: str, msg_type: str, data: dict):
    """广播通用消息"""
    message = WSMessage(type=msg_type, data=data)
    if game_id in active_connections:
        for ws in active_connections[game_id]:
            try:
                await ws.send_json(message.model_dump())
            except:
                pass


async def broadcast_move(game_id: str, player: str, coordinate: str):
    """广播落子消息给该游戏的所有客户端"""
    await broadcast_message(game_id, "move", {"color": player, "coordinate": coordinate})


async def broadcast_game_over(game_id: str, winner: Optional[str]):
    """广播游戏结束"""
    await broadcast_message(game_id, "game_over", {"winner": winner})


if __name__ == "__main__":
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
