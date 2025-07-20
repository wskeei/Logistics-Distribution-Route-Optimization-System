import random
from typing import List, Annotated, Optional
import math
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import auth, database, models, schemas

models.Base.metadata.create_all(bind=database.engine)

# ==============================================================================
# 1. 数据结构定义 (Data Structures)
# ==============================================================================

class Location(BaseModel):
    """
    代表一个地理位置点，可以是仓库或客户。
    增加了 demand 字段以支持CVRP。
    """
    id: int
    x: float
    y: float
    demand: float # 需求量

class Chromosome:
    """
    代表一个个体（一个完整的多车配送方案）。
    基因 (genes) 是一个地点的列表，其中仓库(id=0)作为分隔符。
    适应度 (fitness) 代表方案的总成本（例如总距离），值越小越好。
    """
    def __init__(self, genes: List[Location]):
        self.genes = genes
        self.fitness = float('inf')
        self.routes: List[List[Location]] = [] # 将解析出的多条路径存储在这里
        self.total_distance = 0
        self.capacity_violation = 0 # 容量违规惩罚

    def __repr__(self):
        return f"Chromosome(Fitness: {self.fitness:.2f}, Distance: {self.total_distance:.2f}, Capacity Violation: {self.capacity_violation})"

# ==============================================================================
# 2. 遗传算法核心类 (Genetic Algorithm Core)
# ==============================================================================

class GeneticAlgorithm:
    """
    封装遗传算法的主要流程。
    已升级为支持CVRP（带容量约束的车辆路径问题）。
    """
    def __init__(self, locations: List[Location], vehicle_capacity: float, population_size: int, mutation_rate: float, crossover_rate: float, generations: int, patience: int = 20):
        """
        初始化遗传算法参数。
        :param locations: 所有需要访问的地点列表（仓库为第一个）。
        :param vehicle_capacity: 车辆的运载能力。
        :param population_size: 种群大小。
        :param mutation_rate: 变异率。
        :param crossover_rate: 交叉率。
        :param generations: 最大迭代代数。
        :param patience: 连续多少代最优解未改善则提前停止。
        """
        self.locations = locations
        self.vehicle_capacity = vehicle_capacity
        self.depot = locations[0]
        self.customers = locations[1:]
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.generations = generations
        self.patience = patience
        self.population: List[Chromosome] = []

    def run(self):
        """执行遗传算法的主循环。"""
        print("遗传算法开始...")
        # 1. 初始化种群
        self.initialize_population()
        print(f"初始种群创建完毕，大小: {len(self.population)}")

        # 首次计算适应度
        self.calculate_fitness()
        
        best_fitness_so_far = float('inf')
        generations_without_improvement = 0

        for i in range(self.generations):
            # 1. 选择
            new_population = self.selection()

            # 2. 交叉与变异
            offspring_population = self.crossover_and_mutate(new_population)

            # 3. 形成新一代种群 (精英主义：保留上一代最优解)
            best_of_last_gen = min(self.population, key=lambda c: c.fitness)
            self.population = [best_of_last_gen] + offspring_population[:self.population_size - 1]

            # 4. 计算新种群的适应度
            self.calculate_fitness()

            # 打印当前最优解
            current_best_chromosome = self.population[0]
            print(f"第 {i+1} 代: 最优解 = {current_best_chromosome}", flush=True)

            # 5. 检查是否满足提前停止条件
            if current_best_chromosome.fitness < best_fitness_so_far:
                best_fitness_so_far = current_best_chromosome.fitness
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            if generations_without_improvement >= self.patience:
                print(f"最优解连续 {self.patience} 代未改善，算法提前结束于第 {i+1} 代。")
                break

        print("遗传算法结束。")
        return min(self.population, key=lambda c: c.fitness)

    def calculate_fitness(self):
        """
        计算整个种群中每个个体的适应度。
        这个版本包含了对CVRP的容量约束检查。
        """
        CAPACITY_PENALTY = 1000  # 超载惩罚系数

        for chromosome in self.population:
            chromosome.routes = []
            chromosome.total_distance = 0
            chromosome.capacity_violation = 0
            
            # 1. 解析基因序列为多条路径
            current_route = [self.depot]
            current_demand = 0
            
            for gene in chromosome.genes:
                gene_demand = gene.demand
                if current_demand + gene_demand > self.vehicle_capacity:
                    # 当前车辆装不下，结束当前路径，开启新路径
                    chromosome.routes.append(current_route)
                    current_route = [self.depot, gene]
                    current_demand = gene_demand
                else:
                    # 加入当前路径
                    current_route.append(gene)
                    current_demand += gene_demand
            
            # 添加最后一条路径
            if len(current_route) > 1:
                chromosome.routes.append(current_route)

            # 2. 计算总距离和惩罚
            for route in chromosome.routes:
                route_distance = 0
                route_demand = sum(loc.demand for loc in route)
                
                # 计算路径距离
                for i in range(len(route) - 1):
                    route_distance += calculate_distance(route[i], route[i+1])
                route_distance += calculate_distance(route[-1], self.depot) # 返回仓库
                
                chromosome.total_distance += route_distance

                # 计算容量违规
                if route_demand > self.vehicle_capacity:
                    chromosome.capacity_violation += (route_demand - self.vehicle_capacity)

            # 3. 计算最终适应度
            chromosome.fitness = chromosome.total_distance + (chromosome.capacity_violation * CAPACITY_PENALTY)

    def initialize_population(self):
        """
        创建初始种群。
        每个个体的基因都是客户点的随机排列。
        """
        for _ in range(self.population_size):
            shuffled_customers = random.sample(self.customers, len(self.customers))
            self.population.append(Chromosome(shuffled_customers))

    def selection(self, tournament_size=5) -> List[Chromosome]:
        """
        使用锦标赛选择法选择父代。
        """
        selected = []
        for _ in range(self.population_size):
            # 随机选择k个个体进行锦标赛
            tournament = random.sample(self.population, tournament_size)
            # 选择锦标赛中适应度最高的个体
            winner = min(tournament, key=lambda c: c.fitness)
            selected.append(winner)
        return selected

    def crossover_and_mutate(self, parents: List[Chromosome]) -> List[Chromosome]:
        """对父代进行交叉和变异操作，产生子代。"""
        offspring = []
        for i in range(0, self.population_size, 2):
            p1 = parents[i]
            # 确保有p2
            if i + 1 < len(parents):
                p2 = parents[i+1]
            else:
                p2 = p1 # 如果父代数量为奇数，则最后一个与自身配对

            # 交叉
            if random.random() < self.crossover_rate:
                c1_genes, c2_genes = self.ordered_crossover(p1.genes, p2.genes)
            else:
                c1_genes, c2_genes = p1.genes[:], p2.genes[:]
            
            # 变异
            self.mutate(c1_genes)
            self.mutate(c2_genes)

            offspring.append(Chromosome(c1_genes))
            offspring.append(Chromosome(c2_genes))
        
        return offspring

    def ordered_crossover(self, parent1: List[Location], parent2: List[Location]) -> (List[Location], List[Location]):
        """有序交叉 (OX1)，适用于CVRP的染色体结构。"""
        size = len(parent1)
        child1, child2 = [None]*size, [None]*size
        
        # 随机选择交叉点
        start, end = sorted(random.sample(range(size), 2))
        
        # 复制交叉片段到子代
        child1[start:end] = parent1[start:end]
        child2[start:end] = parent2[start:end]
        
        # 填充剩余部分
        p1_genes = [gene for gene in parent2 if gene not in child1]
        p2_genes = [gene for gene in parent1 if gene not in child2]
        
        # 指针
        p1_idx, p2_idx = 0, 0
        for i in range(size):
            if child1[i] is None:
                child1[i] = p1_genes[p1_idx]
                p1_idx += 1
            if child2[i] is None:
                child2[i] = p2_genes[p2_idx]
                p2_idx += 1
        
        return child1, child2

    def mutate(self, genes: List[Location]):
        """交换变异：随机交换路径中的两个客户点。"""
        if random.random() < self.mutation_rate:
            if len(genes) >= 2:
                idx1, idx2 = random.sample(range(len(genes)), 2)
                genes[idx1], genes[idx2] = genes[idx2], genes[idx1]

# ==============================================================================
# 3. API 定义 (API Definitions)
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

def calculate_distance(loc1: Location, loc2: Location) -> float:
    """计算两个地点之间的欧几里得距离。"""
    return math.sqrt((loc1.x - loc2.x)**2 + (loc1.y - loc2.y)**2)

@app.post("/api/optimize", response_model=OptimizationResponse)
def optimize_route(
    request: OptimizationRequest,
    current_user: Annotated[schemas.User, Depends(auth.get_current_user)]
):
    """
    (Protected) 接收配送点和算法参数，返回优化后的路径。
    """
    ga = GeneticAlgorithm(
        locations=request.locations,
        population_size=request.population_size,
        mutation_rate=request.mutation_rate,
        crossover_rate=request.crossover_rate,
        generations=request.generations,
        patience=request.patience
    )
    
    best_chromosome = ga.run()
    
    return OptimizationResponse(
        path=[loc.id for loc in best_chromosome.genes],
        distance=best_chromosome.fitness
    )

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
    """
    db_customer = models.Customer(**customer.model_dump())
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
    """
    db_depot = models.Depot(**depot.model_dump())
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