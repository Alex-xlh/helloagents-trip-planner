# HelloAgents 智能旅行规划助手

这是一个前后端分离的 AI 旅行规划项目。前端使用 Vue 3 + Vite，后端使用 FastAPI + LangChain/LangGraph，结合高德地图 MCP/REST 接口、Redis 缓存、PostgreSQL/SQLite 存储、Edge TTS 和 Live2D 虚拟导游，生成可视化、多日、可导出的旅行计划。

## 当前项目能力

- AI 流式生成旅行计划，前端展示打字机式进度
- 高德地图 POI、天气、酒店数据检索
- 按天生成景点、住宿、餐饮、天气、预算建议
- TSP 简单路线纠偏，减少每日景点绕路
- 结果页高德 3D 地图标点展示
- 登录、注册、JWT 鉴权
- 已登录用户自动保存历史行程
- 行程结果支持编辑、导出图片、导出 PDF
- 虚拟导游聊天、语音输入、Edge TTS 语音播报、Live2D 口型同步
- Redis 缓存相同请求，减少重复调用大模型

## 从 Windows 切到 macOS 的影响

这个项目主体是跨平台的，但下面几点需要注意：

- `.bat` 启动脚本只适合 Windows。macOS 请使用本文档里的 `source venv/bin/activate`、`python run.py`、`npm run dev`。
- Python 虚拟环境激活路径不同：Windows 是 `venv\Scripts\activate`，macOS 是 `source venv/bin/activate`。
- macOS 默认命令通常是 `python3` 和 `pip3`，也可以在激活虚拟环境后直接用 `python`、`pip`。
- 如果你在 Windows 本地放过 Live2D 静态文件，它们当前没有随仓库一起提交。macOS 需要重新放到 `frontend/public/`，否则虚拟导游不会显示。
- 前端语音输入依赖浏览器 Web Speech API，推荐 Chrome 或 Edge；Safari 支持情况不稳定。
- 高德 JS API 需要 Web 端 JS Key 和安全密钥，后端需要 Web 服务 Key。它们不是同一种 Key。
- 项目里有 `.env` 类配置文件，迁移机器后需要重新确认本地环境变量、API Key、数据库地址。

## 环境要求

建议版本：

- macOS 12+
- Python 3.10+
- Node.js 18+，推荐 20 LTS
- npm 9+
- Docker Desktop，用于 PostgreSQL 和 Redis
- Chrome 或 Edge，用于语音识别和 Live2D 调试

你当前这台 Mac 上如果 Node/Python 版本更高，一般也能跑；遇到依赖编译问题时优先切到 Node 20 LTS 和 Python 3.11/3.12。

## 需要下载/准备的内容

系统工具：

- Python 3.10+
- Node.js 18+ 或 20 LTS
- Docker Desktop
- Git

后端 Python 依赖在 `backend/requirements.txt`：

- FastAPI / Uvicorn
- Pydantic / pydantic-settings
- LangChain / LangGraph / langchain-openai
- MCP SDK
- HTTP 客户端：httpx / aiohttp
- 数据库：SQLAlchemy / asyncpg / aiosqlite
- 缓存：redis
- 登录鉴权：bcrypt / python-jose / PyJWT
- 限流：slowapi
- 语音合成：edge-tts
- 工具：uv / python-dotenv / python-dateutil / loguru

前端 npm 依赖在 `frontend/package.json`：

- Vue 3
- Vue Router
- Vite
- TypeScript / vue-tsc
- Ant Design Vue
- Ant Design Icons Vue
- Axios
- 高德地图 JS API Loader
- dayjs
- html2canvas
- jsPDF

外部账号和 Key：

- 高德开放平台 Web 服务 Key：后端 `AMAP_API_KEY`
- 高德开放平台 Web 端 JS API Key：前端 `VITE_AMAP_JS_KEY`
- 高德开放平台安全密钥：前端 `VITE_AMAP_SECURITY_CODE`
- LLM API Key：`LLM_API_KEY` 或 `OPENAI_API_KEY`
- 可选：自定义 OpenAI 兼容接口地址 `LLM_BASE_URL`
- 可选：自定义模型名 `LLM_MODEL_ID`

Live2D 静态资源，需要自行放入 `frontend/public/`：

```text
frontend/public/
├── pixi.min.js
├── live2d.min.js
├── live2dcubismcore.js
├── pixi-live2d-display.min.js
└── shizuku/
    └── shizuku.model.json
```

如果这些文件缺失，主功能仍可使用，但右下角虚拟导游会初始化失败。

## 项目结构

```text
helloagents-trip-planner/
├── backend/
│   ├── app/
│   │   ├── agents/              # 多智能体旅行规划逻辑
│   │   ├── api/
│   │   │   ├── main.py          # FastAPI 入口
│   │   │   └── routes/          # trip / poi / auth / history / tts / guide
│   │   ├── core/                # DB、Redis、JWT、HTTP client、限流
│   │   ├── models/              # Pydantic schema 和 SQLAlchemy model
│   │   ├── services/            # 高德、LLM、TTS 服务
│   │   └── utils/               # 地理距离工具
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/          # 导航栏、滑动提交、虚拟导游
│   │   ├── services/            # Axios / fetch API 封装
│   │   ├── store/               # 简单登录状态
│   │   ├── types/               # TypeScript 类型
│   │   └── views/               # 首页、结果页、历史页
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml           # PostgreSQL + Redis
├── start_backend.bat            # Windows 启动脚本
└── start_frontend.bat           # Windows 启动脚本
```

## 本地部署，macOS 推荐流程

### 1. 启动 PostgreSQL 和 Redis

在项目根目录执行：

```bash
cd /Users/mac/Desktop/Alex/helloagents-trip-planner
docker compose up -d
```

默认容器：

- PostgreSQL：`127.0.0.1:5432`
- Redis：`127.0.0.1:6379`

`docker-compose.yml` 里的 PostgreSQL 默认账号如下：

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=xlh20041109
POSTGRES_DB=trip_planner
```

### 2. 配置后端环境变量

创建 `backend/.env`：

```bash
cd /Users/mac/Desktop/Alex/helloagents-trip-planner/backend
touch .env
```

写入：

```env
APP_NAME=智能旅行规划助手
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

AMAP_API_KEY=你的高德Web服务APIKey

LLM_API_KEY=你的LLM_API_Key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_ID=gpt-4o-mini

DATABASE_URL=postgresql+asyncpg://postgres:xlh20041109@127.0.0.1:5432/trip_planner
JWT_SECRET_KEY=请替换成本地随机字符串
CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

如果使用 DeepSeek，可改成：

```env
LLM_API_KEY=你的DeepSeekKey
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_ID=deepseek-chat
```

如果不想启动 PostgreSQL，也可以临时使用 SQLite：

```env
DATABASE_URL=sqlite+aiosqlite:///trips.db
```

Redis 地址目前在代码里固定为 `redis://localhost:6379/0`，所以需要本机 Redis 可访问；如果 Redis 没启动，生成行程仍会尝试继续，但缓存会失效并打印警告。

### 3. 安装并启动后端

```bash
cd /Users/mac/Desktop/Alex/helloagents-trip-planner/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python run.py
```

后端启动成功后访问：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

### 4. 配置前端环境变量

创建或编辑 `frontend/.env`：

```bash
cd /Users/mac/Desktop/Alex/helloagents-trip-planner/frontend
touch .env
```

写入：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_AMAP_JS_KEY=你的高德Web端JSAPIKey
VITE_AMAP_SECURITY_CODE=你的高德安全密钥
```

也可以不设置 `VITE_API_BASE_URL`，让 Vite 通过 `vite.config.ts` 把 `/api` 和 `/static` 代理到后端。当前 `.env` 使用直连后端的方式，也可以正常工作。

### 5. 安装并启动前端

```bash
cd /Users/mac/Desktop/Alex/helloagents-trip-planner/frontend
npm install
npm run dev
```

打开：

```text
http://127.0.0.1:3000
```

## 高德 MCP 初始化说明

后端启动时会初始化高德 MCP 连接池。代码中使用：

```text
uvx --offline amap-mcp-server
```

这意味着如果你的 Mac 从未缓存过 `amap-mcp-server`，第一次可能会因为离线模式找不到包而失败。可以先联网执行一次：

```bash
cd /Users/mac/Desktop/Alex/helloagents-trip-planner/backend
source venv/bin/activate
uvx amap-mcp-server
```

确认能启动后再停止它，并重新运行：

```bash
python run.py
```

## 常用 API

启动后端后，完整接口见：

```text
http://127.0.0.1:8000/docs
```

主要接口：

- `GET /health`：后端健康检查
- `POST /api/trip/plan/stream`：流式生成旅行计划
- `GET /api/trip/health`：旅行规划服务检查
- `GET /api/poi/photo`：获取景点图片
- `POST /api/auth/register`：注册
- `POST /api/auth/login`：登录
- `GET /api/auth/me`：当前用户
- `GET /api/history`：历史行程列表
- `POST /api/history`：保存历史行程
- `GET /api/history/{trip_id}`：历史行程详情
- `DELETE /api/history/{trip_id}`：删除历史行程
- `POST /api/guide/chat`：虚拟导游聊天
- `POST /api/tts/generate`：生成 TTS 音频

## 常见问题

### 1. 后端提示 `AMAP_API_KEY未配置`

后端启动会强制检查 `AMAP_API_KEY`。请确认 `backend/.env` 存在，并且是在 `backend` 目录下执行 `python run.py`。

### 2. 生成计划失败，但后端能启动

检查：

- `LLM_API_KEY` 是否正确
- `LLM_BASE_URL` 是否是 OpenAI 兼容接口
- `LLM_MODEL_ID` 是否存在
- 高德 Web 服务 Key 是否可用
- `uvx amap-mcp-server` 是否已能正常运行

### 3. 登录或历史记录失败

检查数据库：

```bash
docker compose ps
```

确认 PostgreSQL 正在运行，且 `DATABASE_URL` 与 `docker-compose.yml` 账号密码一致。

### 4. Redis 报错

检查：

```bash
docker compose ps
```

确认 Redis 正在运行。Redis 只是缓存层，短时间不可用不会阻止主流程，但会失去缓存加速。

### 5. 地图加载失败

检查：

- `frontend/.env` 中 `VITE_AMAP_JS_KEY` 是否是 Web 端 JS API Key
- `VITE_AMAP_SECURITY_CODE` 是否配置
- 高德控制台是否允许当前访问来源
- 修改 `.env` 后需要重启 `npm run dev`

### 6. 虚拟导游不显示

检查 `frontend/public/` 下是否有：

```text
pixi.min.js
live2d.min.js
live2dcubismcore.js
pixi-live2d-display.min.js
shizuku/shizuku.model.json
```

这些文件当前不在仓库里，需要从原 Windows 项目或资源包复制过来。

### 7. 语音输入不可用

推荐使用 Chrome 或 Edge，并允许浏览器麦克风权限。Safari 可能不稳定。

## Windows 启动方式

如果之后仍在 Windows 上运行，可以继续使用：

```text
start_backend.bat
start_frontend.bat
```

但在 macOS 上请不要使用 `.bat`，按本文档的 macOS 命令启动。

## 开发备注

- 后端启动时会自动创建数据库表，生产环境建议改为 Alembic 迁移。
- 当前 Redis 地址写死在 `backend/app/core/redis_client.py`，后续可以改为从 `.env` 读取。
- `frontend/.env` 里的高德 JS Key 属于前端公开变量，不应放置后端私密 Key。
- 请不要提交真实的后端 `.env`、数据库文件、TTS 生成音频缓存和本地 Live2D 大文件。
