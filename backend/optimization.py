import random
from typing import List
from pydantic import BaseModel
from . import ors_client

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
        self.geometries: List[str] = [] # 存储每条路径的ORS几何信息
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
        self.distance_matrix = {} # Store pre-computed distances

    def _precompute_distance_matrix(self):
        """
        Calls the ORS Matrix API to get all-to-all distances and stores them.
        """
        print("Pre-computing distance matrix...")
        all_locations = [self.depot] + self.customers
        
        # Add a safeguard to prevent API errors for large matrices
        if len(all_locations) > 50:
            raise Exception(f"Too many locations ({len(all_locations)}) for distance matrix calculation. Maximum is 50.")

        coords = [[loc.x, loc.y] for loc in all_locations]
        
        matrix_data = ors_client.get_distance_matrix(coords)
        
        if not matrix_data or 'distances' not in matrix_data:
            raise Exception("Failed to retrieve distance matrix from openrouteservice.")

        distances = matrix_data['distances']
        # Create a lookup dictionary for easy access
        for i, from_loc in enumerate(all_locations):
            for j, to_loc in enumerate(all_locations):
                distance = distances[i][j]
                # If a route is not found, ORS returns None. Treat it as infinite distance.
                self.distance_matrix[(from_loc.id, to_loc.id)] = float('inf') if distance is None else distance
        print("Distance matrix successfully computed.")

    def run(self):
        """执行遗传算法的主循环。"""
        print("遗传算法开始...")
        # 0. Pre-compute the distance matrix
        self._precompute_distance_matrix()

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
        best_chromosome = min(self.population, key=lambda c: c.fitness)

        # 6. 为最优解获取路径几何信息
        print("为最优解获取精确路径...")
        best_chromosome.geometries = []
        for route in best_chromosome.routes:
            coords = [[loc.x, loc.y] for loc in route]
            coords.append([self.depot.x, self.depot.y]) # 确保路径返回仓库
            if len(coords) > 1:
                ors_route_data = ors_client.get_route(coords)
                if ors_route_data and 'routes' in ors_route_data and ors_route_data['routes']:
                    best_chromosome.geometries.append(ors_route_data['routes'][0]['geometry'])
        
        return best_chromosome

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
                    chromosome.routes.append(current_route)
                    current_route = [self.depot, gene]
                    current_demand = gene_demand
                else:
                    current_route.append(gene)
                    current_demand += gene_demand
            
            if len(current_route) > 1:
                chromosome.routes.append(current_route)

            # 2. 使用预计算的距离矩阵计算总距离和惩罚
            for route in chromosome.routes:
                route_distance = 0
                route_demand = sum(loc.demand for loc in route)
                
                # 从距离矩阵中查找距离
                for i in range(len(route) - 1):
                    from_id = route[i].id
                    to_id = route[i+1].id
                    route_distance += self.distance_matrix.get((from_id, to_id), float('inf'))
                
                # 添加返回仓库的距离
                route_distance += self.distance_matrix.get((route[-1].id, self.depot.id), float('inf'))
                
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