# 智能数据分析 Agent 系统

一个「对话式数据洞察」全栈 Web 应用：用户上传 CSV / Excel / JSON 数据集后，用自然语言提问，
Agent 自动完成 **元数据查询 → 生成 pandas 代码 → 沙箱执行 → 生成 ECharts 图表 → 输出分析结论 + Markdown 报告** 的全流程。

## ✨ 核心特性

- **对话式分析**：多轮追问、携带上下文，自然语言驱动数据分析
- **自主工具调用**：元数据查询、代码生成与执行、图表生成、报告生成 4 类工具
- **自动纠错**：代码执行失败时根据报错自动修正并重试（最多 3 次）
- **思考过程可视化**：SSE 流式展示「思考 → 生成代码 → 执行 → 生成图表 → 完成」
- **安全沙箱**：进程级隔离（资源限制 + 模块白名单 + 禁网 + 禁危险调用 + 临时目录）
- **数据权限隔离**：每个用户只能操作自己上传的数据集
- **安全体系**：PBKDF2 加盐哈希 + JWT 鉴权 + IP/用户双维度限流 + 上传三重校验

## 🧰 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10 · FastAPI · Celery · Redis · SQLite · SQLAlchemy |
| 前端 | Vue 3 · Vite · Element Plus · ECharts · axios · SSE |
| Agent | LangChain · 工具调用框架 · OpenAI 兼容 API（支持 Ollama 切换） |
| 工程化 | Docker Compose · 分级日志 · 统一异常处理 |

## 📁 目录结构

```
Data_Analysis_Agent/
├── backend/
│   ├── app/
│   │   ├── api/          # API 层（路由）
│   │   ├── services/     # Service 层（业务逻辑）
│   │   ├── core/         # Core 层（安全/限流/校验/日志/异常）
│   │   ├── agent/        # Agent 核心（LLM/提示词/4 类工具/组装）
│   │   ├── sandbox/      # 代码执行沙箱
│   │   ├── models/       # ORM 模型
│   │   └── schemas/      # Pydantic 模型
│   ├── tasks/            # Celery 任务
│   ├── celery_app.py     # Celery 实例
│   ├── requirements.txt
│   └── run.py            # 本地启动入口
├── frontend/
│   └── src/              # Vue 3 前端
├── data/                 # SQLite 数据、上传文件、测试数据集
├── docker-compose.yml
├── Dockerfile.backend / Dockerfile.frontend
├── nginx.conf
└── .env.example
```

## 🚀 快速开始

### 方式一：Docker Compose 一键部署（推荐）

```bash
# 1. 准备环境变量
cp .env.example .env
# 编辑 .env：填入 OPENAI_API_BASE / OPENAI_API_KEY / MODEL_NAME 等

# 2. 一键启动（后端 + worker + redis + 前端 nginx）
docker compose up --build -d

# 3. 访问
# http://localhost  （前端）
# http://localhost/api/health  （健康检查）
```

> 若使用宿主机 Ollama，`OPENAI_API_BASE` 填 `http://host.docker.internal:11434/v1`。

### 方式二：本地无 Docker 运行（Windows 调试）

```bash
# ---- 后端 ----
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cd ..   # 回到项目根目录
cp .env.example .env   # 本地默认 CELERY_MODE=eager，无需 Redis
python backend/run.py   # 启动于 http://localhost:8000

# ---- 前端（另开一个终端）----
cd frontend
npm install
npm run dev   # 启动于 http://localhost:5173
```

> 本地模式说明：`CELERY_MODE=eager` 使 Celery 任务同步执行（用 fakeredis 兜底），
> 无需安装 Redis 即可跑通全流程；生产 / Compose 部署自动切换为 `redis` 异步队列。

## 🔧 环境变量配置（.env）

| 变量 | 说明 | 默认值 |
|---|---|---|
| `OPENAI_API_BASE` | OpenAI 兼容端点（Ollama：`http://localhost:11434/v1`） | `http://localhost:11434/v1` |
| `OPENAI_API_KEY` | API Key（Ollama 填任意值如 `ollama`） | `ollama` |
| `MODEL_NAME` | 模型名（Ollama 如 `qwen2.5:7b`） | `qwen2.5:7b` |
| `CELERY_MODE` | `eager`（本地同步）/ `redis`（异步队列） | `eager` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `JWT_SECRET` | JWT 签名密钥（务必修改） | 开发默认值 |
| `SECRET_KEY` | 应用密钥（务必修改） | 开发默认值 |
| `DATABASE_URL` | SQLite 连接串 | `sqlite:///./data/app.db` |
| `MAX_UPLOAD_MB` | 上传大小上限 | `50` |
| `SANDBOX_TIMEOUT` | 沙箱单任务超时（秒） | `30` |
| `SANDBOX_MAX_MEMORY_MB` | 沙箱内存上限（MB） | `512` |
| `RATE_LIMIT_PER_MINUTE` | 每 IP/用户每分钟限流次数 | `60` |

## 📡 API 接口文档

启动后访问 `http://localhost:8000/docs` 查看 Swagger 交互式文档。

### 认证
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/register` | 注册 `{username, password}` |
| POST | `/api/auth/login` | 登录，返回 `{token, user}` |
| GET | `/api/auth/me` | 当前用户（需 Bearer token） |

### 数据集
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/datasets` | 数据集列表（按用户隔离） |
| POST | `/api/datasets/upload` | 上传（multipart，`file` 字段） |
| PATCH | `/api/datasets/{id}` | 重命名 `{name}` |
| DELETE | `/api/datasets/{id}` | 删除 |
| GET | `/api/datasets/{id}/meta` | 元数据 + 清洗预检 |

### 分析（SSE 流式）
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/analysis/chat` | 对话分析，`{dataset_id, question, history}`，返回 `text/event-stream` |

SSE 事件类型：`thinking`（思考文本增量）、`tool_call`（调用工具/代码）、`tool_result`（执行结果/图表/报告）、`done`（完成）、`error`（异常）。

### 报告
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/reports/generate` | 提交异步报告生成，返回 `{task_id}` |
| GET | `/api/reports/{task_id}` | 查询生成状态 |
| GET | `/api/reports/{task_id}/download` | 下载 Markdown 报告 |

## 📖 使用说明

1. 注册并登录；
2. 左侧「上传」数据集（`data/sample_sales.csv` 或 `data/sample_iris.csv`）；
3. 点击数据集查看元数据与清洗预检（字段/类型/缺失值/异常值/建议）；
4. 在右侧输入分析需求，或点击快捷指令，例如：
   - 「各品类销售额占比如何？用饼图展示」
   - 「月度销售额趋势如何？用折线图展示」
5. 观察流式分析过程：思考 → 代码 → 执行 → 图表 → 结论；
6. 单条结果可导出图片 / 图表导出 PNG / 整段对话导出 Markdown / 生成完整报告。

## 🔒 安全说明

- **密码**：PBKDF2-SHA256（20 万次迭代）加盐哈希存储，常量时间比较
- **鉴权**：JWT（HS256，含过期时间），数据集接口按 `user_id` 隔离
- **限流**：Redis 固定窗口，IP + 用户双维度
- **上传校验**：扩展名白名单 + MIME + magic bytes 三重校验
- **沙箱**：`python -I` 隔离 + RLIMIT 资源限制 + import 白名单 + 禁网 + 禁危险系统调用 + 临时目录
- **日志脱敏**：password/token/api_key 等敏感字段自动脱敏

> ⚠️ 沙箱为进程级隔离，适合单机部署与演示；如需对不可信代码提供更强隔离，
> 建议升级为容器级（每任务独立 Docker 容器）或 nsjail 方案。

## 📦 测试数据集

- `data/sample_sales.csv`：电商销售数据（500 行，含订单/地区/品类/销售额/利润等，带少量缺失值）
- `data/sample_iris.csv`：鸢尾花数据（150 行，4 个数值特征 + 品种标签）

可运行 `python data/generate_samples.py` 重新生成（纯标准库，无额外依赖）。
