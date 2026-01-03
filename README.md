# 🚛 物流配送路径优化系统 (Logistics Distribution Route Optimization System)

> 专业的企业级物流调度平台，集成智能路径算法与现代化可视化界面。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Vue](https://img.shields.io/badge/Vue-3.0%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal)

## 📖 项目简介

本项目是一个现代化的物流配送管理解决方案，专为解决复杂的车辆路径问题 (CVRP) 而设计。系统采用前后端分离架构，结合了遗传算法 (Genetic Algorithm) 与 OpenRouteService 地图服务，实现了从订单汇聚、自动调度到路径可视化的全流程闭环。

核心价值在于**降低运输成本**、**提高配送效率**以及**提升用户体验**。

## ✨ 核心特性

### 🧠 智能核心
*   **高级调度算法**: 内置改进型遗传算法，支持带容量约束的车辆路径规划 (CVRP)，自动均衡车队负载。
*   **精准路径规划**: 集成 OpenRouteService，提供基于真实路网的精确导航和距离计算。
*   **智能聚类**: 采用 K-Means 算法对大规模订单进行地理聚类，优化多车任务分配。

### 💻 现代化体验
*   **沉浸式 UI**: 基于 Glassmorphism (玻璃拟态) 设计语言，提供清新、现代的视觉体验。
*   **流畅交互**: 深度集成 Motion 动画库，操作反馈丝滑自然。
*   **实时大屏**: 动态的监控仪表盘，实时展示车辆状态、订单进度和关键运营指标 (KPI)。

### 🛡️ 企业级架构
*   **模块化后端**: 基于 FastAPI 的清晰分层架构 (API/Core/Services)，易于扩展和维护。
*   **异步任务处理**: 引入 Celery + Redis 处理耗时计算，确保高并发下的系统响应速度。
*   **安全认证**: 完善的 JWT 身份验证与权限管理体系。

## 🛠️ 技术栈

| 领域 | 技术选型 | 备注 |
| :--- | :--- | :--- |
| **前端架构** | **Vue 3** (Composition API) | 渐进式框架 |
| **UI 组件** | **Element Plus** + **Tailwind CSS** | 企业级组件与原子化样式 |
| **可视化** | **Leaflet** / **ECharts** | 地图与数据图表 |
| **后端框架** | **FastAPI** | 高性能异步 Python Web 框架 |
| **数据持久化** | **SQLAlchemy** (SQLite/PostgreSQL) | ORM 映射 |
| **任务队列** | **Celery** + **Redis** | 异步调度 |
| **环境管理** | **uv** | 极速 Python 包管理器 |

## 🚀 快速开始

### 1. 环境准备
确保您的环境满足以下要求：
*   **Python**: 3.10+ (推荐使用 `uv` 管理)
*   **Node.js**: 18+
*   **Redis**: 服务需在本地启动或通过 Docker 运行

### 2. 初始化数据 (推荐)
如果您是初次运行，建议先生成全国演示数据：

```bash
cd backend
# 使用 seed_data.py 生成测试数据 (包含全国主要城市的车辆、订单等)
uv run python seed_data.py
```

### 3.后端服务启动
我们提供了一个增强版启动脚本 `run_dev.py`，它会自动释放 8000 端口并同时管理 Celery Worker：

```bash
cd backend

# 1. 安装项目依赖
uv sync

# 2. 启动服务 (同时启动 API 和 Worker)
uv run python run_dev.py
```
> **提示**: 脚本启动时会自动检查并清理占用 8000 端口的进程，无需手动 Kill。

### 4. 前端应用启动
```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```

### 5. 访问系统
服务启动后，您可以通过以下地址访问：
- **Web 可视化大屏**: [http://localhost:5173](http://localhost:5173)
- **后端 API 文档**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Celery 任务监控**: (如已配置 Flower) [http://localhost:5555](http://localhost:5555)



## 📂 目录结构

```
Logistics-System/
├── backend/                # 后端工程
│   ├── app/                # 应用源码
│   │   ├── api/            # 接口层
│   │   ├── core/           # 核心配置与安全
│   │   ├── services/       # 业务逻辑 (算法, ORS)
│   │   └── ...
│   ├── run_dev.py          # 统一启动脚本
│   └── ...
├── frontend/               # 前端工程
│   ├── src/                # Vue 源码
│   └── ...
├── docs/                   # 项目文档
└── logs/                   # 运行日志
```

## 📚 文档资源

*   [📘 接口文档 (API)](docs/API.md)
*   [📗 部署指南 (Deployment)](docs/DEPLOYMENT.md)
*   [📙 用户手册 (User Manual)](docs/USER_MANUAL.md)

## 📄 许可证

MIT License