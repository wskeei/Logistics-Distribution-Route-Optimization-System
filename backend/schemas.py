from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str
    address: str
    x: float
    y: float

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None

class Customer(CustomerBase):
    id: int

    class Config:
        from_attributes = True

# --- Depot Schemas ---
class DepotBase(BaseModel):
    name: str
    address: str
    x: float
    y: float

class DepotCreate(DepotBase):
    pass

class DepotUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None

class Depot(DepotBase):
    id: int

    class Config:
        from_attributes = True

# --- Vehicle Schemas ---
class VehicleBase(BaseModel):
    name: str
    capacity: float = 100.0

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[float] = None

class Vehicle(VehicleBase):
    id: int

    class Config:
        from_attributes = True

# --- TaskStop Schemas ---
class TaskStopBase(BaseModel):
    customer_id: int
    stop_order: int

class TaskStopCreate(TaskStopBase):
    pass

class TaskStop(TaskStopBase):
    id: int
    customer: Customer

    class Config:
        from_attributes = True

# --- Task Schemas ---
class TaskBase(BaseModel):
    vehicle_id: Optional[int] = None
    depot_id: int

class TaskCreate(TaskBase):
    customer_ids: List[int] # List of customer IDs to include in the task

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    vehicle_id: Optional[int] = None
    total_distance: Optional[float] = None

class Task(TaskBase):
    id: int
    created_at: datetime
    status: str
    total_distance: Optional[float]
    vehicle: Optional[Vehicle]
    depot: Depot
    stops: List[TaskStop]

    class Config:
        from_attributes = True