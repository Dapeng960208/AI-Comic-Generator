from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.database import get_session
from app.models.models import Task
from app.schemas.schemas import TaskRead

router = APIRouter()

@router.get("/{task_id}", response_model=TaskRead)
def get_task_status(task_id: str, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/project/{project_id}", response_model=list[TaskRead])
def get_project_tasks(project_id: str, session: Session = Depends(get_session)):
    from sqlmodel import select
    statement = select(Task).where(Task.project_id == project_id).order_by(Task.created_at.desc())
    tasks = session.exec(statement).all()
    # Filter only recent or active tasks if list is too long?
    # For now return all, maybe limit 20
    return tasks[:20]

@router.post("/{task_id}/cancel", response_model=TaskRead)
def cancel_task(task_id: str, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in ["completed", "failed", "cancelled"]:
        return task
        
    task.status = "cancelled"
    task.message = "Task cancelled by user"
    session.add(task)
    session.commit()
    session.refresh(task)
    return task