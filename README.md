# 大棋局 (Grand Board)

一个基于 React + FastAPI 的围棋游戏，支持人机对战、AI 对弈和大模型 API 接入。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tech](https://img.shields.io/badge/React-18+-61dafb.svg)
![Tech](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)
![AI](https://img.shields.io/badge/AI-OpenAI%20Compatible-412991.svg)

---

## 特性

-   🎯 **标准 19x19 棋盘**：传统围棋棋盘，支持天元和星位显示
-   📜 **完整规则引擎**：气、提子、打劫、自杀禁止等（逐步完善中）
-   🤖 **AI 对战模式**
    - 人机对战 (PVE)
    - AI 自动对弈 (AI vs AI)
    - AI 实时点评（复盘模式）
-   🔌 **大模型 API 接入**：支持 OpenAI 兼容接口，可接入 Claude、GPT-4、本地模型等
-   🎨 **精美 UI**：响应式设计，深色主题，直观的棋盘交互
-   📊 **棋步统计**：显示当前玩家、提子数、历史记录

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite |
| 状态管理 | React Hooks (useState/useCallback) |
| UI 样式 | 原生 CSS (CSS Grid + Flexbox) |
| 后端 | Python 3.11+ + FastAPI |
| 实时通信 | WebSocket |
| AI 集成 | OpenAI Python SDK (兼容接口) |
| 容器化 | Docker + Docker Compose |

---

## 项目结构

```
go-game/
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── Board.tsx      # 棋盘组件
│   │   │   └── Board.css
│   │   ├── utils/
│   │   │   └── board.ts       # 棋盘逻辑工具
│   │   ├── types/
│   │   │   └── index.ts       # TypeScript 类型
│   │   ├── App.tsx
│   │   └── App.css
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
│
├── backend/                  # FastAPI 后端
│   ├── src/
│   │   ├── server.py         # 主服务器 (API + WebSocket)
│   │   ├── config.py         # 配置管理
│   │   ├── schemas.py        # Pydantic 模型
│   │   ├── agents/           # AI Agent 实现 (待开发)
│   │   │   └── go_agent.py
│   │   └── engine/           # 规则引擎 (待开发)
│   │       ├── go_rules.py
│   │       └── board.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── README.md
└── 大棋局.md  # 详细设计文档（计划文件）

```

---

## 快速开始

### 环境要求

-   Node.js 18+
-   Python 3.9+
-   npm / pip
-   (可选) Docker & Docker Compose

### 1. 克隆与安装

```bash
cd go-game

# 前端依赖安装
cd frontend
npm install
cd ..

# 后端依赖安装
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
cd ..
```

### 2. 配置环境变量

#### 后端配置

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 LLM API 密钥
# OPENAI_API_KEY=sk-...
# OPEN 重要：Python 虚拟环境已创建但依赖安装失败？
终端显示 "externally managed environment" 错误，这是因为系统禁止直接安装包到全局 Python 环境。

**解决方法：**
1. 确保在 `backend` 目录
2. 已创建虚拟环境: `python3 -m venv venv`
3. 使用虚拟环境的 pip: `venv/bin/pip install -r requirements.txt` (Linux/Mac)
   或 `venv\Scripts\pip install` (Windows)

如果仍然问题，可以尝试: `venv/bin/pip install --break-system-packages -r requirements.txt` (不推荐生产环境)

---

### 3. 运行开发服务器

#### 后端 (FastAPI)

```bash
cd backend
source venv/bin/activate
uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
# API 文档: http://localhost:8000/docs
# WebSocket: ws://localhost:8000/ws/game/{game_id}
```

#### 前端 (Vite)

```bash
cd frontend
npm run dev
# 浏览器访问: http://localhost:5173
```

### 4. (可选) 使用 Docker Compose 一键启动

```bash
# 设置环境变量
export OPENAI_API_KEY=your-api-key-here

# 启动所有服务
docker-compose up -d

# 访问
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
```

---

## 使用指南

### 人机对战 (PVE)

1. 选择 **"人机对战"** 模式
2. 配置 AI 的 API Key 和模型参数
3. 玩家执黑先行（或可通过设置改为白方）
4. 点击棋盘落子后，自动轮到 AI 思考
5. AI 落子完成后，游戏继续

### AI 对弈 (AI vs AI)

1. 选择 **"AI 对弈"** 模式
2. 在侧边栏分别配置黑方和白方的 AI 参数（可不同模型）
3. 点击开始（或未来实现的"开始对弈"按钮）
4. 观察 WebSocket 推送的实时棋步

### 棋局复盘

1. 选择 **"棋局复盘"** 模式
2. 导入 SGF 棋谱文件（将来实现）
3. AI 会对当前局面提供实时分析和建议

---

## API 概览

### REST API

| 端点 | 方法 | 描述 |
|------|------|------|
| `POST /api/game/start` | 创建新游戏 | 返回 `game_id` |
| `GET /api/game/{game_id}/state` | 获取游戏状态 | 返回棋盘、历史、当前玩家 |
| `POST /api/game/{game_id}/move` | 执行落子 | 玩家或 AI 落子 |
| `POST /api/ai/move` | 获取 AI 走法 (待实现) | 返回坐标和分析 |

### WebSocket

连接: `ws://localhost:8000/ws/game/{game_id}`

**客户端 -> 服务器:**
```json
{
  "type": "move",
  "data": { "coordinate": "Q16" }
}
```

**服务器 -> 客户端:**
```json
{
  "type": "move",
  "data": { "color": "B", "coordinate": "Q16" }
}
```

消息类型: `move`, `ai_thinking`, `game_over`, `error`

---

## 开发路线图

- [x] Phase 1: 基础架构（React + FastAPI + 棋盘 UI）
- [ ] Phase 2: 围棋规则引擎（气、提子、劫争）
- [ ] Phase 3: AI Agent 集成（Prompt 管理、API 调用）
- [ ] Phase 4: PVE 人机对战完整流程
- [ ] Phase 5: AI vs AI 自动对弈
- [ ] Phase 6: SGF 导入/导出、复盘功能
- [ ] Phase 7: 优化、测试、部署

详见 [大棋局.md](./大棋局.md) 详细设计文档。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

## License

MIT

---

**Made with ❤️ by Claude Code**
