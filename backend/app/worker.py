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
        
        # Prepare Data for Solver
        print(f"Preparing data for {len(orders)} orders and {len(vehicles)} vehicles...")
        
        # 1. Main Dispatch Depot (Node 0)
        depot_loc = Location(id=0, x=depot.x, y=depot.y, demand=0) 
        
        # 2. Customers (Nodes 1..N)
        # Map Order ID -> Location
        order_map = {o.id: o for o in orders}
        customer_locs = [Location(id=o.id, x=o.customer.x, y=o.customer.y, demand=o.demand) for o in orders]
        
        all_locations = [depot_loc] + customer_locs
        
        # 3. Vehicle Start Locations (Nodes N+1..M)
        # We need to identify unique start locations for vehicles (their current depots).
        # If current_depot == dispatch_depot, index is 0.
        # Else, we add new location node.
        
        # Helper to find existing location index or add new one
        # Using a coordinate-based key or depot ID key? ID is safer.
        # But Location.id logic in optimization usually ignored except for result mapping.
        # We use internal list index for solver.
        
        # Let's verify existing locations to avoid dupes?
        # Actually, simpler: Just maintain a map of DepotID -> List Index.
        depot_to_index = {depot.id: 0} # Dispatch depot is always index 0
        
        vehicle_data = []
        for v in vehicles:
            v_depot_id = v.current_depot_id if v.current_depot_id else depot.id
            
            if v_depot_id not in depot_to_index:
                # Need to load this depot info. 
                # Since we didn't query it yet, we might need to fetch or use relationship if eager loaded.
                # v.current_depot is relationship.
                if v.current_depot:
                    new_loc = Location(id=v_depot_id * -1, x=v.current_depot.x, y=v.current_depot.y, demand=0) # Negative ID for other depots to distinguish?
                    all_locations.append(new_loc)
                    depot_to_index[v_depot_id] = len(all_locations) - 1
                else:
                    # Fallback to Node 0 if data missing
                    depot_to_index[v_depot_id] = 0
            
            start_idx = depot_to_index[v_depot_id]
            vehicle_data.append({
                'id': v.id, 
                'capacity': v.capacity,
                'start_index': start_idx,
                'end_index': start_idx # Return to same base
            })

        self.update_state(state='PROGRESS', meta={'status': 'Running Optimization (OR-Tools)...'})
        print("Running Optimization...")
        
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