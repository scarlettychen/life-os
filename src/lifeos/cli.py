"""LifeOS command-line interface (M0).

Thin CLI over the repositories for managing areas, goals, projects, and tasks.
Every command opens a transactional session, performs one operation, and prints
a result table.
"""

from __future__ import annotations

from typing import TypeVar

import typer
from rich.console import Console
from rich.table import Table

from lifeos.db import init_db, session_scope
from lifeos.models.area import Area, AreaCreate, AreaUpdate
from lifeos.models.enums import (
    EnergyLevel,
    GoalHorizon,
    GoalStatus,
    ProjectStatus,
    TaskStatus,
)
from lifeos.models.goal import Goal, GoalCreate, GoalUpdate
from lifeos.models.project import Project, ProjectCreate, ProjectUpdate
from lifeos.models.task import Task, TaskCreate, TaskUpdate
from lifeos.repositories import (
    AreaRepository,
    GoalRepository,
    ProjectRepository,
    TaskRepository,
)

app = typer.Typer(help="LifeOS — personal AI Chief of Staff (M0 CLI).", no_args_is_help=True)
console = Console()

T = TypeVar("T")

area_app = typer.Typer(help="Manage life-domain areas.", no_args_is_help=True)
goal_app = typer.Typer(help="Manage long-term goals.", no_args_is_help=True)
project_app = typer.Typer(help="Manage projects.", no_args_is_help=True)
task_app = typer.Typer(help="Manage tasks.", no_args_is_help=True)

app.add_typer(area_app, name="area")
app.add_typer(goal_app, name="goal")
app.add_typer(project_app, name="project")
app.add_typer(task_app, name="task")


@app.command()
def init() -> None:
    """Create the database schema."""
    init_db()
    console.print("[green]Database initialized.[/green]")


# --------------------------------------------------------------------------- #
# Areas
# --------------------------------------------------------------------------- #
@area_app.command("add")
def area_add(
    key: str = typer.Argument(..., help="Unique slug, e.g. 'robotics'."),
    name: str = typer.Option(..., "--name", "-n"),
    target: float = typer.Option(0.0, "--target", help="Target time allocation (0-1)."),
    color: str | None = typer.Option(None, "--color"),
) -> None:
    with session_scope() as session:
        area = AreaRepository(session).create(
            Area.model_validate(
                AreaCreate(key=key, name=name, target_allocation=target, color=color)
            )
        )
        _print_area_table([area], title="Area created")


@area_app.command("list")
def area_list() -> None:
    with session_scope() as session:
        _print_area_table(AreaRepository(session).list(), title="Areas")


@area_app.command("update")
def area_update(
    area_id: int = typer.Argument(...),
    name: str | None = typer.Option(None, "--name", "-n"),
    target: float | None = typer.Option(None, "--target"),
    color: str | None = typer.Option(None, "--color"),
    active: bool | None = typer.Option(None, "--active/--inactive"),
) -> None:
    with session_scope() as session:
        area = AreaRepository(session).update(
            area_id,
            AreaUpdate(name=name, target_allocation=target, color=color, active=active),
        )
        area = _require(area, "Area", area_id)
        _print_area_table([area], title="Area updated")


@area_app.command("rm")
def area_rm(area_id: int = typer.Argument(...)) -> None:
    with session_scope() as session:
        ok = AreaRepository(session).delete(area_id)
        _require(ok or None, "Area", area_id)
        console.print(f"[green]Deleted area {area_id}.[/green]")


# --------------------------------------------------------------------------- #
# Goals
# --------------------------------------------------------------------------- #
@goal_app.command("add")
def goal_add(
    title: str = typer.Argument(...),
    area: int | None = typer.Option(None, "--area", help="Area id."),
    horizon: GoalHorizon = typer.Option(GoalHorizon.MEDIUM, "--horizon"),
    priority: int = typer.Option(3, "--priority", "-p", min=1, max=5),
    description: str | None = typer.Option(None, "--desc"),
) -> None:
    with session_scope() as session:
        goal = GoalRepository(session).create(
            Goal.model_validate(
                GoalCreate(
                    title=title,
                    area_id=area,
                    horizon=horizon,
                    priority=priority,
                    description=description,
                )
            )
        )
        _print_goal_table([goal], title="Goal created")


@goal_app.command("list")
def goal_list(
    status: GoalStatus | None = typer.Option(None, "--status"),
    area: int | None = typer.Option(None, "--area"),
) -> None:
    with session_scope() as session:
        goals = GoalRepository(session).list(status=status, area_id=area)
        _print_goal_table(goals, title="Goals")


@goal_app.command("update")
def goal_update(
    goal_id: int = typer.Argument(...),
    title: str | None = typer.Option(None, "--title"),
    priority: int | None = typer.Option(None, "--priority", "-p", min=1, max=5),
    status: GoalStatus | None = typer.Option(None, "--status"),
    progress: float | None = typer.Option(None, "--progress", min=0.0, max=1.0),
) -> None:
    with session_scope() as session:
        goal = GoalRepository(session).update(
            goal_id,
            GoalUpdate(title=title, priority=priority, status=status, progress=progress),
        )
        goal = _require(goal, "Goal", goal_id)
        _print_goal_table([goal], title="Goal updated")


@goal_app.command("rm")
def goal_rm(goal_id: int = typer.Argument(...)) -> None:
    with session_scope() as session:
        ok = GoalRepository(session).delete(goal_id)
        _require(ok or None, "Goal", goal_id)
        console.print(f"[green]Deleted goal {goal_id}.[/green]")


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
@project_app.command("add")
def project_add(
    title: str = typer.Argument(...),
    area: int | None = typer.Option(None, "--area"),
    goal: int | None = typer.Option(None, "--goal"),
    effort: float | None = typer.Option(None, "--effort", help="Estimated effort (hours)."),
    priority: int = typer.Option(3, "--priority", "-p", min=1, max=5),
) -> None:
    with session_scope() as session:
        project = ProjectRepository(session).create(
            Project.model_validate(
                ProjectCreate(
                    title=title,
                    area_id=area,
                    goal_id=goal,
                    estimated_effort_hours=effort,
                    priority=priority,
                )
            )
        )
        _print_project_table([project], title="Project created")


@project_app.command("list")
def project_list(
    status: ProjectStatus | None = typer.Option(None, "--status"),
    area: int | None = typer.Option(None, "--area"),
) -> None:
    with session_scope() as session:
        projects = ProjectRepository(session).list(status=status, area_id=area)
        _print_project_table(projects, title="Projects")


@project_app.command("update")
def project_update(
    project_id: int = typer.Argument(...),
    title: str | None = typer.Option(None, "--title"),
    status: ProjectStatus | None = typer.Option(None, "--status"),
    priority: int | None = typer.Option(None, "--priority", "-p", min=1, max=5),
    progress: float | None = typer.Option(None, "--progress", min=0.0, max=1.0),
) -> None:
    with session_scope() as session:
        project = ProjectRepository(session).update(
            project_id,
            ProjectUpdate(title=title, status=status, priority=priority, progress=progress),
        )
        project = _require(project, "Project", project_id)
        _print_project_table([project], title="Project updated")


@project_app.command("rm")
def project_rm(project_id: int = typer.Argument(...)) -> None:
    with session_scope() as session:
        ok = ProjectRepository(session).delete(project_id)
        _require(ok or None, "Project", project_id)
        console.print(f"[green]Deleted project {project_id}.[/green]")


# --------------------------------------------------------------------------- #
# Tasks
# --------------------------------------------------------------------------- #
@task_app.command("add")
def task_add(
    title: str = typer.Argument(...),
    project: int | None = typer.Option(None, "--project"),
    goal: int | None = typer.Option(None, "--goal"),
    area: int | None = typer.Option(None, "--area"),
    estimate: int | None = typer.Option(None, "--estimate", help="Estimated minutes."),
    priority: int = typer.Option(3, "--priority", "-p", min=1, max=5),
    energy: EnergyLevel = typer.Option(EnergyLevel.MEDIUM, "--energy"),
    deep: bool = typer.Option(False, "--deep", help="Requires a deep-work block."),
) -> None:
    with session_scope() as session:
        task = TaskRepository(session).create(
            Task.model_validate(
                TaskCreate(
                    title=title,
                    project_id=project,
                    goal_id=goal,
                    area_id=area,
                    estimated_minutes=estimate,
                    priority=priority,
                    energy_required=energy,
                    is_deep_work=deep,
                )
            )
        )
        _print_task_table([task], title="Task created")


@task_app.command("list")
def task_list(
    status: TaskStatus | None = typer.Option(None, "--status"),
    project: int | None = typer.Option(None, "--project"),
) -> None:
    with session_scope() as session:
        tasks = TaskRepository(session).list(status=status, project_id=project)
        _print_task_table(tasks, title="Tasks")


@task_app.command("show")
def task_show(task_id: int = typer.Argument(...)) -> None:
    with session_scope() as session:
        task = TaskRepository(session).get(task_id)
        task = _require(task, "Task", task_id)
        _print_task_table([task], title=f"Task {task_id}")


@task_app.command("update")
def task_update(
    task_id: int = typer.Argument(...),
    title: str | None = typer.Option(None, "--title"),
    status: TaskStatus | None = typer.Option(None, "--status"),
    priority: int | None = typer.Option(None, "--priority", "-p", min=1, max=5),
    estimate: int | None = typer.Option(None, "--estimate"),
) -> None:
    with session_scope() as session:
        task = TaskRepository(session).update(
            task_id,
            TaskUpdate(title=title, status=status, priority=priority, estimated_minutes=estimate),
        )
        task = _require(task, "Task", task_id)
        _print_task_table([task], title="Task updated")


@task_app.command("done")
def task_done(
    task_id: int = typer.Argument(...),
    actual: int | None = typer.Option(None, "--actual", help="Actual minutes spent."),
) -> None:
    with session_scope() as session:
        task = TaskRepository(session).mark_done(task_id, actual_minutes=actual)
        task = _require(task, "Task", task_id)
        _print_task_table([task], title="Task completed")


@task_app.command("rm")
def task_rm(task_id: int = typer.Argument(...)) -> None:
    with session_scope() as session:
        ok = TaskRepository(session).delete(task_id)
        _require(ok or None, "Task", task_id)
        console.print(f"[green]Deleted task {task_id}.[/green]")


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #
def _require(value: T | None, entity: str, entity_id: int) -> T:
    """Return ``value`` or abort the command if the entity was not found."""
    if value is None:
        console.print(f"[red]{entity} {entity_id} not found.[/red]")
        raise typer.Exit(code=1)
    return value


def _print_area_table(areas: list[Area], *, title: str) -> None:
    table = Table(title=title)
    for col in ("id", "key", "name", "target", "active"):
        table.add_column(col)
    for a in areas:
        table.add_row(str(a.id), a.key, a.name, f"{a.target_allocation:.2f}", str(a.active))
    console.print(table)


def _print_goal_table(goals: list[Goal], *, title: str) -> None:
    table = Table(title=title)
    for col in ("id", "title", "area", "horizon", "priority", "status", "progress"):
        table.add_column(col)
    for g in goals:
        table.add_row(
            str(g.id),
            g.title,
            str(g.area_id or "-"),
            g.horizon.value,
            str(g.priority),
            g.status.value,
            f"{g.progress:.0%}",
        )
    console.print(table)


def _print_project_table(projects: list[Project], *, title: str) -> None:
    table = Table(title=title)
    for col in ("id", "title", "area", "goal", "status", "priority", "effort(h)", "progress"):
        table.add_column(col)
    for p in projects:
        table.add_row(
            str(p.id),
            p.title,
            str(p.area_id or "-"),
            str(p.goal_id or "-"),
            p.status.value,
            str(p.priority),
            "-" if p.estimated_effort_hours is None else f"{p.estimated_effort_hours:g}",
            f"{p.progress:.0%}",
        )
    console.print(table)


def _print_task_table(tasks: list[Task], *, title: str) -> None:
    table = Table(title=title)
    for col in ("id", "title", "project", "status", "prio", "est(min)", "energy", "deep"):
        table.add_column(col)
    for t in tasks:
        table.add_row(
            str(t.id),
            t.title,
            str(t.project_id or "-"),
            t.status.value,
            str(t.priority),
            "-" if t.estimated_minutes is None else str(t.estimated_minutes),
            t.energy_required.value,
            "yes" if t.is_deep_work else "no",
        )
    console.print(table)


if __name__ == "__main__":
    app()
