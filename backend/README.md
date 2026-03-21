# ⚙️ 后端工程 (Backend)

本项目后端基于 **FastAPI** 构建，提供了高性能的异步 API、智能调度算法以及任务队列支持。

## 🛠️ 技术栈清单

*   **Web 框架**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
*   **Web 服务器**: Uvicorn / Gunicorn
*   **数据库 ORM**: SQLAlchemy (默认使用 SQLite，生产环境推荐 PostgreSQL)
*   **包管理**: [uv](https://github.com/astral-sh/uv) (极速 Python 包管理器)
*   **异步任务**: Celery
*   **消息中间件**: Redis
*   **算法**: Genetic Algorithm (遗传算法), K-Means Clustering
*   **GIS 服务**: OpenRouteService Client

## 📦 目录结构

```
backend/
├── app/
│   ├── api/               # API 路由层 (Endpoints)
│   ├── core/              # 核心配置 (Config, Security)
│   ├── db/                # 数据库连接与 Session 管理
│   ├── models/            # SQLAlchemy 数据模型
│   ├── schemas/           # Pydantic 数据验证模型
│   ├── services/          # 业务逻辑服务
│   │   ├── optimization.py # 核心算法 (GA)
│   │   └── ors.py          # 地图服务客户端
│   └── worker.py          # Celery 任务定义
├── logs/                  # 日志文件
├── run_dev.py             # 开发启动脚本
├── seed_data.py           # 数据填充脚本
└── pyproject.toml         # 项目依赖配置
```

## 🚀 开发指南

### 1. 环境初始化

我们使用 `uv` 管理依赖。如果您尚未安装 `uv`，请先安装它（或使用标准 pip）。

```bash
# 安装依赖
uv sync
```

### 2. 配置环境变量

在项目根目录创建 `.env`（推荐）或在 `backend/` 目录创建 `.env`：

```ini
# .env
ORS_API_KEY=your_openrouteservice_api_key
SECRET_KEY=your_jwt_secret_key
# 当前代码中 Celery Redis 地址与数据库路径为代码内固定值：
# Redis: redis://localhost:6379/0
# SQLite: sqlite:///./logistics.db
```

### 3. 数据初始化 (可选)

如果是首次运行，可以使用脚本生成一些测试数据：

```bash
uv run python seed_data.py
```

### 4. 启动服务

**推荐方式 (同时启动 API 和 Worker)**:
```bash
cd backend
uv run python run_dev.py
```

**手动启动 (API Only)**:
```bash
uv run uvicorn app.main:app --reload
```

---

## 🧠 核心算法逻辑

### 车辆路径问题 (CVRP)
我们在 `app/services/optimization.py` 中实现了遗传算法来求解 CVRP：
1.  **编码**: 使用整数列表表示访问顺序，仓库作为分隔符。
2.  **适应度函数**: `总距离 + (罚函数系数 * 超载量)`。
3.  **算子**: 锦标赛选择、有序交叉 (OX)、交换变异。
4.  **混合策略**: 针对大规模数据，先使用 K-Means 聚类将订单分组，再对每组进行并行路径优化。
