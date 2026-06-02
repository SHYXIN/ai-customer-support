# AI 智能客服系统

基于 LangGraph + FastAPI + React 的 RAG 智能客服系统，支持多轮对话、知识库检索、聊天记录持久化。

![系统截图](screenshot.png)

## 功能特性

- **RAG 检索增强生成**：BGE 中文嵌入模型 + Chroma 向量数据库，支持语义搜索知识库
- **LangGraph ReAct Agent**：检索知识库 → 生成回答，支持多轮对话
- **对话上下文持久化**：SqliteSaver 存储对话状态，服务重启后 LLM 仍能恢复多轮记忆
- **聊天记录管理**：SQLite + SQLAlchemy 持久化，支持会话列表、历史查询、重命名、删除
- **前后端分离**：React 前端通过 REST API 与后端通信，环境变量配置后端地址
- **TDD 开发**：57 个测试用例覆盖全栈

## 架构设计

```
ai-customer-support/
├── backend/                    # FastAPI + LangGraph + Chroma
│   ├── app/
│   │   ├── agent.py            # LangGraph ReAct Agent（检索 → 生成）
│   │   ├── database.py         # SQLAlchemy 引擎和 Session
│   │   ├── main.py             # FastAPI 入口，lifespan 管理
│   │   ├── config.py           # Pydantic Settings 配置
│   │   ├── models/
│   │   │   ├── database.py     # ChatSession / ChatMessage ORM 模型
│   │   │   └── schemas.py      # Pydantic API 请求/响应模型
│   │   ├── routers/
│   │   │   ├── chat.py         # POST /api/chat 对话接口
│   │   │   ├── history.py      # 会话列表/历史/重命名/删除
│   │   │   └── admin.py        # 知识库导入/统计/检索
│   │   ├── services/
│   │   │   ├── chat_log.py     # ChatLogService 聊天记录 CRUD
│   │   │   ├── data_loader.py  # Bitext 数据加载/清洗/去重
│   │   │   ├── embedding.py    # BGE 嵌入服务（ONNX Runtime）
│   │   │   └── vector_store.py # Chroma 向量存储服务
│   │   └── tools/
│   │       └── customer_service.py  # LangChain @tool 函数
│   ├── tests/                  # 57 个测试用例
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                   # React + Vite + Shadcn UI
│   ├── src/
│   │   ├── components/         # UI 组件
│   │   ├── hooks/
│   │   │   └── useSessions.ts  # 会话管理 Hook（后端同步）
│   │   ├── services/
│   │   │   └── api.ts          # API 客户端
│   │   └── App.tsx             # 根组件
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml
```

## 数据流

```
用户输入 → POST /api/chat
    ↓
chat.py 路由 → agent.chat()
    ↓
LangGraph Agent:
    1. retrieve 节点：Chroma 语义检索 top-3 知识库条目
    2. generate 节点：LLM 根据知识库上下文生成回答
    ↓
保存消息到 SQLite（ChatLogService）
保存对话上下文到 checkpoint.db（SqliteSaver）
    ↓
返回 AI 回复 + 引用来源
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- uv（Python 包管理器）

### 后端

```bash
cd backend
cp .env.example .env
# 编辑 .env 配置 OPENAI_API_KEY 和 OPENAI_BASE_URL
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可使用。

## API 文档

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 发送消息，返回 AI 回复 |
| GET | `/health` | 健康检查 |

### 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/chat/sessions` | 列出所有会话 |
| GET | `/api/chat/history/{session_id}` | 获取会话消息历史 |
| PUT | `/api/chat/sessions/{session_id}/rename` | 重命名会话 |
| DELETE | `/api/chat/sessions/{session_id}` | 删除会话 |

### 知识库管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/import` | 导入 Bitext 数据到 Chroma |
| GET | `/api/admin/stats` | 获取知识库统计 |
| POST | `/api/admin/search` | 语义检索知识库 |

## 技术栈

| 层级 | 技术 |
|------|------|
| **大模型** | LongCat API（OpenAI 兼容格式） |
| **嵌入模型** | BAAI/bge-small-zh-v1.5（ONNX 本地推理，512 维） |
| **向量数据库** | Chroma（本地持久化） |
| **智能体编排** | LangGraph（StateGraph + Checkpoint） |
| **后端框架** | FastAPI + Pydantic V2 |
| **ORM** | SQLAlchemy 2.0 + Alembic |
| **前端框架** | React 19 + TypeScript + Vite |
| **UI 组件** | Shadcn UI + Tailwind CSS |
| **测试** | pytest（后端）+ Vitest（前端） |

## 测试

```bash
# 后端测试
cd backend
uv run pytest tests/ -v

# 前端测试
cd frontend
npm run test
```

## License

MIT
