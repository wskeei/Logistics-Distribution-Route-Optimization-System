from typing import List, Tuple, Dict
import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from pydantic import BaseModel
from . import ors as ors_client

# ==================================
# Data Structures
# ==================================

class Location(BaseModel):
    id: int
    x: float
    y: float
    demand: float = 0

class RouteResult(BaseModel):
    vehicle_id: int
    route_path: List[Location]
    distance: float
    load: float
    geometry: str = ""

class OptimizationResult(BaseModel):
    total_distance: float
    routes: List[RouteResult]

# ==================================
# OR-Tools VRP Solver
# ==================================

class VRPSolver:
    def __init__(self, locations: List[Location], vehicles: List[dict]):
        """
        :param locations: List[Location], index 0 is depot.
        :param vehicles: List[dict] [{'id': int, 'capacity': float}, ...]
        """
        self.locations = locations
        self.vehicles = vehicles
        self.depot = locations[0]
        self.num_vehicles = len(vehicles)
        
        # Scaling factor to convert float coordinates/demands to integers for OR-Tools
        self.dist_scale = 1000 # 1km = 1000 units
        self.demand_scale = 100 # 1.00 weight = 100 units

    def _create_data_model(self):
        data = {}
        
        # 1. Distance Matrix
        data['distance_matrix'] = self._compute_distance_matrix()
        
        # 2. Demands
        data['demands'] = [int(loc.demand * self.demand_scale) for loc in self.locations]
        
        # 3. Vehicle Capacities
        data['vehicle_capacities'] = [int(v['capacity'] * self.demand_scale) for v in self.vehicles]
        
        # 4. Vehicle Start/End (All start/end at depot 0)
        data['num_vehicles'] = self.num_vehicles
        data['depot'] = 0
        
        return data

    def _compute_distance_matrix(self) -> List[List[int]]:
        """
        Computes distance matrix in meters.
        Tries ORS first, falls back to Haversine.
        """
        print("Computing distance matrix...")
        coords = [[loc.x, loc.y] for loc in self.locations]
        
        # ORS Limit Check (typically 50x50 for free tier, but let's try or fallback)
        matrix = None
        if len(coords) <= 50:
            try:
                # data = ors_client.get_distance_matrix(coords)
                # if data and 'distances' in data:
                #     matrix = data['distances']
                #     # Replace None with large number
                #     matrix = [[int(d) if d is not None else 999999999 for d in row] for row in matrix]
                pass # Skip ORS for now to ensure speed and stability for large nationwide data
            except:
                pass

        if matrix is None:
            # Fallback Haversine
            matrix = []
            for i, loc1 in enumerate(self.locations):
                row = []
                for j, loc2 in enumerate(self.locations):
                    if i == j:
                        row.append(0)
                    else:
                        dist_km = self._haversine(loc1.y, loc1.x, loc2.y, loc2.x)
                        row.append(int(dist_km * 1000)) # meters
                matrix.append(row)
        return matrix

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in kilometers
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def solve(self) -> OptimizationResult:
        data = self._create_data_model()
        
        # Create Routing Index Manager
        manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                               data['num_vehicles'], data['depot'])

        # Create Routing Model
        routing = pywrapcp.RoutingModel(manager)

        # 1. Register Transit Callback (Distance)
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # 2. Add Capacity Constraint
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )

        # Setting Search Parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.seconds = 10 # Limit solver time

        # Solve
        print("Running OR-Tools Solver...")
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            return self._format_solution(data, manager, routing, solution)
        else:
            print("No solution found!")
            return OptimizationResult(total_distance=0, routes=[])

    def _format_solution(self, data, manager, routing, solution) -> OptimizationResult:
        print("Solution found! Formatting results...")
        total_distance = 0
        routes = []

        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_load = 0
            route_nodes = []
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route_load += data['demands'][node_index]
                route_nodes.append(self.locations[node_index])
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)

            # Add end node (depot) only if route has customers
            if len(route_nodes) > 1: # >1 means Depot + at least 1 customer
                 # Append depot at end for closed loop
                 # node_index = manager.IndexToNode(index) # This is end node
                 # route_nodes.append(self.locations[node_index]) # Often same as depot
                 
                 # Let's clean up logic:
                 # route_nodes currently: [Depot, C1, C2...]
                 # We need to explicitly add Depot at the end? 
                 # OR-Tools "End" node is virtual.
                 # Let's just append the depot object manually to close the loop.
                 route_nodes.append(self.depot)

                 dist_km = route_distance / 1000.0 # Convert back to meters or km? The matrix was meters.
                 # Actually matrix was from _haversine * 1000 so it is Meters.
                 # Let's keep it as meters.
                 
                 # Fetch Geometry from ORS only for this final route
                 geometry = self._fetch_route_geometry(route_nodes)
                 
                 routes.append(RouteResult(
                     vehicle_id=self.vehicles[vehicle_id]['id'],
                     route_path=route_nodes,
                     distance=dist_km,
                     load=route_load / self.demand_scale,
                     geometry=geometry
                 ))
                 total_distance += dist_km

        return OptimizationResult(total_distance=total_distance, routes=routes)

    def _fetch_route_geometry(self, route_nodes: List[Location]) -> str:
        coords = [[loc.x, loc.y] for loc in route_nodes]
        try:
             # Only query if reasonable number of points
            if len(coords) < 100:
                data = ors_client.get_route(coords)
                if data and 'routes' in data and len(data['routes']) > 0:
                    return data['routes'][0]['geometry']
        except Exception as e:
            print(f"Error fetching geometry: {e}")
        return ""