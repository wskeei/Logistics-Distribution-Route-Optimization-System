from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.session import engine
from .models import sql_models as models
from .api.api import api_router

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Logistics Optimization API")

# Configure CORS
origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Logistics Optimization API"}
