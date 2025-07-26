import random
from typing import List, Annotated, Optional
import math
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import auth, database, models, schemas, ors_client
from .optimization import solve_vrp, Location

models.Base.metadata.create_all(bind=database.engine)

# ==============================================================================
# API 定义 (API Definitions)
# ==============================================================================

app = FastAPI()

# --- User Authentication Endpoints ---

@app.post("/api/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(database.get_db)
):
    user = auth.get_user(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    print(f"--- Received registration request for username: {user.username} ---", flush=True)
    try:
        db_user = auth.get_user(db, username=user.username)
        print(f"Checking existing user... Found: {db_user}", flush=True)
        if db_user:
            print("User already exists. Raising HTTPException.", flush=True)
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_password = auth.get_password_hash(user.password)
        print("Password hashed successfully.", flush=True)
        
        db_user = models.User(username=user.username, hashed_password=hashed_password)
        print("User model created.", flush=True)
        
        db.add(db_user)
        print("User added to session.", flush=True)
        
        db.commit()
        print("DB commit successful.", flush=True)
        
        db.refresh(db_user)
        print("DB refresh successful.", flush=True)
        
        print(f"--- Successfully registered user: {db_user.username} ---", flush=True)
        return db_user
    except Exception as e:
        print(f"!!! AN UNEXPECTED ERROR OCCURRED: {e} !!!", flush=True)
        raise HTTPException(status_code=500, detail="Internal server error during registration.")

@app.get("/api/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(auth.get_current_user)]
):
    return current_user

# --- Optimization Endpoint (Now Protected) ---

class OptimizationRequest(BaseModel):
    locations: List[Location]
    population_size: int = 50
    mutation_rate: float = 0.01
    crossover_rate: float = 0.85
    generations: int = 500 # 增加最大代数
    patience: int = 50 # 增加耐心值

class OptimizationResponse(BaseModel):
    path: List[int]
    distance: float


# --- Customer CRUD Endpoints ---

@app.get("/api/customers/", response_model=list[schemas.Customer])
def read_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    获取所有客户列表。
    """
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    return customers

@app.post("/api/customers/", response_model=schemas.Customer)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    创建新客户。
    如果只提供了地址，则自动进行地理编码。
    """
    customer_data = customer.model_dump()
    
    # Geocoding logic
    if customer_data.get('x') is None or customer_data.get('y') is None:
        if not customer_data.get('address'):
            raise HTTPException(status_code=400, detail="Either address or coordinates (x, y) must be provided.")
        
        coords = ors_client.geocode(customer_data['address'])
        if not coords:
            raise HTTPException(status_code=400, detail=f"Could not geocode address: {customer_data['address']}")
        
        customer_data['x'] = coords[0] # longitude
        customer_data['y'] = coords[1] # latitude

    db_customer = models.Customer(**customer_data)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.get("/api/customers/{customer_id}", response_model=schemas.Customer)
def read_customer(
    customer_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    获取单个客户详情。
    """
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@app.put("/api/customers/{customer_id}", response_model=schemas.Customer)
def update_customer(
    customer_id: int,
    customer: schemas.CustomerUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    更新客户信息。
    """
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = customer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
    
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.delete("/api/customers/{customer_id}", response_model=schemas.Customer)
def delete_customer(
    customer_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    删除客户。
    """
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(db_customer)
    db.commit()
    return db_customer

# --- Depot CRUD Endpoints ---

@app.get("/api/depots/", response_model=list[schemas.Depot])
def read_depots(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    获取所有仓库列表。
    """
    depots = db.query(models.Depot).offset(skip).limit(limit).all()
    return depots

@app.post("/api/depots/", response_model=schemas.Depot)
def create_depot(
    depot: schemas.DepotCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    创建新仓库。
    如果只提供了地址，则自动进行地理编码。
    """
    depot_data = depot.model_dump()

    # Geocoding logic
    if depot_data.get('x') is None or depot_data.get('y') is None:
        if not depot_data.get('address'):
            raise HTTPException(status_code=400, detail="Either address or coordinates (x, y) must be provided.")
        
        coords = ors_client.geocode(depot_data['address'])
        if not coords:
            raise HTTPException(status_code=400, detail=f"Could not geocode address: {depot_data['address']}")
        
        depot_data['x'] = coords[0] # longitude
        depot_data['y'] = coords[1] # latitude

    db_depot = models.Depot(**depot_data)
    db.add(db_depot)
    db.commit()
    db.refresh(db_depot)
    return db_depot

@app.get("/api/depots/{depot_id}", response_model=schemas.Depot)
def read_depot(
    depot_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    获取单个仓库详情。
    """
    db_depot = db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    if db_depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    return db_depot

@app.put("/api/depots/{depot_id}", response_model=schemas.Depot)
def update_depot(
    depot_id: int,
    depot: schemas.DepotUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    更新仓库信息。
    """
    db_depot = db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    if db_depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    
    update_data = depot.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_depot, key, value)
    
    db.commit()
    db.refresh(db_depot)
    return db_depot

@app.delete("/api/depots/{depot_id}", response_model=schemas.Depot)
def delete_depot(
    depot_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    删除仓库。
    """
    db_depot = db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    if db_depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    
    db.delete(db_depot)
    db.commit()
    return db_depot

# --- Geocoding Endpoints ---

class AutocompleteSuggestion(BaseModel):
    label: str
    coordinates: List[float]

@app.get("/api/geocode/autocomplete", response_model=List[AutocompleteSuggestion])
def get_address_suggestions(
    text: str,
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    (Protected) Get address autocomplete suggestions based on user input.
    """
    if not text or not text.strip():
        return []
    
    suggestions = ors_client.autocomplete(text)
    
    if suggestions is None:
        # The client function already prints the specific error, 
        # so we return a generic 503 Service Unavailable error to the client.
        raise HTTPException(status_code=503, detail="Address suggestion service is currently unavailable.")
        
    return suggestions


class AddressQuery(BaseModel):
    address: str
    region: Optional[str] = None

class CoordinatesResponse(BaseModel):
    x: float # longitude
    y: float # latitude

@app.post("/api/geocode/address", response_model=CoordinatesResponse)
def get_coordinates_for_address(
    query: AddressQuery,
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    (Protected) Geocode a full address string to coordinates, with an optional region for focus.
    """
    if not query.address or not query.address.strip():
        raise HTTPException(status_code=400, detail="Address cannot be empty.")
    
    focus_point = None
    if query.region and query.region.strip():
        # Geocode the region first to get a focus point
        focus_point = ors_client.geocode(query.region)
        if not focus_point:
            print(f"Warning: Could not geocode region '{query.region}' to create a focus point.")

    # Now geocode the main address, using the focus point if available
    coords = ors_client.geocode(query.address, focus_point=focus_point)
    
    if not coords:
        raise HTTPException(status_code=404, detail=f"Could not geocode address: {query.address}")
        
    return CoordinatesResponse(x=coords[0], y=coords[1])
# --- Vehicle CRUD Endpoints ---

@app.get("/api/vehicles/", response_model=list[schemas.Vehicle])
def read_vehicles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    获取所有车辆列表。
    """
    vehicles = db.query(models.Vehicle).offset(skip).limit(limit).all()
    return vehicles

@app.post("/api/vehicles/", response_model=schemas.Vehicle)
def create_vehicle(
    vehicle: schemas.VehicleCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    创建新车辆。
    """
    db_vehicle = models.Vehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@app.get("/api/vehicles/{vehicle_id}", response_model=schemas.Vehicle)
def read_vehicle(
    vehicle_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    获取单个车辆详情。
    """
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return db_vehicle

@app.put("/api/vehicles/{vehicle_id}", response_model=schemas.Vehicle)
def update_vehicle(
    vehicle_id: int,
    vehicle: schemas.VehicleUpdate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    更新车辆信息。
    """
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
# --- Simple Optimization Endpoint (Legacy, but upgraded) ---

@app.post("/api/optimize", response_model=schemas.OptimizationResponse)
def optimize_simple_route(
    request: schemas.OptimizationRequest,
    current_user: Annotated[schemas.User, Depends(auth.get_current_user)]
):
    """
    (Protected) Receives a simple list of locations and returns an optimized route
    using the new openrouteservice-powered Genetic Algorithm.
    This endpoint is for simple, stateless optimization tests.
    """
    # Process locations: geocode if necessary
    for loc in request.locations:
        if loc.x is None or loc.y is None:
            if not loc.address:
                raise HTTPException(status_code=400, detail=f"Location with id {loc.id} must have either coordinates or an address.")
            coords = ors_client.geocode(loc.address)
            if not coords:
                raise HTTPException(status_code=400, detail=f"Could not geocode address for location id {loc.id}: {loc.address}")
            loc.x, loc.y = coords

    # Convert simple locations to the format required by the Genetic Algorithm
    # We assume a default demand of 0 for this simple endpoint.
    locations_for_ga = [
        Location(id=loc.id, x=loc.x, y=loc.y, demand=0)
        for loc in request.locations
    ]

    if not locations_for_ga:
        raise HTTPException(status_code=400, detail="No locations provided for optimization.")

    best_chromosome = solve_vrp(
        locations=locations_for_ga,
        vehicle_capacity=request.vehicle_capacity,
        num_vehicles=request.num_vehicles,
        population_size=request.population_size,
        mutation_rate=request.mutation_rate,
        crossover_rate=request.crossover_rate,
        generations=request.generations,
        patience=request.patience,
        algorithm_mode=request.algorithm_mode
    )

    # Check if a valid route was found
    if best_chromosome.total_distance == float('inf'):
        raise HTTPException(
            status_code=400,
            detail="Optimization failed: Could not find a valid path connecting all locations. Please check if all points are reachable on the road network."
        )
    
    # Extract routes with location IDs
    routes_with_ids = []
    for route in best_chromosome.routes:
        routes_with_ids.append([loc.id for loc in route])

    return schemas.OptimizationResponse(
        total_distance=best_chromosome.total_distance,
        routes=routes_with_ids,
        path_geometries=best_chromosome.geometries
    )

    update_data = vehicle.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_vehicle, key, value)
    
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@app.delete("/api/vehicles/{vehicle_id}", response_model=schemas.Vehicle)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    删除车辆。
    """
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    db.delete(db_vehicle)
    db.commit()
    return db_vehicle

# --- Product CRUD Endpoints ---

@app.post("/api/products/", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/api/products/", response_model=List[schemas.Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/api/products/{product_id}", response_model=schemas.Product)
def read_product(
    product_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# --- Order CRUD Endpoints ---

@app.post("/api/orders/", response_model=schemas.Order)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    # Validate customer
    db_customer = db.query(models.Customer).filter(models.Customer.id == order.customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail=f"Customer with id {order.customer_id} not found")

    # Calculate total demand
    total_demand = 0
    for item in order.items:
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")
        total_demand += db_product.weight * item.quantity

    # Create the order
    db_order = models.Order(
        customer_id=order.customer_id,
        demand=total_demand,
        status=models.OrderStatus.PENDING
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # Create order items
    for item in order.items:
        db_item = models.OrderProduct(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/api/orders/", response_model=List[schemas.Order])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    orders = db.query(models.Order).offset(skip).limit(limit).all()
    return orders

@app.get("/api/orders/{order_id}", response_model=schemas.Order)
def read_order(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order


# --- Task Creation & Optimization Endpoint ---

@app.post("/api/tasks/optimize_cvrp", response_model=schemas.Task)
def create_and_optimize_cvrp_task(
    task_create: schemas.TaskCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    (CVRP) 创建一个新任务，从数据库读取订单信息，执行带容量约束的路径优化，并将结果保存。
    """
    # 1. 验证并获取车辆信息
    if not task_create.vehicle_id:
        raise HTTPException(status_code=400, detail="Vehicle ID is required for CVRP.")
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == task_create.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # 2. 验证并获取仓库信息
    depot = db.query(models.Depot).filter(models.Depot.id == task_create.depot_id).first()
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")

    # 3. 验证并获取订单信息，并将其转换为Location对象
    if not task_create.order_ids:
        raise HTTPException(status_code=400, detail="Order IDs are required for CVRP.")
    orders = db.query(models.Order).filter(models.Order.id.in_(task_create.order_ids)).all()
    if len(orders) != len(task_create.order_ids):
        raise HTTPException(status_code=404, detail="One or more orders not found")
    if not orders:
        raise HTTPException(status_code=400, detail="At least one order is required for optimization")

    # 4. 准备用于优化的地点列表
    depot_location = Location(id=depot.id, x=depot.x, y=depot.y, demand=0)
    customer_locations = [
        Location(id=order.customer.id, x=order.customer.x, y=order.customer.y, demand=order.demand)
        for order in orders
    ]
    locations_for_optimization = [depot_location] + customer_locations

    # 5. 执行遗传算法优化
    ga = GeneticAlgorithm(
        locations=locations_for_optimization,
        vehicle_capacity=vehicle.capacity,
        population_size=100,
        mutation_rate=0.02,
        crossover_rate=0.9,
        generations=1000,
        patience=100
    )
    best_chromosome = ga.run()

    # 6. 创建主任务记录
    db_task = models.Task(
        depot_id=task_create.depot_id,
        vehicle_id=task_create.vehicle_id, # Main vehicle for the task
        status=models.TaskStatus.COMPLETED,
        total_distance=best_chromosome.total_distance
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 7. 保存多条路径的站点顺序
    stop_counter = 1
    for route in best_chromosome.routes:
        for customer_loc in route:
            if customer_loc.id == depot.id: continue # Skip depot
            task_stop = models.TaskStop(
                task_id=db_task.id,
                customer_id=customer_loc.id,
                stop_order=stop_counter
            )
            db.add(task_stop)
            stop_counter += 1
    
    db.commit()
    db.refresh(db_task)
    return db_task

# --- Task CRUD Endpoints (Basic) ---

@app.get("/api/tasks/", response_model=list[schemas.Task])
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    获取所有任务列表。
    """
    tasks = db.query(models.Task).offset(skip).limit(limit).all()
    return tasks

@app.get("/api/tasks/{task_id}", response_model=schemas.Task)
def read_task(
    task_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    获取单个任务详情。
    """
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

# 运行服务器的命令 (在终端中):
# uvicorn backend.main:app --reload

# --- Dispatcher (Multi-Vehicle, Multi-Order) ---
from celery.result import AsyncResult

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[schemas.DispatchResult] = None
    error: Optional[str] = None

@app.post("/api/dispatch/run", status_code=202)
def run_dispatcher_async(
    dispatch_request: schemas.DispatchRequest,
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    Asynchronously trigger the multi-vehicle dispatching task.
    """
    # Move the import inside the function to break the circular import
    from .celery_worker import run_dispatch_task
    task = run_dispatch_task.delay(dispatch_request.model_dump())
    return {"task_id": task.id}

@app.get("/api/dispatch/status/{task_id}", response_model=TaskStatusResponse)
def get_dispatch_status(task_id: str):
    """
    Check the status of a dispatching task.
    """
    task_result = AsyncResult(task_id)
    if task_result.state == 'PENDING':
        return TaskStatusResponse(task_id=task_id, status='Pending')
    elif task_result.state == 'PROGRESS':
        return TaskStatusResponse(task_id=task_id, status='In Progress', result=task_result.info.get('status'))
    elif task_result.state == 'SUCCESS':
        response_data = task_result.result['result']
        return TaskStatusResponse(task_id=task_id, status='Success', result=schemas.DispatchResult.model_validate(response_data))
    elif task_result.state == 'FAILURE':
        return TaskStatusResponse(task_id=task_id, status='Failed', error=str(task_result.info))
    return TaskStatusResponse(task_id=task_id, status=task_result.state)