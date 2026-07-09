"""FastAPI route handlers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from lifeos.api.deps import get_session
from lifeos.models.area import Area, AreaCreate, AreaUpdate
from lifeos.models.calibration import CalibrationFactor
from lifeos.models.goal import Goal, GoalCreate, GoalUpdate
from lifeos.models.project import Project, ProjectCreate, ProjectUpdate
from lifeos.models.task import Task, TaskCreate, TaskUpdate
from lifeos.repositories import (
    AreaRepository,
    CalibrationRepository,
    GoalRepository,
    ProjectRepository,
    TaskRepository,
)
from lifeos.schemas.api import BriefBody, CompletionResponse, ReviewBody, TaskDoneBody
from lifeos.services import (
    check_rest,
    complete_task,
    plan_and_persist,
    recommend_now,
    sync_vault_from_settings,
    write_daily_brief,
    write_weekly_review,
)
from lifeos.services.energy import apply_satisfaction_weight_nudge
from lifeos.services.overload import check_overload
from lifeos.services.review import week_start_for

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ------------------------------------------------------------------ engine ---
@router.get("/now")
def api_now(
    limit: int = Query(5, ge=1, le=50),
    session: Session = Depends(get_session),
):
    return recommend_now(session)


@router.get("/plan")
def api_plan(session: Session = Depends(get_session)):
    return plan_and_persist(session)


@router.get("/rest")
def api_rest(
    hours: float = Query(2.0, ge=0.5),
    session: Session = Depends(get_session),
):
    return check_rest(session, hours=hours)


@router.get("/overload")
def api_overload(session: Session = Depends(get_session)):
    return check_overload(session)


@router.get("/calibrate")
def api_calibrate(session: Session = Depends(get_session)) -> list[CalibrationFactor]:
    return CalibrationRepository(session).list_all(limit=100)


# ------------------------------------------------------------------ tasks ---
@router.get("/tasks")
def list_tasks(
    status: str | None = None,
    project: int | None = None,
    session: Session = Depends(get_session),
) -> list[Task]:
    filters: dict = {}
    if status is not None:
        filters["status"] = status
    if project is not None:
        filters["project_id"] = project
    return TaskRepository(session).list(limit=500, **filters)


@router.get("/tasks/{task_id}")
def get_task(task_id: int, session: Session = Depends(get_session)) -> Task:
    task = TaskRepository(session).get(task_id)
    if task is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return task


@router.post("/tasks", status_code=201)
def create_task(body: TaskCreate, session: Session = Depends(get_session)) -> Task:
    return TaskRepository(session).create(Task.model_validate(body))


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    body: TaskUpdate,
    session: Session = Depends(get_session),
) -> Task:
    task = TaskRepository(session).update(task_id, body)
    if task is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)) -> None:
    if not TaskRepository(session).delete(task_id):
        raise HTTPException(404, f"Task {task_id} not found")


@router.post("/tasks/{task_id}/done")
def done_task(
    task_id: int,
    body: TaskDoneBody,
    session: Session = Depends(get_session),
) -> CompletionResponse:
    try:
        result = complete_task(
            session,
            task_id,
            actual_minutes=body.actual_minutes,
            energy_before=body.energy_before,
            energy_after=body.energy_after,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return CompletionResponse(
        task=result.task.model_dump(),
        log=result.log.model_dump(),
        observed_ratio=result.observed_ratio,
        updated_area_ratio=result.updated_area_ratio,
    )


# ------------------------------------------------------------------ areas ---
@router.get("/areas")
def list_areas(session: Session = Depends(get_session)) -> list[Area]:
    return AreaRepository(session).list(limit=200)


@router.post("/areas", status_code=201)
def create_area(body: AreaCreate, session: Session = Depends(get_session)) -> Area:
    return AreaRepository(session).create(Area.model_validate(body))


@router.patch("/areas/{area_id}")
def update_area(
    area_id: int,
    body: AreaUpdate,
    session: Session = Depends(get_session),
) -> Area:
    area = AreaRepository(session).update(area_id, body)
    if area is None:
        raise HTTPException(404, f"Area {area_id} not found")
    return area


@router.delete("/areas/{area_id}", status_code=204)
def delete_area(area_id: int, session: Session = Depends(get_session)) -> None:
    if not AreaRepository(session).delete(area_id):
        raise HTTPException(404, f"Area {area_id} not found")


# ------------------------------------------------------------------ goals ---
@router.get("/goals")
def list_goals(
    status: str | None = None,
    area: int | None = None,
    session: Session = Depends(get_session),
) -> list[Goal]:
    filters: dict = {}
    if status is not None:
        filters["status"] = status
    if area is not None:
        filters["area_id"] = area
    return GoalRepository(session).list(limit=500, **filters)


@router.post("/goals", status_code=201)
def create_goal(body: GoalCreate, session: Session = Depends(get_session)) -> Goal:
    return GoalRepository(session).create(Goal.model_validate(body))


@router.patch("/goals/{goal_id}")
def update_goal(
    goal_id: int,
    body: GoalUpdate,
    session: Session = Depends(get_session),
) -> Goal:
    goal = GoalRepository(session).update(goal_id, body)
    if goal is None:
        raise HTTPException(404, f"Goal {goal_id} not found")
    return goal


@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(goal_id: int, session: Session = Depends(get_session)) -> None:
    if not GoalRepository(session).delete(goal_id):
        raise HTTPException(404, f"Goal {goal_id} not found")


# ----------------------------------------------------------------- projects ---
@router.get("/projects")
def list_projects(
    status: str | None = None,
    area: int | None = None,
    session: Session = Depends(get_session),
) -> list[Project]:
    filters: dict = {}
    if status is not None:
        filters["status"] = status
    if area is not None:
        filters["area_id"] = area
    return ProjectRepository(session).list(limit=500, **filters)


@router.post("/projects", status_code=201)
def create_project(body: ProjectCreate, session: Session = Depends(get_session)) -> Project:
    return ProjectRepository(session).create(Project.model_validate(body))


@router.patch("/projects/{project_id}")
def update_project(
    project_id: int,
    body: ProjectUpdate,
    session: Session = Depends(get_session),
) -> Project:
    project = ProjectRepository(session).update(project_id, body)
    if project is None:
        raise HTTPException(404, f"Project {project_id} not found")
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, session: Session = Depends(get_session)) -> None:
    if not ProjectRepository(session).delete(project_id):
        raise HTTPException(404, f"Project {project_id} not found")


# ------------------------------------------------------------------ ops ---
@router.post("/sync")
def api_sync(session: Session = Depends(get_session)):
    result = sync_vault_from_settings(session)
    return {
        "areas": result.areas,
        "goals": result.goals,
        "projects": result.projects,
        "tasks": result.tasks,
        "dropped_tasks": result.dropped_tasks,
        "skipped_files": result.skipped_files,
        "warnings": result.warnings,
    }


@router.post("/brief")
def api_brief(body: BriefBody, session: Session = Depends(get_session)):
    try:
        result = write_daily_brief(session, dry_run=body.dry_run)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "path": str(result.path),
        "content": result.content,
        "written": result.written,
    }


@router.post("/review")
def api_review(body: ReviewBody, session: Session = Depends(get_session)):
    week_start = body.week
    if week_start is not None:
        week_start = week_start_for(week_start)
    if body.satisfaction is not None:
        apply_satisfaction_weight_nudge(session, body.satisfaction)
    try:
        result = write_weekly_review(session, week_start=week_start, dry_run=body.dry_run)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    if body.satisfaction is not None and not body.dry_run:
        from lifeos.repositories import WeeklyReviewRepository

        repo = WeeklyReviewRepository(session)
        existing = repo.get_by_week(result.week_start)
        if existing is not None:
            existing.satisfaction = body.satisfaction
            session.add(existing)
    return {
        "path": str(result.path),
        "content": result.content,
        "written": result.written,
        "week_start": result.week_start.isoformat(),
    }
