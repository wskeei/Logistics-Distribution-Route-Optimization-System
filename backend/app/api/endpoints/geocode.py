from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...schemas import all_schemas as schemas
from ...api import deps
from ...services import ors

router = APIRouter()

class AutocompleteSuggestion(BaseModel):
    label: str
    coordinates: List[float]

@router.get("/autocomplete", response_model=List[AutocompleteSuggestion])
def get_address_suggestions(
    text: str,
    current_user: schemas.User = Depends(deps.get_current_user)
):
    """
    (Protected) Get address autocomplete suggestions based on user input.
    """
    if not text or not text.strip():
        return []
    
    suggestions = ors.autocomplete(text)
    
    if suggestions is None:
        # The client function already prints the specific error, 
        # so we return a generic 503 Service Unavailable error to the client.
        raise HTTPException(status_code=503, detail="Address suggestion service is currently unavailable.")
        
    return suggestions


class AddressQuery(BaseModel):
    address: str
    region: Optional[str] = None

class CoordinatesResponse(BaseModel):
    x: float # longitude
    y: float # latitude

@router.post("/address", response_model=CoordinatesResponse)
def get_coordinates_for_address(
    query: AddressQuery,
    current_user: schemas.User = Depends(deps.get_current_user)
):
    """
    (Protected) Geocode a full address string to coordinates, with an optional region for focus.
    """
    if not query.address or not query.address.strip():
        raise HTTPException(status_code=400, detail="Address cannot be empty.")
    
    focus_point = None
    if query.region and query.region.strip():
        # Geocode the region first to get a focus point
        focus_point = ors.geocode(query.region)
        if not focus_point:
            print(f"Warning: Could not geocode region '{query.region}' to create a focus point.")

    # Now geocode the main address, using the focus point if available
    coords = ors.geocode(query.address, focus_point=focus_point)
    
    if not coords:
        raise HTTPException(status_code=404, detail=f"Could not geocode address: {query.address}")
        
    return CoordinatesResponse(x=coords[0], y=coords[1])
