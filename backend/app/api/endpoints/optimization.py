from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas import all_schemas as schemas
from ...api import deps
from ...services.optimization import solve_vrp, Location
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

    # Convert simple locations to the format required by the Genetic Algorithm
    # We assume a default demand of 0 for this simple endpoint.
    locations_for_ga = [
        Location(id=loc.id, x=loc.x, y=loc.y, demand=0)
        for loc in request.locations
    ]

    if not locations_for_ga:
        raise HTTPException(status_code=400, detail="No locations provided for optimization.")

    best_chromosome = solve_vrp(
        locations=locations_for_ga,
        vehicle_capacity=request.vehicle_capacity,
        num_vehicles=request.num_vehicles,
        population_size=request.population_size,
        mutation_rate=request.mutation_rate,
        crossover_rate=request.crossover_rate,
        generations=request.generations,
        patience=request.patience,
        algorithm_mode=request.algorithm_mode
    )

    # Check if a valid route was found
    if best_chromosome.total_distance == float('inf'):
        raise HTTPException(
            status_code=400,
            detail="Optimization failed: Could not find a valid path connecting all locations. Please check if all points are reachable on the road network."
        )
    
    # Extract routes with location IDs
    routes_with_ids = []
    for route in best_chromosome.routes:
        routes_with_ids.append([loc.id for loc in route])

    return schemas.OptimizationResponse(
        total_distance=best_chromosome.total_distance,
        routes=routes_with_ids,
        path_geometries=best_chromosome.geometries
    )
