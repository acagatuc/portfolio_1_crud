from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, user_id: str, data: ProjectCreate) -> Project:
        project = Project(
            user_id=user_id,
            name=data.name,
            description=data.description,
            status=data.status,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_projects_for_user(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[Project], int]:
        query = self.db.query(Project).filter(Project.user_id == user_id)
        if status:
            query = query.filter(Project.status == status)
        total = query.count()
        projects = query.offset((page - 1) * per_page).limit(per_page).all()
        return projects, total

    def update_project(self, project: Project, data: ProjectUpdate) -> Project:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()

    def get_task_counts(self, project_id: str) -> Dict[str, int]:
        rows = (
            self.db.query(Task.status, func.count(Task.id).label("count"))
            .filter(Task.project_id == project_id)
            .group_by(Task.status)
            .all()
        )
        counts: Dict[str, int] = {"todo": 0, "in_progress": 0, "done": 0}
        for row in rows:
            counts[row.status] = row.count
        return counts

    def get_task_counts_bulk(self, project_ids: List[str]) -> Dict[str, Dict[str, int]]:
        """Load task counts for multiple projects in a single query to avoid N+1."""
        if not project_ids:
            return {}
        rows = (
            self.db.query(Task.project_id, Task.status, func.count(Task.id).label("count"))
            .filter(Task.project_id.in_(project_ids))
            .group_by(Task.project_id, Task.status)
            .all()
        )
        empty = {"todo": 0, "in_progress": 0, "done": 0}
        result: Dict[str, Dict[str, int]] = {pid: dict(empty) for pid in project_ids}
        for row in rows:
            result[row.project_id][row.status] = row.count
        return result

    @staticmethod
    def calculate_total_pages(total: int, per_page: int) -> int:
        if per_page == 0:
            return 0
        return math.ceil(total / per_page) if total > 0 else 1
