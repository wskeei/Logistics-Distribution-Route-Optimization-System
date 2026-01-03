from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core import security
from ...db.session import get_db
from ...schemas import all_schemas as schemas
from ...models import sql_models as models
from ...api import deps

router = APIRouter()

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print(f"--- Received registration request for username: {user.username} ---", flush=True)
    try:
        db_user = deps.get_user(db, username=user.username)
        print(f"Checking existing user... Found: {db_user}", flush=True)
        if db_user:
            print("User already exists. Raising HTTPException.", flush=True)
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_password = security.get_password_hash(user.password)
        print("Password hashed successfully.", flush=True)
        
        db_user = models.User(username=user.username, hashed_password=hashed_password)
        print("User model created.", flush=True)
        
        db.add(db_user)
        print("User added to session.", flush=True)
        
        db.commit()
        print("DB commit successful.", flush=True)
        
        db.refresh(db_user)
        print("DB refresh successful.", flush=True)
        
        print(f"--- Successfully registered user: {db_user.username} ---", flush=True)
        return db_user
    except Exception as e:
        print(f"!!! AN UNEXPECTED ERROR OCCURRED: {e} !!!", flush=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error during registration.")

@router.get("/me/", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(deps.get_current_user)]
):
    return current_user
