from __future__ import annotations

from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

router = APIRouter(tags=["tasks"])


def _get_project_or_raise(project_id: str, user_id: str, db: Session):
    project_service = ProjectService(db)
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return project


@router.post(
    "/projects/{project_id}/tasks",
    response_model=DataResponse[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: str,
    data: TaskCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project_or_raise(project_id, current_user.id, db)
    service = TaskService(db)
    task = service.create_task(project_id=project_id, data=data)
    response.headers["Location"] = f"/projects/{project_id}/tasks/{task.id}"
    return DataResponse(
        data=TaskResponse.model_validate(task),
        message="Task created successfully",
    )


@router.get(
    "/projects/{project_id}/tasks",
    response_model=PaginatedResponse[TaskResponse],
)
def list_tasks(
    project_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[Literal["todo", "in_progress", "done"]] = Query(None),
    priority: Optional[Literal["low", "medium", "high"]] = Query(None),
    sort_by: Literal["due_date", "created_at", "updated_at"] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("asc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project_or_raise(project_id, current_user.id, db)
    service = TaskService(db)
    tasks, total = service.get_tasks_for_project(
        project_id=project_id,
        page=page,
        per_page=per_page,
        status=status,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = TaskService.calculate_total_pages(total, per_page)
    return PaginatedResponse(
        data=[TaskResponse.model_validate(t) for t in tasks],
        meta=PaginationMeta(total=total, page=page, per_page=per_page, total_pages=total_pages),
        message="success",
    )


@router.get("/tasks/{task_id}", response_model=DataResponse[TaskResponse])
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service = TaskService(db)
    task = task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _get_project_or_raise(task.project_id, current_user.id, db)
    return DataResponse(data=TaskResponse.model_validate(task), message="success")


@router.patch("/tasks/{task_id}", response_model=DataResponse[TaskResponse])
def update_task(
    task_id: str,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service = TaskService(db)
    task = task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _get_project_or_raise(task.project_id, current_user.id, db)
    updated = task_service.update_task(task, data)
    return DataResponse(
        data=TaskResponse.model_validate(updated),
        message="Task updated successfully",
    )


@router.delete("/tasks/{task_id}", response_model=DataResponse[dict])
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service = TaskService(db)
    task = task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _get_project_or_raise(task.project_id, current_user.id, db)
    task_service.delete_task(task)
    return DataResponse(data={"id": task_id}, message="Task deleted successfully")
