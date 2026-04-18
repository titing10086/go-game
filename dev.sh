#!/bin/bash

# 大棋局 - 开发环境快速启动脚本

set -e

echo "🎮 大棋局 - 开发环境启动"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python 3.9+"
    exit 1
fi

# 前端依赖安装
echo "📦 安装前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# 后端虚拟环境和依赖
echo "🐍 设置后端环境..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install -r requirements.txt
deactivate

cd ..

echo ""
echo "✅ 环境设置完成！"
echo ""
echo "启动方式："
echo "  1. 终端1: cd backend && source venv/bin/activate && uvicorn src.server:app --reload --port 8000"
echo "  2. 终端2: cd frontend && npm run dev"
echo ""
echo "或使用 Docker Compose:"
echo "  export OPENAI_API_KEY=your-key"
echo "  docker-compose up -d"
echo ""
