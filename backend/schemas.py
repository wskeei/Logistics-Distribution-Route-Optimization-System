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
    username: Optional[str] = None

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str
    address: str
    x: Optional[float] = None
    y: Optional[float] = None

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
    x: Optional[float] = None
    y: Optional[float] = None

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
    customer_ids: Optional[List[int]] = None # Old field, make it optional
    order_ids: Optional[List[int]] = None # New field for CVRP

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
    path_geometries: Optional[List[str]] = None

    class Config:
        from_attributes = True


# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str
    weight: float

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True


# --- Dispatch Schemas ---
class DispatchRequest(BaseModel):
    vehicle_ids: List[int]
    order_ids: List[int]
    depot_id: int

class DispatchResult(BaseModel):
    total_tasks_created: int
    tasks: List[Task]


# --- Order Schemas ---
class OrderProductCreate(BaseModel):
    product_id: int
    quantity: int

class OrderProduct(OrderProductCreate):
    id: int
    product: Product

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    customer_id: int

class OrderCreate(OrderBase):
    items: List[OrderProductCreate]

class OrderUpdate(BaseModel):
    status: Optional[str] = None

class Order(OrderBase):
    id: int
    status: str
    demand: float
    created_at: datetime
    customer: Customer
    items: List[OrderProduct]

    class Config:
        from_attributes = True

# --- Schemas for Simple Optimization Endpoint ---

class SimpleLocation(BaseModel):
    id: int
    x: Optional[float] = None
    y: Optional[float] = None
    address: Optional[str] = None

class OptimizationRequest(BaseModel):
    locations: List[SimpleLocation]
    vehicle_capacity: float = 1000.0 # Provide a default capacity
    population_size: int = 50
    mutation_rate: float = 0.01
    crossover_rate: float = 0.9
    generations: int = 200
    patience: int = 20
    num_vehicles: int = 3 # Used as K in clustering
    algorithm_mode: str = 'ga_only' # 'ga_only' or 'cluster'

class OptimizationResponse(BaseModel):
    total_distance: float
    routes: List[List[int]] # List of routes, each route is a list of location IDs
    path_geometries: List[str]