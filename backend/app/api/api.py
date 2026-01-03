from fastapi import APIRouter

from .endpoints import (
    auth,
    users,
    customers,
    depots,
    vehicles,
    products,
    orders,
    tasks,
    dispatch,
    geocode,
    optimization
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/api", tags=["auth"]) # /api/token
api_router.include_router(users.router, prefix="/api/users", tags=["users"])
api_router.include_router(customers.router, prefix="/api/customers", tags=["customers"])
api_router.include_router(depots.router, prefix="/api/depots", tags=["depots"])
api_router.include_router(vehicles.router, prefix="/api/vehicles", tags=["vehicles"])
api_router.include_router(products.router, prefix="/api/products", tags=["products"])
api_router.include_router(orders.router, prefix="/api/orders", tags=["orders"])
api_router.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
api_router.include_router(dispatch.router, prefix="/api/dispatch", tags=["dispatch"])
api_router.include_router(geocode.router, prefix="/api/geocode", tags=["geocode"])
api_router.include_router(optimization.router, prefix="/api", tags=["optimization"]) # /api/optimize
