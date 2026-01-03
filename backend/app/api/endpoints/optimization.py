from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas import all_schemas as schemas
from ...api import deps
from ...services.optimization import VRPSolver, Location
from ...services import ors

router = APIRouter()

@router.post("/optimize", response_model=schemas.OptimizationResponse)
def optimize_simple_route(
    request: schemas.OptimizationRequest,
    current_user: Annotated[schemas.User, Depends(deps.get_current_user)]
):
    """
    (Protected) Receives a simple list of locations and returns an optimized route
    using the new openrouteservice-powered Genetic Algorithm.
    This endpoint is for simple, stateless optimization tests.
    """
    # Process locations: geocode if necessary
    for loc in request.locations:
        if loc.x is None or loc.y is None:
            if not loc.address:
                raise HTTPException(status_code=400, detail=f"Location with id {loc.id} must have either coordinates or an address.")
            coords = ors.geocode(loc.address)
            if not coords:
                raise HTTPException(status_code=400, detail=f"Could not geocode address for location id {loc.id}: {loc.address}")
            loc.x, loc.y = coords

    # Convert simple locations to the format required by the Solver
    # We assume a default demand of 0 for this simple endpoint, or 1 if capacity checks needed?
    # For basic TSP/VRP without strict demand payload, demand=0 is fine if capacity is huge.
    # But VRPSolver handles capacity. If demand is 0, capacity doesn't matter.
    locations_for_solver = [
        Location(id=loc.id, x=loc.x, y=loc.y, demand=0)
        for loc in request.locations
    ]

    if not locations_for_solver:
        raise HTTPException(status_code=400, detail="No locations provided for optimization.")

    vehicle_data = [{'id': i, 'capacity': request.vehicle_capacity} for i in range(request.num_vehicles)]

    solver = VRPSolver(locations=locations_for_solver, vehicles=vehicle_data)
    result = solver.solve()

    # Check if a valid route was found
    if result.total_distance == 0 and not result.routes:
        # Note: OptimizationResult returns 0 distance if no solution or trivial solution.
        # But assuming non-trivial input, it implies failure if empty.
         raise HTTPException(
            status_code=400,
            detail="Optimization found no valid routes."
        )
    
    # Extract routes with location IDs and flatten geometries
    routes_with_ids = []
    path_geometries = []
    
    for route in result.routes:
        routes_with_ids.append([loc.id for loc in route.route_path])
        if route.geometry:
            path_geometries.append(route.geometry)

    return schemas.OptimizationResponse(
        total_distance=result.total_distance,
        routes=routes_with_ids,
        path_geometries=path_geometries
    )
