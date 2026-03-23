from __future__ import annotations

from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def _build_project_response(project, task_counts: dict) -> ProjectResponse:
    data = ProjectResponse.model_validate(project)
    data.task_counts = task_counts
    return data


@router.post("", response_model=DataResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    project = service.create_project(user_id=current_user.id, data=data)
    task_counts = service.get_task_counts(project.id)
    response.headers["Location"] = f"/projects/{project.id}"
    return DataResponse(
        data=_build_project_response(project, task_counts),
        message="Project created successfully",
    )


@router.get("", response_model=PaginatedResponse[ProjectResponse])
def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[Literal["active", "archived"]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    projects, total = service.get_projects_for_user(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        status=status,
    )
    total_pages = ProjectService.calculate_total_pages(total, per_page)
    project_ids = [p.id for p in projects]
    task_counts_bulk = service.get_task_counts_bulk(project_ids)
    items = [_build_project_response(p, task_counts_bulk[p.id]) for p in projects]
    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(total=total, page=page, per_page=per_page, total_pages=total_pages),
        message="success",
    )


@router.get("/{project_id}", response_model=DataResponse[ProjectResponse])
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    project = service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    task_counts = service.get_task_counts(project.id)
    return DataResponse(
        data=_build_project_response(project, task_counts),
        message="success",
    )


@router.patch("/{project_id}", response_model=DataResponse[ProjectResponse])
def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    project = service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    updated = service.update_project(project, data)
    task_counts = service.get_task_counts(updated.id)
    return DataResponse(
        data=_build_project_response(updated, task_counts),
        message="Project updated successfully",
    )


@router.delete("/{project_id}", response_model=DataResponse[dict])
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    project = service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    service.delete_project(project)
    return DataResponse(data={"id": project_id}, message="Project deleted successfully")
