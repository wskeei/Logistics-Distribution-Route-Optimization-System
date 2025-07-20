# 物流路径规划配送系统

这是一个功能增强版的物流路径规划与配送系统。在原有基础上，系统增加了订单管理、带容量约束的多车路径规划 (CVRP)、以及基于后台任务的智能调度中心。

## 功能特性

- **现代化的UI**: 基于 Vue 3 和 Element Plus 构建，提供清晰、美观的操作界面。
- **核心业务模块**:
    - **货物管理**: 对配送的货物进行统一管理。
    - **订单管理**: 创建、查看、管理客户订单，自动计算订单需求。
    - **客户/车辆/仓库管理**: 基础数据的增删改查。
- **智能调度中心**:
    - **多车联合调度**: 接收一批订单和可用车辆，通过地理位置聚类和贪心算法，自动为车队分配任务。
    - **CVRP路径优化**: 为每辆分配了任务的车辆计算考虑其运力限制的最优配送路径。
- **异步任务处理**:
    - 基于 Celery 和 Redis，将耗时的调度计算放入后台执行，避免API超时，提升用户体验。
    - 提供任务状态查询接口。

## 技术栈

- **后端**: FastAPI, SQLAlchemy, Celery, Scikit-learn
- **前端**: Vue.js 3, Vue Router, Pinia, Element Plus, Vite
- **数据库**: SQLite
- **消息队列**: Redis

## 运行与部署指南

为了成功运行本项目，您需要启动四个独立的服务：Redis, Celery Worker, Backend API, 和 Frontend App。

### 步骤 1: 环境准备

1.  **安装 Python 依赖**:
    ```bash
    pip install -r backend/requirements.txt
    ```

2.  **安装 Node.js 依赖**:
    ```bash
    cd frontend/logistics-app
    npm install
    cd ../..
    ```

3.  **安装并启动 Redis**:
    请确保您的系统上已经安装了 Redis。您可以通过官网下载或使用包管理器（如 `brew`, `apt`, `choco`）安装。启动 Redis 服务器（通常无需额外配置）。

### 步骤 2: 启动服务

请打开**四个独立**的终端窗口，并按顺序执行以下命令：

**终端 1: 启动 Celery Worker**
(在项目根目录 `d:/Logistics Distribution Route Optimization System` 下运行)
```bash
python -m celery -A backend.celery_worker worker --loglevel=info
```
*这个窗口将显示 Celery 任务的执行日志。*

**终端 2: 启动后端 API 服务器**
(在项目根目录 `d:/Logistics Distribution Route Optimization System` 下运行)
```bash
uvicorn backend.main:app --reload
```
*这个窗口将显示 API 请求日志。*

**终端 3: 启动前端开发服务器**
(在项目根目录 `d:/Logistics Distribution Route Optimization System` 下运行)
```bash
cd frontend/logistics-app
npm run dev
```
*这个窗口将显示 Vite 的启动信息和前端应用的访问地址（通常是 `http://localhost:5173`）。*

**终端 4: (可选) 监控 Redis**
您可以使用 `redis-cli` 来监控 Celery 任务队列的情况。
```bash
redis-cli
monitor
```

### 步骤 3: 测试系统

1.  在浏览器中打开前端应用的地址。
2.  **注册/登录** 一个新用户。
3.  **数据准备**:
    -   在 **客户管理** 页面添加几个客户。
    -   在 **货物管理** 页面添加几种货物（并指定重量）。
    -   在 **车辆管理** 页面添加几辆车（并指定运力）。
    -   在 **订单管理** 页面创建几个订单，将货物分配给客户。
4.  **运行调度**:
    -   进入 **调度中心** 页面。
    -   选择您刚刚创建的订单和车辆。
    -   点击“开始调度”按钮。
    -   您应该能看到一个任务ID被返回。页面可以轮询 `/api/dispatch/status/{task_id}` 来获取实时状态。
5.  **查看结果**:
    -   调度完成后，进入 **任务列表** 页面，您将看到为每辆车生成的配送任务及其详细路径。

---
这份文档为您提供了完整的操作指南。至此，我们对整个项目的重构和增强工作已经全部完成。