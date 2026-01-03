# 📡 接口文档 (API Documentation)

本系统后端基于 FastAPI 构建，提供高性能的 RESTful API。本文档仅列出核心业务接口，完整的交互式文档（包含请求测试）请参考 Swagger UI。

> **交互式文档地址**: `http://localhost:8000/docs`

---

## 🔐 认证与授权 (Auth)

所有业务接口均需要通过 JWT (Bearer Token) 验证。

### 1. 获取访问令牌 (Login)
*   **端点**: `POST /api/token`
*   **用途**: 用户登录并获取 Access Token。
*   **Content-Type**: `application/x-www-form-urlencoded`
*   **参数**:
    *   `username`: 用户名
    *   `password`: 密码
*   **返回**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1Ni...",
      "token_type": "bearer"
    }
    ```

### 2. 注册新用户
*   **端点**: `POST /api/users/`
*   **参数 (Body)**:
    ```json
    {
      "username": "admin",
      "password": "strongpassword"
    }
    ```

---

## 📦 核心资源管理 (Resource Management)

### 1. 客户管理 (Customers)
*   `GET /api/customers/`: 获取客户列表。
*   `POST /api/customers/`: 创建新客户。支持自动地理编码（若仅提供地址，系统自动计算 `x, y` 坐标）。
*   `GET /api/customers/{id}`: 获取详情。
*   `PUT /api/customers/{id}`: 更新信息。
*   `DELETE /api/customers/{id}`: 删除客户。

### 2. 车队管理 (Vehicles)
*   `GET /api/vehicles/`: 获取车辆列表。
*   `POST /api/vehicles/`: 录入新车辆。
    *   **Capacity**: 载重/容量是一个关键的约束参数。

### 3. 仓库/网点 (Depots)
*   `GET /api/depots/`: 获取仓库列表。
*   `POST /api/depots/`: 创建新仓库。

### 4. 货物/产品 (Products)
*   `GET /api/products/`: 获取产品库。
*   `POST /api/products/`: 创建产品（需指定单位重量 `weight`）。

### 5. 订单管理 (Orders)
*   `GET /api/orders/`: 获取订单列表。
*   `POST /api/orders/`: 创建订单/工单。
    *   需要关联 `customer_id` 和产品明细 `items`。系统会自动计算订单总需求量 (Demand)。

---

## 🚀 智能调度与优化 (Optimization)

### 1. 地理服务
*   **地址自动补全**: `GET /api/geocode/autocomplete?text={keyword}`
*   **地址转坐标**: `POST /api/geocode/address`

### 2. 单车路径优化 (CVRP)
*   **端点**: `POST /api/tasks/optimize_cvrp`
*   **用途**: 为**指定的一辆车**和**一组订单**生成最优路径。
*   **逻辑**: 
    1. 校验容量约束。
    2. 使用遗传算法求解最短路径。
    3. 生成 Task 记录并保存站点顺序。

### 3. 多车智能调度中心 (Dispatcher)
*   **端点**: `POST /api/dispatch/run` (异步)
*   **用途**: 系统自动将成百上千个订单分配给多辆车。
*   **逻辑**:
    1. **K-Means 聚类**: 基于地理位置将订单分组。
    2. **任务分配**: 将订单簇分配给合适的车辆。
    3. **并行计算**: 触发 Celery Worker 异步计算每辆车的路径。
*   **返回**: `task_id` (用于轮询状态)。

### 4. 查询调度状态
*   **端点**: `GET /api/dispatch/status/{task_id}`
*   **用途**: 轮询异步调度任务的进度。
*   **状态**: 
    *   `PENDING`: 等待执行
    *   `PROGRESS`:正在计算 (聚类/规划中)
    *   `SUCCESS`: 完成，返回生成的 Task 列表
    *   `FAILURE`: 失败及原因
