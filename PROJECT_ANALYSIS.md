# 物流路径规划配送系统：开发与维护指南

本文档是“物流路径规划配送系统”的官方开发与维护指南，旨在为新接手的开发者提供一个全面、深入的参考，确保项目的顺利交接与未来扩展。

## 1. 项目概述

本项目是一个基于现代Web技术的智能物流调度平台。它旨在解决核心的**带容量约束的车辆路径问题 (CVRP)**，通过智能算法，为多批订单和多辆车自动生成优化的配送方案。系统具备订单管理、多车联合调度、异步任务处理和现代化的用户界面等核心功能。

## 2. 技术架构详解

系统采用前后端分离的架构，并通过异步任务队列处理计算密集型任务，确保了系统的高响应性和可扩展性。

### 2.1. 总体架构图

```mermaid
graph TD
    subgraph "用户界面 (Frontend - Vue.js + Element Plus)"
        A[登录/注册]
        B[订单管理]
        C[客户管理]
        D[车辆管理]
        E[仓库管理]
        F[**智能调度中心**]
        G[任务列表与监控]
        H[数据看板]
    end

    subgraph "后端服务 (Backend - FastAPI)"
        I[用户认证 API]
        J[订单 CRUD API]
        K[客户 CRUD API]
        L[车辆 CRUD API]
        M[仓库 CRUD API]
        N[**CVRP 优化 API (内部调用)**]
        O[**异步调度任务 API**]
        P[任务状态查询 API]
    end

    subgraph "核心业务逻辑 (Core Logic)"
        Q[**遗传算法 (CVRP Solver)**]
        R[**多车任务分配器 (K-Means + Greedy)**]
        S[**后台任务处理器 (Celery + Redis)**]
    end

    subgraph "数据存储 (Database - SQLAlchemy)"
        T[用户表]
        U[客户表]
        V[车辆表]
        W[仓库表]
        X[**货物表**]
        Y[**订单表**]
        Z[任务与路径表]
    end

    %% Connections
    F -- "触发异步任务" --> O
    O -- "发送任务到队列" --> S
    S -- "执行调度逻辑" --> R
    R -- "调用算法" --> Q
    Q -- "返回最优路径" --> R
    R -- "保存结果" --> Z
    G -- "查询状态" --> P
    P -- "查询Celery后端" --> S
```

### 2.2. 技术选型

-   **后端**: **FastAPI** 提供了高性能的API接口。**SQLAlchemy** 作为ORM与数据库交互。**Celery** 和 **Redis** 构成了强大的异步任务处理系统。**Scikit-learn** 用于实现订单的地理位置聚类。
-   **前端**: **Vue.js 3** (Composition API) 提供了现代化的开发体验。**Element Plus** 作为UI组件库，快速构建美观的界面。**Pinia** (替代Vuex) 用于状态管理，**Vue Router** 负责页面路由。

## 3. 核心模块深入解析

### 3.1. 后端 (`/backend`)

#### 3.1.1. 数据模型 (`models.py`)
- **核心关系**: `Order` 是业务的核心。一个 `Order` 关联一个 `Customer`，并通过 `OrderProduct` 中间表与多个 `Product` 建立多对多关系。`Task` 则记录了调度结果，关联 `Vehicle` 和多个 `TaskStop`。
- **关键字段**: `Vehicle.capacity` (车辆运力) 和 `Order.demand` (订单需求量) 是CVRP算法的关键输入。

#### 3.1.2. CVRP遗传算法 (`main.py: GeneticAlgorithm`)
- **染色体设计**: 一个染色体 (`Chromosome`) 代表一个完整的配送方案，其基因 (`genes`) 是一个**客户点**的随机排列序列。
- **适应度函数 (`calculate_fitness`)**: 这是算法的灵魂。它会遍历基因序列，模拟车辆装载过程：
    1. 依次将客户点的需求量累加。
    2. 当累加的需求量将要超过车辆运力时，就结束当前车辆的路径（返回仓库），并开启一辆新车。
    3. 最终将一个长的客户序列解析为多条不超载的路径。
    4. 适应度 = `所有路径总距离` + `超载惩罚`。通过这种方式，超载的解在进化中会被自然淘汰。

#### 3.1.3. 智能调度器 (`celery_worker.py: run_dispatch_task`)
- **异步执行**: 整个调度逻辑被封装在一个Celery任务中，以避免阻塞API。
- **核心流程**:
    1. **聚类**: 使用 `sklearn.cluster.KMeans` 对所有订单的客户坐标进行地理位置聚类，将邻近的订单分组。簇的数量取决于可用车辆数。
    2. **贪心分配**: 将车辆按运力从大到小排序，将订单簇按总需求量从大到小排序。依次尝试将最大的订单簇分配给最大的可用车辆。
    3. **调用CVRP**: 为每个成功分配了订单簇的车辆，调用 `GeneticAlgorithm` 来计算其内部的最优路径。
    4. **结果持久化**: 将每条优化后的路径保存为一个 `Task` 记录。

### 3.2. 前端 (`/frontend/logistics-app`)

#### 3.2.1. 状态管理 (`store.js`)
- **Pinia**: 使用 Pinia (`useAuthStore`) 来管理用户的认证状态（Token、用户名等）。这是实现页面访问控制和API请求认证的基础。
- **API请求**: 在每个需要认证的页面（如 `Orders.vue`），通过 `useAuthStore()` 获取Token，并将其加入到 `fetch` 请求的 `Authorization` 头中。

#### 3.2.2. 核心页面逻辑 (`views/`)
- **数据展示**: 主要使用 `ElCard` 和 `ElTable` 组件来展示列表数据。通过 `onMounted` 生命周期钩子，在组件加载时调用 `fetch` 函数从后端获取数据。
- **CRUD操作**:
    - **创建/编辑**: 使用 `ElDialog` 和 `ElForm` 创建弹窗表单。通过一个 `isEdit` 标志位来复用同一个弹窗。表单提交时，根据 `isEdit` 的值决定发送 `POST` 或 `PUT` 请求。
    - **删除**: 使用 `ElMessageBox.confirm` 来提供二次确认，防止用户误删。
- **调度中心 (`Dispatcher.vue`)**: 这是最复杂的页面，它演示了一个完整的前后端异步交互流程：
    1. `Promise.all` 并行获取订单、车辆、仓库列表。
    2. 用户选择数据后，点击按钮调用 `startDispatch` 函数。
    3. `startDispatch` 发送 `POST` 请求到 `/api/dispatch/run`，**立即**获得一个 `task_id`。
    4. 启动一个定时器 (`setInterval`)，该定时器反复调用 `pollTaskStatus` 函数。
    5. `pollTaskStatus` 函数向 `/api/dispatch/status/{task_id}` 发送 `GET` 请求，获取后台任务的实时状态，并更新UI。
    6. 当任务状态变为 `Success` 或 `Failure` 时，清除定时器，并展示最终结果。

## 4. 开发环境与运行

请参考根目录下的 [`README.md`](README.md) 文件。该文件提供了详细的、分步的环境搭建和项目启动命令，并已针对Windows环境下的常见问题进行了修正。

## 5. 二次开发建议

- **完善订单编辑**: 当前 `Orders.vue` 页面尚未实现编辑功能，可以参照 `Products.vue` 的逻辑进行补充。
- **地图可视化**: 集成地图API（如高德地图、Google Maps），在前端将规划好的路径和车辆位置进行可视化展示。
- **引入时间窗**: 在 `Order` 模型中增加 `time_window_start` 和 `time_window_end` 字段，并将算法升级为VRPTW（带时间窗的车辆路径问题），以支持更复杂的业务场景。
- **数据库迁移**: 当前使用SQLite，在生产环境中建议替换为更强大的数据库（如PostgreSQL），并引入 `Alembic` 等工具进行数据库迁移管理。