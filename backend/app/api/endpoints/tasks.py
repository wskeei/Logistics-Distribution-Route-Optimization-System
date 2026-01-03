from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...db.session import get_db
from ...schemas import all_schemas as schemas
from ...models import sql_models as models
from ...api import deps
from ...services.optimization import VRPSolver, Location
from ...services import ors

router = APIRouter()

# --- Legacy Simple Optimization Endpoint ---
# Kept here or moved to separate file? Let's keep distinct routes here if related to tasks/optimization.
# Actually, the plan had 'optimization' as a separate thing maybe? But it fits in 'tasks' or just 'optimization'.
# Let's put the simple optimization endpoint here too or in a separate 'optimization.py' endpoint.
# Given it's stateless, maybe `optimization.py` endpoint is better.
# For now, I'll put the stateful task optimization here.

@router.post("/optimize_cvrp", response_model=schemas.Task)
def create_and_optimize_cvrp_task(
    task_create: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
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
    
    # We map Order -> Location. ID will be order.id
    customer_locations = [
        Location(id=order.id, x=order.customer.x, y=order.customer.y, demand=order.demand)
        for order in orders
    ]
    locations_for_optimization = [depot_location] + customer_locations

    # 5. 执行 OR-Tools 优化
    # Currently only supporting 1 vehicle in this specific endpoint logic?
    # The input `task_create` has `vehicle_id`.
    # But `VRPSolver` expects a list of vehicles.
    # We will provide just this one vehicle.
    vehicle_data = [{'id': vehicle.id, 'capacity': vehicle.capacity}]
    
    solver = VRPSolver(locations=locations_for_optimization, vehicles=vehicle_data)
    result = solver.solve()
    
    # Since we only passed 1 vehicle, we expect at most 1 route result if it fits?
    # Or multiple if it splits? OR-Tools with 1 vehicle might fail if demand > capacity.
    # But let's assume valid or best effort.
    
    if not result.routes:
         raise HTTPException(status_code=400, detail="Optimization failed to generate a route. Capacity might be exceeded.")

    # We take the first (and likely only) route
    route_res = result.routes[0]

    # 6. 创建主任务记录
    db_task = models.Task(
        depot_id=task_create.depot_id,
        vehicle_id=task_create.vehicle_id, # Main vehicle for the task
        status=models.TaskStatus.COMPLETED,
        total_distance=route_res.distance, # Use result distance
        path_geometries=[route_res.geometry] if route_res.geometry else []
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 7. 保存多条路径的站点顺序
    stop_counter = 1
    # route_res.route_path contains Locations.
    # Locations ID is order.id as per our preparation above.
    
    # Map order.id back to customer_id for TaskStop?
    # TaskStop needs customer_id.
    # We have orders loaded.
    order_map = {o.id: o for o in orders}
    
    for loc in route_res.route_path:
        if loc.id == depot.id: continue # Skip depot (id match check)
        
        order_obj = order_map.get(loc.id)
        if order_obj:
            task_stop = models.TaskStop(
                task_id=db_task.id,
                customer_id=order_obj.customer_id,
                stop_order=stop_counter
            )
            db.add(task_stop)
            stop_counter += 1
    
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    tasks = db.query(models.Task).offset(skip).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=schemas.Task)
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Cascade delete stops (SQLAlchemy relationship usually handles this, but manual check is good)
    db.query(models.TaskStop).filter(models.TaskStop.task_id == task_id).delete()
    
    db.delete(db_task)
    db.commit()
    return None

@router.put("/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task
