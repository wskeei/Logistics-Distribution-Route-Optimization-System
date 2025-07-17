import random
from typing import List, Annotated
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

# 运行服务器的命令 (在终端中):
# uvicorn backend.main:app --reload