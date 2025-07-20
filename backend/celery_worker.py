from celery import Celery

# Configure Celery
celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)

# Import necessary components
from .database import SessionLocal
from . import models, schemas
from .main import GeneticAlgorithm, Location # We can reuse the GA class
from sklearn.cluster import KMeans
import numpy as np

@celery.task(bind=True)
def run_dispatch_task(self, dispatch_request_data: dict):
    """
    Celery task to run the multi-vehicle dispatching logic.
    """
    db = SessionLocal()
    try:
        dispatch_request = schemas.DispatchRequest.model_validate(dispatch_request_data)
        
        self.update_state(state='PROGRESS', meta={'status': 'Fetching data...'})
        vehicles = db.query(models.Vehicle).filter(models.Vehicle.id.in_(dispatch_request.vehicle_ids)).order_by(models.Vehicle.capacity.desc()).all()
        orders = db.query(models.Order).filter(models.Order.id.in_(dispatch_request.order_ids)).all()
        depot = db.query(models.Depot).filter(models.Depot.id == dispatch_request.depot_id).first()

        if not vehicles or not orders or not depot:
            raise Exception("Invalid data: Vehicles, orders, or depot not found.")

        self.update_state(state='PROGRESS', meta={'status': 'Clustering orders...'})
        customer_coords = np.array([[order.customer.x, order.customer.y] for order in orders])
        num_clusters = min(len(vehicles), len(orders))
        if num_clusters == 0:
            return {'status': 'COMPLETE', 'result': {'total_tasks_created': 0, 'tasks': []}}

        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(customer_coords)
        
        order_clusters = [[] for _ in range(num_clusters)]
        for i, order in enumerate(orders):
            order_clusters[clusters[i]].append(order)

        self.update_state(state='PROGRESS', meta={'status': 'Assigning clusters and optimizing routes...'})
        created_tasks_ids = []
        
        for i, vehicle in enumerate(vehicles):
            if not any(order_clusters): break # No more orders to assign
            
            order_clusters.sort(key=lambda c: sum(o.demand for o in c), reverse=True)
            
            best_cluster_idx = -1
            for j, cluster in enumerate(order_clusters):
                if not cluster: continue
                if sum(o.demand for o in cluster) <= vehicle.capacity:
                    best_cluster_idx = j
                    break
            
            if best_cluster_idx != -1:
                assigned_cluster = order_clusters.pop(best_cluster_idx)
                
                depot_loc = Location(id=depot.id, x=depot.x, y=depot.y, demand=0)
                customer_locs = [Location(id=o.customer.id, x=o.customer.x, y=o.customer.y, demand=o.demand) for o in assigned_cluster]
                locations = [depot_loc] + customer_locs

                ga = GeneticAlgorithm(
                    locations=locations, vehicle_capacity=vehicle.capacity,
                    population_size=50, mutation_rate=0.01, crossover_rate=0.9, generations=200, patience=20
                )
                best_chromosome = ga.run()

                db_task = models.Task(
                    depot_id=depot.id, vehicle_id=vehicle.id,
                    status=models.TaskStatus.ASSIGNED, total_distance=best_chromosome.total_distance
                )
                db.add(db_task)
                db.commit()
                db.refresh(db_task)

                stop_counter = 1
                for route in best_chromosome.routes:
                    for loc in route:
                        if loc.id == depot.id: continue
                        db.add(models.TaskStop(task_id=db_task.id, customer_id=loc.id, stop_order=stop_counter))
                        stop_counter += 1
                
                db.commit()
                created_tasks_ids.append(db_task.id)
        
        final_tasks = db.query(models.Task).filter(models.Task.id.in_(created_tasks_ids)).all()
        return {'status': 'COMPLETE', 'result': schemas.DispatchResult(total_tasks_created=len(final_tasks), tasks=final_tasks).model_dump()}
    
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        return {'status': 'FAILURE', 'error': str(e)}
    finally:
        db.close()

# To run the worker, use the following command in the terminal:
# celery -A backend.celery_worker worker --loglevel=info