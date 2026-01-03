from .core.celery_app import celery
from .db.session import SessionLocal
from .models import sql_models as models
from .schemas import all_schemas as schemas
# Heavy imports will be moved inside the task function for lazy loading.

@celery.task(bind=True)
def run_dispatch_task(self, dispatch_request_data: dict):
    """
    Celery task to run the multi-vehicle dispatching logic.
    """
    # --- Lazy Loading ---
    # Import heavy libraries here
    print("Task received. Importing heavy libraries...")
    from .services.optimization import VRPSolver, Location
    # from sklearn.cluster import KMeans # No longer needed
    # import numpy as np
    print("Libraries imported.")

    db = SessionLocal()
    try:
        dispatch_request = schemas.DispatchRequest.model_validate(dispatch_request_data)
        
        self.update_state(state='PROGRESS', meta={'status': 'Fetching data...'})
        print("Fetching data from DB...")
        vehicles = db.query(models.Vehicle).filter(models.Vehicle.id.in_(dispatch_request.vehicle_ids)).all()
        orders = db.query(models.Order).filter(models.Order.id.in_(dispatch_request.order_ids)).all()
        depot = db.query(models.Depot).filter(models.Depot.id == dispatch_request.depot_id).first()

        if not vehicles or not orders or not depot:
            raise Exception("Invalid data: Vehicles, orders, or depot not found.")

        # Prepare Data for Solver
        print(f"Preparing data for {len(orders)} orders and {len(vehicles)} vehicles...")
        
        depot_loc = Location(id=depot.id, x=depot.x, y=depot.y, demand=0)
        customer_locs = [Location(id=o.customer.id, x=o.customer.x, y=o.customer.y, demand=o.demand) for o in orders]
        all_locations = [depot_loc] + customer_locs
        
        vehicle_data = [{'id': v.id, 'capacity': v.capacity} for v in vehicles]

        self.update_state(state='PROGRESS', meta={'status': 'Running Optimization (OR-Tools)...'})
        print("Running Optimization...")
        
        solver = VRPSolver(locations=all_locations, vehicles=vehicle_data)
        result = solver.solve()
        
        print(f"Optimization complete. Total Distance: {result.total_distance}")

        # Save Results
        self.update_state(state='PROGRESS', meta={'status': 'Saving tasks...'})
        created_tasks_ids = []
        
        # Determine actual order objects map for quick lookup
        # Map location_id -> Order object (Note: location_id was customer_id)
        # We need to link back Location ID to Order ID.
        # Issue: Multiple orders might have same customer? 
        # In current seed, 1 order per customer usually. 
        # let's map customer_id -> list of orders? 
        # Actually logic: Location(id=customer.id). 
        # So we map customer_id -> order.
        
        # What if multiple orders for same customer? 
        # The input was `orders`.
        # `customer_locs` used `o.customer.id`.
        # If multiple orders share a customer, we passed duplicate locations with same ID?
        # OR-Tools handles duplicate nodes fine? No, usually IDs must be unique or handled carefully.
        # But `optimization.py` uses list index. `Location.id` is just meta.
        # So it works.
        
        # Mapping back:
        # We have `route_path` containing Locations.
        # We need to know which Order corresponds to that Location.
        # Since we flattened orders into `customer_locs` by order index, 
        # we generally need a way to track which order it was.
        # But `Location` struct has `id`.
        # If we use `o.id` instead of `o.customer.id` for Location ID, it's safer.
        # Let's fix that in the prep code below.
        
        # Map Order ID to Order Object for easy lookup
        # We use order.id as Location.id to prevent confusion (since multiple orders can be at same customer/location)
        # NOTE: Location.id in optimization.py is just an integer ID. 
        # We will use order.id for locations representing orders.
        order_map = {o.id: o for o in orders}
        
        # Redefine locations with order.id
        depot_loc = Location(id=0, x=depot.x, y=depot.y, demand=0) # ID 0 for depot
        customer_locs = [Location(id=o.id, x=o.customer.x, y=o.customer.y, demand=o.demand) for o in orders]
        all_locations = [depot_loc] + customer_locs

        # Re-initialize solver with correct IDs
        solver = VRPSolver(locations=all_locations, vehicles=vehicle_data)
        result = solver.solve()

        print(f"Optimization complete. Total Distance: {result.total_distance}")

        # Save Results
        self.update_state(state='PROGRESS', meta={'status': 'Saving tasks...'})
        created_tasks_ids = []

        for route_res in result.routes:
            # Create Task for this vehicle/route
            db_task = models.Task(
                depot_id=depot.id, 
                vehicle_id=route_res.vehicle_id,
                status=models.TaskStatus.ASSIGNED,
                total_distance=route_res.distance,
                path_geometries=[route_res.geometry] if route_res.geometry else [],
                title=dispatch_request.title,
                description=dispatch_request.description
            )
            db.add(db_task)
            db.commit()
            db.refresh(db_task)

            stop_counter = 1
            for loc in route_res.route_path:
                if loc.id == 0: continue # Skip depot in stops list
                
                # loc.id is order.id
                order_obj = order_map.get(loc.id)
                if order_obj:
                     # We need to link stop to a customer.
                     # TaskStop model uses customer_id?
                     # Let's check models.TaskStop from previous knowledge or assume customer_id
                     # Yes, `customer_id=loc.id` in old code, but that was customer id.
                     # Here loc.id is order.id.
                     # So we use order_obj.customer_id
                     db.add(models.TaskStop(
                         task_id=db_task.id, 
                         customer_id=order_obj.customer_id, 
                         stop_order=stop_counter
                     ))
                     
                     # Update order status?
                     order_obj.status = models.OrderStatus.ASSIGNED
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
# celery -A backend.celery_app worker --loglevel=info