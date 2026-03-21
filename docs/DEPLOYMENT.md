# 📗 部署与运维指南 (Deployment Guide)

本指南针对生产环境和高级开发环境的部署。对于日常快速开发，请参考 `README.md` 中的 Quick Start。

系统由四个核心组件构成：
1.  **Redis**: 消息中间件，用于 Celery 任务队列。
2.  **API Server**: 基于 FastAPI 的后端服务。
3.  **Celery Worker**: 执行耗时算法和后台任务的 Worker 进程。
4.  **Frontend App**: 基于 Vue 3 的前端应用。

---

## 🏗️ 生产环境部署 (Docker 推荐)

虽然目前项目未提供 Dockerfile，但我们强烈建议在生产环境使用 Docker 容器化部署。

### 1. 基础环境
*   **Linux Server** (Ubuntu 22.04 LTS 推荐)
*   **Python 3.10+**
*   **Nginx** (用于反向代理)
*   **Redis** (生产环境建议设置密码)

### 2. 后端部署 (API & Worker)

#### 2.1 安装依赖
推荐使用 `uv` 安装依赖（仓库包含 `uv.lock`）。

```bash
cd backend
uv sync --frozen  # 使用 lock 文件锁死版本
```

#### 2.2 启动 API 服务
当前仓库默认依赖中不包含 `gunicorn`，可直接使用 `uvicorn` 启动：

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如需使用 Gunicorn，请先额外安装后再启动。

#### 2.3 启动 Celery Worker
请确保 Redis 服务可访问。当前代码里 Celery 使用固定地址 `redis://localhost:6379/0`（定义在 `backend/app/core/celery_app.py`）。

```bash
cd backend
PYTHONPATH=.. uv run celery -A backend.app.worker worker --loglevel=info
# 建议配合 Supervisor 或 Systemd 进行进程守护
```

### 3. 前端部署

前端应用为静态资源，构建后部署到 Nginx 即可。

```bash
cd frontend
npm ci        # 清净安装依赖
npm run build # 构建生产包
```

构建完成后，将 `dist/` 目录下的所有文件上传至服务器 Nginx 的 web 根目录（如 `/var/www/html`）。

**Nginx 配置示例**:
```nginx
server {
    listen 80;
    server_name logistics.example.com;

    # 前端静态资源
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html; # SPA 路由重定向
    }

    # 后端 API 反向代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 💻 开发者环境 (Windows/Mac)

### 多终端手动启动
如果您不使用 `run_dev.py` 脚本，可以手动在不同终端启动服务进行调试。

#### 1. 启动 Redis
*   Windows: 确保 Redis 服务已运行。
*   Mac/Linux: `redis-server`

#### 2. 后端 API
```bash
cd backend
uv run uvicorn app.main:app --reload
```

#### 3. Celery Worker (Windows 注意)
Windows 下 Celery 4.x+ 可能会遇到多进程兼容性问题，建议使用 `pool=solo`。

```bash
cd backend
# Windows 推荐模式:
PYTHONPATH=.. uv run celery -A backend.app.worker worker --loglevel=info --pool=solo
```

#### 4. 前端
```bash
cd frontend
npm run dev
```

---

## 🔧 常见故障排查 (Troubleshooting)

| 问题现象 | 可能原因 | 解决方案 |
| :--- | :--- | :--- |
| **Redis Connection Error** | Redis 未启动或配置错误 | 检查 Redis 服务状态，确认 `localhost:6379` 可访问；当前 Celery 地址见 `backend/app/core/celery_app.py`。 |
| **Celery 任务一直 Pending** | Worker 未启动 | 检查 Worker 终端是否有报错，Windows 下尝试添加 `--pool=solo` 参数。 |
| **ModuleNotFoundError** | 运行路径错误 | 优先使用 README 推荐命令；手动启动 Celery 时使用 `PYTHONPATH=.. uv run celery -A backend.app.worker worker --loglevel=info`。 |
| **ORS API Error** | Key 无效或超限 | 检查项目根目录 `.env`（或 `backend/.env`）中的 `ORS_API_KEY` 是否有效，每日配额是否用完。 |
