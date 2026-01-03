from celery.result import AsyncResult
from typing import Optional, Union, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...schemas import all_schemas as schemas
from ...api import deps

# Use absolute or proper relative imports for CELERY
# We import run_dispatch_task inside the function to avoid circular imports? 
# Actually if we structure it right, we can import validly. But stick to inside for safety if it was an issue.

router = APIRouter()

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Union[schemas.DispatchResult, str, dict, Any]] = None
    error: Optional[str] = None

@router.post("/run", status_code=202)
def run_dispatcher_async(
    dispatch_request: schemas.DispatchRequest,
    current_user: schemas.User = Depends(deps.get_current_user)
):
    """
    Asynchronously trigger the multi-vehicle dispatching task.
    """
    # Move the import inside the function to break the circular import
    from ...worker import run_dispatch_task
    task = run_dispatch_task.delay(dispatch_request.model_dump())
    return {"task_id": task.id}

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_dispatch_status(task_id: str):
    """
    Check the status of a dispatching task.
    """
    from ...core.celery_app import celery as celery_app
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.state == 'PENDING':
        return TaskStatusResponse(task_id=task_id, status='Pending')
    elif task_result.state == 'PROGRESS':
        return TaskStatusResponse(task_id=task_id, status='In Progress', result=task_result.info.get('status'))
    elif task_result.state == 'SUCCESS':
        # The return value of the task is in task_result.result
        # The task returns a dict like: {'status': 'COMPLETE', 'result': ...}
        task_return_value = task_result.result
        
        # Check if the task return value is a dict and has the expected keys
        if isinstance(task_return_value, dict):
            if 'error' in task_return_value:
                 return TaskStatusResponse(task_id=task_id, status='Failed', error=task_return_value['error'])
            
            # The 'result' key contains the DispatchResult data
            if 'result' in task_return_value:
                 return TaskStatusResponse(task_id=task_id, status='Success', result=schemas.DispatchResult.model_validate(task_return_value['result']))
        return TaskStatusResponse(task_id=task_id, status='Success', result=task_return_value)
    else:
        return TaskStatusResponse(task_id=task_id, status=task_result.state)
