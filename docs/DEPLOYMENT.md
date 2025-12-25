# Deployment & Operation Guide

This system consists of four main components that need to run simultaneously:
1.  **Redis** (Message Broker)
2.  **Backend API** (FastAPI)
3.  **Celery Worker** (Background Tasks)
4.  **Frontend App** (Vue 3)

## Prerequisites

-   **Python 3.9+**
-   **Node.js 16+** & **npm**
-   **Redis** installed and running on default port `6379`.

## Installation

### 1. Backend Setup

Navigate to the project root directory.

```bash
# It is recommended to create a virtual environment
python -m venv venv
# Activate it:
#   Windows: .\venv\Scripts\activate
#   Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend/logistics-app
npm install
```

## Running the System

You will need **4 separate terminal windows**.

### Terminal 1: Redis
Ensure Redis is running.
-   **Mac/Linux**: `redis-server`
-   **Windows**: Start your Redis service.

### Terminal 2: Celery Worker
Navigate to the project root.

```bash
# Mac/Linux/Windows
python -m celery -A backend.celery_worker worker --loglevel=info
```
*Note: On Windows, if you encounter issues, you may need to install `eventlet` and run with `-P eventlet`.*

### Terminal 3: Backend API
Navigate to the project root.

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
API docs will be available at: `http://localhost:8000/docs`

### Terminal 4: Frontend Application
Navigate to `frontend/logistics-app`.

```bash
npm run dev
```
The application will be available at: `http://localhost:5173` (or the port shown in the terminal).

## Troubleshooting

-   **Redis Connection Error**: Check if Redis is running and reachable at `localhost:6379`.
-   **Module Not Found**: Ensure you have activated your virtual environment and installed `requirements.txt`.
-   **CORS Errors**: The backend is configured to allow CORS from localhost. If you change ports, update `backend/main.py`.
