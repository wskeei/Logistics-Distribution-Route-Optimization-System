import random
from typing import List, Annotated
import math
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

import auth, database, models, schemas

models.Base.metadata.create_all(bind=database.engine)

# ==============================================================================
# 1. 数据结构定义 (Data Structures)
# ==============================================================================

class Location(BaseModel):
    """
    代表一个地理位置点，可以是仓库或客户。
    使用Pydantic BaseModel以用于API请求/响应。
    """
    id: int
    x: float
    y: float

class Chromosome:
    """
    代表一个个体（一条配送路径）。
    基因 (genes) 是一个地点的列表，顺序代表配送顺序。
    适应度 (fitness) 代表路径的总成本（例如总距离），值越小越好。
    """
    def __init__(self, genes: List[Location]):
        self.genes = genes
        self.fitness = float('inf') # 初始适应度设为无穷大

    def __repr__(self):
        return f"Chromosome(Path: {' -> '.join(str(g.id) for g in self.genes)}, Fitness: {self.fitness:.2f})"

# ==============================================================================
# 2. 遗传算法核心类 (Genetic Algorithm Core)
# ==============================================================================

class GeneticAlgorithm:
    """
    封装遗传算法的主要流程。
    """
    def __init__(self, locations: List[Location], population_size: int, mutation_rate: float, crossover_rate: float, generations: int, patience: int = 20):
        """
        初始化遗传算法参数。
        :param locations: 所有需要访问的地点列表（包括起点）。
        :param population_size: 种群大小。
        :param mutation_rate: 变异率。
        :param crossover_rate: 交叉率。
        :param generations: 最大迭代代数。
        :param patience: 连续多少代最优解未改善则提前停止。
        """
        self.locations = locations
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
        """
        for chromosome in self.population:
            total_distance = 0.0
            path = chromosome.genes
            for i in range(len(path) - 1):
                total_distance += calculate_distance(path[i], path[i+1])
            total_distance += calculate_distance(path[-1], path[0])
            chromosome.fitness = total_distance

    def initialize_population(self):
        """
        创建初始种群。
        对于每个个体，路径的起点固定，其他客户点随机排列。
        """
        start_node = self.locations[0]
        other_nodes = self.locations[1:]
        
        for _ in range(self.population_size):
            shuffled_nodes = random.sample(other_nodes, len(other_nodes))
            genes = [start_node] + shuffled_nodes
            self.population.append(Chromosome(genes))

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
        """有序交叉 (OX1)，适用于旅行商问题。"""
        size = len(parent1)
        child1, child2 = [None]*size, [None]*size
        
        # 随机选择交叉点
        start, end = sorted(random.sample(range(1, size), 2)) # 不交叉起点
        
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
        """交换变异：随机交换路径中的两个城市（不包括起点）。"""
        if random.random() < self.mutation_rate:
            idx1, idx2 = random.sample(range(1, len(genes)), 2)
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

# --- Task Creation & Optimization Endpoint ---

@app.post("/api/tasks/optimize", response_model=schemas.Task)
def create_and_optimize_task(
    task_create: schemas.TaskCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """
    创建一个新任务，从数据库读取仓库和客户信息，执行路径优化，并将结果保存为任务。
    """
    # 1. 验证仓库是否存在
    depot = db.query(models.Depot).filter(models.Depot.id == task_create.depot_id).first()
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")

    # 2. 验证客户是否存在
    customers = db.query(models.Customer).filter(models.Customer.id.in_(task_create.customer_ids)).all()
    if len(customers) != len(task_create.customer_ids):
        raise HTTPException(status_code=404, detail="One or more customers not found")
    
    if not customers:
        raise HTTPException(status_code=400, detail="At least one customer is required for optimization")

    # 3. 创建任务记录
    db_task = models.Task(
        depot_id=task_create.depot_id,
        vehicle_id=task_create.vehicle_id,
        status=models.TaskStatus.PENDING
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task) # Need ID for TaskStop creation

    # 4. 准备用于优化的地点列表
    locations_for_optimization = [
        Location(id=depot.id, x=depot.x, y=depot.y)
    ]
    for customer in customers:
        locations_for_optimization.append(Location(id=customer.id, x=customer.x, y=customer.y))

    # 5. 执行遗传算法优化
    ga = GeneticAlgorithm(
        locations=locations_for_optimization,
        population_size=50, # Default values for now
        mutation_rate=0.01,
        crossover_rate=0.85,
        generations=500,
        patience=50
    )
    best_chromosome = ga.run()

    # 6. 保存优化结果到任务
    db_task.total_distance = best_chromosome.fitness
    db_task.status = models.TaskStatus.COMPLETED

    # 7. 保存路径中的站点顺序
    for order, loc in enumerate(best_chromosome.genes[1:], start=1): # Skip depot (first element)
        task_stop = models.TaskStop(
            task_id=db_task.id,
            customer_id=loc.id,
            stop_order=order
        )
        db.add(task_stop)
    
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