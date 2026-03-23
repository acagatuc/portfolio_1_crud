from __future__ import annotations

import math
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, project_id: str, data: TaskCreate) -> Task:
        task = Task(
            project_id=project_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_tasks_for_project(
        self,
        project_id: str,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "asc",
    ) -> Tuple[List[Task], int]:
        query = self.db.query(Task).filter(Task.project_id == project_id)

        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)

        if sort_by == "due_date":
            sort_column = Task.due_date
        elif sort_by == "updated_at":
            sort_column = Task.updated_at
        else:
            sort_column = Task.created_at
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        total = query.count()
        tasks = query.offset((page - 1) * per_page).limit(per_page).all()
        return tasks, total

    def update_task(self, task: Task, data: TaskUpdate) -> Task:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task: Task) -> None:
        self.db.delete(task)
        self.db.commit()

    @staticmethod
    def calculate_total_pages(total: int, per_page: int) -> int:
        if per_page == 0:
            return 0
        return math.ceil(total / per_page) if total > 0 else 1
