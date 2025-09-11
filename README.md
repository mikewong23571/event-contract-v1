# Event Contract Trading System

一个面向 Binance 事件合约的交易系统，包含信号生成、风险控制、回测与多渠道通知。

重点：本项目统一使用 uv 管理 Python 依赖与运行，使用 Make 作为开发命令入口。项目不使用 requirements.txt，每个 Python 子项目都以 `pyproject.toml` + `uv.lock` 管理依赖。

## 架构概览

- Backend：FastAPI 实时 API + WebSocket
- Frontend：Next.js 14（App Router）+ TailwindCSS
- Backtesting：基于 pandas/numpy 的回测引擎
- Runtime：实盘/准实时信号计算与推送
- Notifications：多渠道告警（Telegram、飞书、Email）

目录结构（部分）：

```
event-contract-v1/
├── backend/              # FastAPI backend
├── frontend/             # Next.js dashboard
├── backtesting/          # 回测引擎
├── runtime/              # 实时引擎
├── notifications/        # 通知服务
├── docker-compose.yml    # 基础设施服务（Postgres/InfluxDB/Redis 等）
└── Makefile              # 统一开发命令入口
```

## 环境要求

- Python 3.11+
- Node.js 18+
- Docker 20.10+ 与 Docker Compose 2+
- uv（Python 包与运行管理）

安装 uv（官方推荐脚本）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# 安装后确保 `uv --version` 可用
```

## 快速开始（uv + Make）

1) 克隆与配置：

```bash
git clone <repository-url>
cd event-contract-v1
cp .env.example .env  # 按需填写密钥与连接串
```

2) 安装依赖（一次性）：

```bash
make install-tools
# 说明：
# - 会在 backend/backtesting/runtime/notifications 目录下执行 `uv sync --extra dev`
# - 前端目录 frontend 安装开发依赖（eslint/prettier 等）
```

3) 启动开发环境（基础设施 + 应用进程）：

```bash
make dev
# 说明：
# - 先通过 Docker Compose 启动基础设施
# - 再使用 uvx + honcho 按 Procfile.dev 启动所有应用进程
```

4) 访问：

- Dashboard：http://localhost:3000
- API 文档（Swagger）：http://localhost:8000/docs
- pgAdmin：http://localhost:5050
- Redis Commander：http://localhost:8081

## 常用命令（Make）

```bash
# 统一格式化（Python/前端）
make format

# 统一 Lint（Python/前端）
make lint

# 统一类型检查（mypy / tsc）
make type-check

# 统一测试（Python 用 uv 运行 pytest，前端用 npm test）
make test

# 一键检查（格式 + Lint）
make fix

# CI 常用：格式 + Lint + 类型检查 + 测试
make ci

# 清理构建产物与缓存
make clean
```

说明：Makefile 内部所有 Python 工具都通过 `uv run ...` 执行，保证在项目虚拟环境中运行（不污染全局环境）。

### 关闭/停止服务

`make dev` 使用 uvx + honcho 按 `Procfile.dev` 启动应用进程，并用 `docker compose` 启动基础设施。可用以下命令一键关闭：

```bash
# 停止由 honcho 拉起的前后端/服务进程（尽力而为）
make stop

# 仅关闭基础设施容器（Postgres/InfluxDB/Redis 等）
make down

# 一键关闭：先 stop 应用进程，再 down 基础设施
make shutdown
```

提示：在运行 `make dev` 的终端中按 Ctrl+C 也会停止 honcho 管理的应用进程；随后可执行 `make down` 关闭基础设施。

## 组件开发速查

Backend（FastAPI）：

```bash
cd backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
uv run pytest
uv run mypy src/
```

Frontend（Next.js）：

```bash
cd frontend
npm run dev
npm run build
npm run lint
```

Backtesting/Runtime/Notifications（Python 子项目同构）：

```bash
cd backtesting   # 或 runtime / notifications
uv run -m src.main        # 运行主程序（不同子项目入口不同）
uv run pytest             # 运行测试
```

## 依赖管理（uv）

- 同步依赖（含开发依赖）：`uv sync --extra dev`
- 新增运行依赖：`uv add <package>`
- 新增开发依赖：`uv add --dev <package>`
- 移除依赖：`uv remove <package>`
- 运行工具：`uv run <tool> ...`（例如 `uv run black .`、`uv run pytest`）

注意：项目不使用 requirements.txt。每个 Python 子项目使用 `pyproject.toml` + `uv.lock` 锁定依赖与可复现环境。

## 基础设施（Docker Compose）

```bash
# 启动基础设施
docker compose up -d

# 查看状态/日志
docker compose ps
docker compose logs -f postgres
docker compose logs -f influxdb
docker compose logs -f redis

# 清空数据（危险操作）
docker compose down -v
```

## 调试入口

- 后端健康检查：`GET http://localhost:8000/api/v1/health`
- WebSocket：由后端 `Procfile.dev` 进程提供
- 前端首页：`/`，可导航到 Signals/Market Data/Backtesting/Risk 等页面

## 约定与质量

- TDD 优先，见 `/memory/constitution.md`
- CLI 工具与可观测性要求见项目文档与各子项目 README
- PR/变更请遵循：先增测、后实现、保持 `uv.lock` 同步

---

如需进一步脚手架或自动化命令支持，可在 Makefile 中追加目标，并优先通过 `uv run` 执行 Python 工具。
