# 🖥️ 前端工程 (Frontend)

本项目基于 **Vue 3** + **Vite** 构建，采用了现代化的技术栈以提供流畅的用户体验。

## 🛠️ 技术栈清单

*   **框架**: [Vue 3](https://vuejs.org/) (Composition API)
*   **构建工具**: [Vite](https://vitejs.dev/)
*   **UI 组件库**: [Element Plus](https://element-plus.org/)
*   **样式框架**: [Tailwind CSS v4](https://tailwindcss.com/)
*   **状态管理**: Pinia (计划中) / Reactive
*   **路由管理**: Vue Router 4
*   **动画库**: @vueuse/motion
*   **地图组件**: Leaflet / OpenLayers (用于展示 OpenRouteService 瓦片)

## 📦 目录结构

```
frontend/
├── src/
│   ├── assets/            # 静态资源 (图片, 字体)
│   ├── components/        # 公共组件 (Navigation, MapView...)
│   ├── views/             # 页面视图 (Login, Dashboard, Dispatch...)
│   ├── router/            # 路由定义
│   ├── App.vue            # 根组件
│   └── main.js            # 入口文件
├── index.html             # HTML 模板
├── vite.config.js         # Vite 配置
└── package.json           # 依赖清单
```

## 🚀 开发指南

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```
访问 `http://localhost:5173`。

### 3. 构建生产版本

```bash
npm run build
```
构建产物将输出到 `dist/` 目录。

### 4. 环境变量
项目使用 `.env` 文件管理环境变量（如后端 API 地址）。
*   `VITE_API_BASE_URL`: 后端服务地址 (默认 `http://localhost:8000`)

---

## 🎨 UI 设计规范
本项目采用 **Glassmorphism (玻璃拟态)** 设计风格：
*   **背景**: 使用渐变色或模糊背景图。
*   **卡片**: 高透明度背景 + 背景模糊 (Backdrop Filter) + 白色边框。
*   **交互**: 强调 Hover 态的光效与流畅的过渡动画。
