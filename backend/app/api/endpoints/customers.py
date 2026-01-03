from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas import all_schemas as schemas
from ...models import sql_models as models
from ...api import deps
from ...services import ors

router = APIRouter()

@router.get("/", response_model=List[schemas.Customer])
def read_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    return customers

@router.post("/", response_model=schemas.Customer)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    customer_data = customer.model_dump()
    
    # Geocoding logic
    if customer_data.get('x') is None or customer_data.get('y') is None:
        if not customer_data.get('address'):
            raise HTTPException(status_code=400, detail="Either address or coordinates (x, y) must be provided.")
        
        coords = ors.geocode(customer_data['address'])
        if not coords:
            raise HTTPException(status_code=400, detail=f"Could not geocode address: {customer_data['address']}")
        
        customer_data['x'] = coords[0] # longitude
        customer_data['y'] = coords[1] # latitude

    db_customer = models.Customer(**customer_data)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.get("/{customer_id}", response_model=schemas.Customer)
def read_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.put("/{customer_id}", response_model=schemas.Customer)
def update_customer(
    customer_id: int,
    customer: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = customer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
    
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.delete("/{customer_id}", response_model=schemas.Customer)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(db_customer)
    db.commit()
    return db_customer
