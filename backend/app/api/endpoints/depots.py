from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas import all_schemas as schemas
from ...models import sql_models as models
from ...api import deps
from ...services import ors

router = APIRouter()

@router.get("/", response_model=List[schemas.Depot])
def read_depots(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    depots = db.query(models.Depot).offset(skip).limit(limit).all()
    return depots

@router.post("/", response_model=schemas.Depot)
def create_depot(
    depot: schemas.DepotCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    depot_data = depot.model_dump()

    # Geocoding logic
    if depot_data.get('x') is None or depot_data.get('y') is None:
        if not depot_data.get('address'):
            raise HTTPException(status_code=400, detail="Either address or coordinates (x, y) must be provided.")
        
        coords = ors.geocode(depot_data['address'])
        if not coords:
            raise HTTPException(status_code=400, detail=f"Could not geocode address: {depot_data['address']}")
        
        depot_data['x'] = coords[0] # longitude
        depot_data['y'] = coords[1] # latitude

    db_depot = models.Depot(**depot_data)
    db.add(db_depot)
    db.commit()
    db.refresh(db_depot)
    return db_depot

@router.get("/{depot_id}", response_model=schemas.Depot)
def read_depot(
    depot_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_depot = db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    if db_depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    return db_depot

@router.put("/{depot_id}", response_model=schemas.Depot)
def update_depot(
    depot_id: int,
    depot: schemas.DepotUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_depot = db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    if db_depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    
    update_data = depot.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_depot, key, value)
    
    db.commit()
    db.refresh(db_depot)
    return db_depot

@router.delete("/{depot_id}", response_model=schemas.Depot)
def delete_depot(
    depot_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_depot = db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    if db_depot is None:
        raise HTTPException(status_code=404, detail="Depot not found")
    
    db.delete(db_depot)
    db.commit()
    return db_depot
