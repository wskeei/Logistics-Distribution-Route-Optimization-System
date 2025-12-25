# Logistics Distribution Route Optimization System

A comprehensive logistics solution featuring intelligent dispatching, CVRP path optimization, and fleet management.

## 📚 Documentation

-   [**Deployment Guide**](docs/DEPLOYMENT.md): Instructions for installing and running the system on Windows, Mac, and Linux.
-   [**User Manual (SOP)**](docs/USER_MANUAL.md): Step-by-step guide for operators using the system.
-   [**API Documentation**](docs/API.md): Details on backend endpoints and integration.

## 🚀 Quick Start

1.  **Backend**: `uvicorn backend.main:app --reload`
2.  **Worker**: `python -m celery -A backend.celery_worker worker --loglevel=info`
3.  **Frontend**: `npm run dev` (in `frontend/logistics-app`)
4.  **Redis**: Ensure Redis service is running.

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed prerequisites and setup steps.

## ✨ Features

-   **Dashboard**: Overview of operations.
-   **Order Management**: Create and track customer orders.
-   **Fleet Management**: Manage vehicle capacity and status.
-   **Intelligent Dispatching**: Automated route planning using Genetic Algorithms.
-   **Visual Tracking**: Interactive map for routes and stops.

## 🛠 Tech Stack

-   **Frontend**: Vue 3, Element Plus, Vite
-   **Backend**: Python, FastAPI, SQLAlchemy
-   **Async Tasks**: Celery, Redis
-   **Optimization**: Custom Genetic Algorithm + OpenRouteService