# 物流配送路径优化系统 - 运行手册

本文档提供了在 macOS 和 Windows 操作系统上安装、配置和运行本项目的详细步骤。

## 1. 架构概览

本项目是一个全栈应用，包含：
- **前端**: 基于 Vue.js 和 Vite 构建的单页应用。
- **后端**: 基于 Python、FastAPI 和 Celery 构建的 API 服务。
- **数据库**: 使用 SQLite 作为数据库，无需额外安装。
- **消息队列**: 使用 Redis 作为 Celery 的消息代理和结果后端，处理耗时的异步任务（如路径优化）。

## 2. 先决条件

在开始之前，请确保您的系统上安装了以下软件：

- **Conda**: 用于管理 Python 环境。您可以从 [Anaconda官网](https://www.anaconda.com/products/distribution) 下载并安装。
- **Python**: Conda 会在创建环境时自动为您安装。
- **Node.js**: 推荐版本 18.x (LTS) 或更高。
- **Git**: 用于克隆项目代码。

---

## 3. 在 macOS 上运行

### 3.1. 安装依赖

如果您尚未安装 Homebrew，请先安装它。Homebrew 是 macOS 的包管理器。
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

使用 Homebrew 安装 Python, Node.js 和 Redis。
```bash
brew install python node redis
```

### 3.2. 启动 Redis

使用 Homebrew services 在后台启动 Redis 服务。
```bash
brew services start redis
```
您可以使用 `brew services list` 来确认 Redis 是否正在运行。

### 3.3. 设置和运行后端

1.  **进入项目根目录**
    ```bash
    # 假设您已经通过 git clone 将项目下载到本地
    cd /path/to/Logistics-Distribution-Route-Optimization-System
    ```

2.  **创建并激活 Conda 虚拟环境**
    我们建议使用 Python 3.9。
    ```bash
    conda create --name route python=3.9 -y
    conda activate route
    ```

3.  **安装后端依赖**
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **启动 Celery Worker (需要新开一个终端)**
    - 确保您处于项目根目录并且虚拟环境已激活。
    ```bash
    celery -A backend.celery_worker worker --loglevel=info
    ```

5.  **启动 FastAPI 应用 (需要再新开一个终端)**
    - 确保您处于项目根目录并且虚拟环境已激活。
    ```bash
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```

### 3.4. 设置和运行前端

1.  **进入前端项目目录 (需要再新开一个终端)**
    ```bash
    cd frontend/logistics-app
    ```

2.  **安装 Node.js 依赖**
    ```bash
    npm install
    ```

3.  **启动前端开发服务器**
    ```bash
    npm run dev
    ```

---

## 4. 在 Windows 上运行

### 4.1. 安装依赖

- **Python**: 从 [Python 官网](https://www.python.org/downloads/) 下载并安装。**在安装时，请务必勾选 "Add Python to PATH"**。
- **Node.js**: 从 [Node.js 官网](https://nodejs.org/) 下载并安装 LTS 版本。

### 4.2. 启动 Redis

本项目自带了 Redis for Windows 的便携版本。

1.  **解压 Redis**
    如果 `Redis-8.0.3-Windows-x64-cygwin-with-Service.zip` 尚未解压，请先解压它。

2.  **启动 Redis 服务器**
    打开一个新的命令提示符 (cmd) 或 PowerShell，进入 Redis 目录并运行 `start.bat`。
    ```cmd
    cd Redis-8.0.3-Windows-x64-cygwin-with-Service
    start.bat
    ```
    这会启动 Redis 服务器。请保持此窗口开启。

### 4.3. 设置和运行后端

1.  **进入项目根目录**
    打开一个新的命令提示符 (cmd) 或 PowerShell。
    ```cmd
    # 假设您已经通过 git clone 将项目下载到本地
    cd C:\path\to\Logistics-Distribution-Route-Optimization-System
    ```

2.  **创建并激活 Conda 虚拟环境**
    我们建议使用 Python 3.9。
    ```cmd
    conda create --name route python=3.9 -y
    conda activate route
    ```

3.  **安装后端依赖**
    ```cmd
    pip install -r backend\requirements.txt
    ```

4.  **启动 Celery Worker (需要新开一个终端)**
    - 确保您处于项目根目录并且虚拟环境已激活。
    ```cmd
    celery -A backend.celery_worker worker --loglevel=info
    ```

5.  **启动 FastAPI 应用 (需要再新开一个终端)**
    - 确保您处于项目根目录并且虚拟环境已激活。
    ```cmd
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```

### 4.4. 设置和运行前端

1.  **进入前端项目目录 (需要再新开一个终端)**
    ```cmd
    cd frontend\logistics-app
    ```

2.  **安装 Node.js 依赖**
    ```cmd
    npm install
    ```

3.  **启动前端开发服务器**
    ```cmd
    npm run dev
    ```

---

## 5. 访问应用

当所有服务都成功启动后：
- **后端 API** 将在 `http://localhost:8000` 上可用。
- **前端应用** 将在 `http://localhost:5173` (或 `npm run dev` 输出的另一个端口) 上可用。

在浏览器中打开前端应用的地址即可访问系统。