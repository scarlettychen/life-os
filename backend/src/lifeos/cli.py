"""LifeOS command-line interface.

Thin CLI over repositories and the decision engine.
"""

from __future__ import annotations

from datetime import date
from typing import TypeVar

import typer
from rich.console import Console
from rich.table import Table

from lifeos.db import init_db, session_scope
from lifeos.engine.explain import explain_breakdown
from lifeos.engine.overload import OverloadReport
from lifeos.ingestion.obsidian.sync import SyncResult
from lifeos.ingestion.obsidian.watcher import run_watch_loop, watch_vault
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
    CalibrationRepository,
    GoalRepository,
    ProjectRepository,
    TaskRepository,
)
from lifeos.scheduler_app import run_daemon
from lifeos.schemas.planning import DayPlanResult, RestResult
from lifeos.schemas.results import RankedTask, RecommendationResult
from lifeos.services import (
    check_overload,
    check_rest,
    complete_task,
    plan_and_persist,
    recommend_now,
    resolve_vault_path,
    sync_vault_from_settings,
    write_daily_brief,
    write_weekly_review,
)
from lifeos.services.completion import CompletionResult
from lifeos.services.review import week_start_for
from lifeos.utils.dates import parse_due

app = typer.Typer(help="LifeOS — personal AI Chief of Staff.", no_args_is_help=True)
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


@app.command("now")
def now_cmd(
    limit: int = typer.Option(5, "--limit", "-n", min=1, max=50),
) -> None:
    """Recommend what to work on next (deterministic engine)."""
    with session_scope() as session:
        result = recommend_now(session)
        _print_recommendation(result, limit=limit)


@app.command("overload")
def overload_cmd() -> None:
    """Workload severity (green/yellow/red) and suggested cut-list."""
    with session_scope() as session:
        report = check_overload(session)
        _print_overload(report)


@app.command("done")
def done_cmd(
    task_id: int = typer.Argument(..., help="Task id to complete."),
    actual: int | None = typer.Option(
        None,
        "--actual",
        "-a",
        min=0,
        help="Actual minutes spent (defaults to estimate).",
    ),
    energy_before: float | None = typer.Option(
        None,
        "--energy-before",
        min=0.0,
        max=1.0,
        help="Energy level before (0-1).",
    ),
    energy_after: float | None = typer.Option(
        None,
        "--energy-after",
        min=0.0,
        max=1.0,
        help="Energy level after (0-1).",
    ),
) -> None:
    """Complete a task, log actual time, and update estimation calibration."""
    with session_scope() as session:
        try:
            result = complete_task(
                session,
                task_id,
                actual_minutes=actual,
                energy_before=energy_before,
                energy_after=energy_after,
            )
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        _print_completion(result)


@app.command("calibrate")
def calibrate_cmd() -> None:
    """Show estimation calibration factors per area."""
    with session_scope() as session:
        factors = CalibrationRepository(session).list_all(limit=100)
        if not factors:
            console.print("[dim]No calibration data yet — complete tasks with lifeos done.[/dim]")
            return
        table = Table(title="Estimation calibration")
        table.add_column("area")
        table.add_column("ratio")
        table.add_column("samples")
        table.add_column("meaning")
        for factor in sorted(factors, key=lambda f: (f.area_id is None, f.area_id or 0)):
            label = "global" if factor.area_id is None else str(factor.area_id)
            meaning = "on target"
            if factor.ratio > 1.05:
                meaning = "underestimating"
            elif factor.ratio < 0.95:
                meaning = "overestimating"
            table.add_row(label, f"{factor.ratio:.2f}×", str(factor.sample_count), meaning)
        console.print(table)


@app.command("review")
def review_cmd(
    week: str | None = typer.Option(
        None,
        "--week",
        help="Week start date (YYYY-MM-DD, Monday). Defaults to this week.",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print review without writing."),
    satisfaction: int | None = typer.Option(
        None,
        "--satisfaction",
        "-s",
        min=1,
        max=5,
        help="How the week felt (1-5); tunes balance weighting.",
    ),
) -> None:
    """Generate the weekly review and write it to the Obsidian vault."""
    week_start = None
    if week is not None:
        try:
            week_start = week_start_for(date.fromisoformat(week))
        except ValueError as exc:
            console.print("[red]Invalid --week: use YYYY-MM-DD[/red]")
            raise typer.Exit(code=1) from exc

    with session_scope() as session:
        if satisfaction is not None:
            from lifeos.services.energy import apply_satisfaction_weight_nudge

            apply_satisfaction_weight_nudge(session, satisfaction)
        try:
            result = write_weekly_review(session, week_start=week_start, dry_run=dry_run)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        if dry_run:
            console.print(result.content)
        else:
            console.print(f"[green]Weekly review written to[/green] {result.path}")
            if satisfaction is not None:
                from lifeos.repositories import WeeklyReviewRepository

                repo = WeeklyReviewRepository(session)
                existing = repo.get_by_week(result.week_start)
                if existing is not None:
                    existing.satisfaction = satisfaction
                    session.add(existing)


@app.command("plan")
def plan_cmd() -> None:
    """Build a time-blocked plan for the rest of today."""
    with session_scope() as session:
        result = plan_and_persist(session)
        _print_plan(result)


@app.command("rest")
def rest_cmd(
    hours: float = typer.Option(2.0, "--hours", "-h", min=0.5, help="Hours of rest to evaluate."),
) -> None:
    """Check whether you can afford to take time off."""
    with session_scope() as session:
        result = check_rest(session, hours=hours)
        _print_rest(result)


@app.command("brief")
def brief_cmd(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print brief without writing to vault."),
) -> None:
    """Write today's daily brief into the Obsidian vault."""
    with session_scope() as session:
        try:
            result = write_daily_brief(session, dry_run=dry_run)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        if dry_run:
            console.print(result.content)
        else:
            console.print(f"[green]Daily brief written to[/green] {result.path}")


@app.command("daemon")
def daemon_cmd() -> None:
    """Run background scheduler (daily brief at configured time). Ctrl+C to stop."""
    console.print("[green]Starting LifeOS daemon…[/green]")
    run_daemon()


@app.command("sync")
def sync_cmd() -> None:
    """Ingest goals, projects, and tasks from the Obsidian vault."""
    with session_scope() as session:
        try:
            result = sync_vault_from_settings(session)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        _print_sync_result(result)


@app.command("watch")
def watch_cmd() -> None:
    """Watch the Obsidian vault and sync on changes (Ctrl+C to stop)."""
    try:
        vault = resolve_vault_path()
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    def run_sync() -> None:
        with session_scope() as session:
            result = sync_vault_from_settings(session)
            console.print(
                f"[dim]Synced {result.tasks} tasks, {result.projects} projects, "
                f"{result.goals} goals[/dim]"
            )

    with session_scope():
        run_sync()

    console.print(f"[green]Watching[/green] {vault} — press Ctrl+C to stop.")
    observer = watch_vault(vault, run_sync)
    run_watch_loop(observer)


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
    due: str | None = typer.Option(None, "--due", help="Due date (YYYY-MM-DD or ISO datetime)."),
    priority: int = typer.Option(3, "--priority", "-p", min=1, max=5),
    energy: EnergyLevel = typer.Option(EnergyLevel.MEDIUM, "--energy"),
    deep: bool = typer.Option(False, "--deep", help="Requires a deep-work block."),
) -> None:
    due_date = None
    if due is not None:
        try:
            due_date = parse_due(due)
        except ValueError as exc:
            console.print(f"[red]Invalid --due: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    with session_scope() as session:
        task = TaskRepository(session).create(
            Task.model_validate(
                TaskCreate(
                    title=title,
                    project_id=project,
                    goal_id=goal,
                    area_id=area,
                    estimated_minutes=estimate,
                    due_date=due_date,
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
    due: str | None = typer.Option(None, "--due", help="Due date (YYYY-MM-DD or ISO datetime)."),
) -> None:
    due_date = None
    if due is not None:
        try:
            due_date = parse_due(due)
        except ValueError as exc:
            console.print(f"[red]Invalid --due: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    with session_scope() as session:
        task = TaskRepository(session).update(
            task_id,
            TaskUpdate(
                title=title,
                status=status,
                priority=priority,
                estimated_minutes=estimate,
                due_date=due_date,
            ),
        )
        task = _require(task, "Task", task_id)
        _print_task_table([task], title="Task updated")


@task_app.command("done")
def task_done(
    task_id: int = typer.Argument(...),
    actual: int | None = typer.Option(None, "--actual", help="Actual minutes spent."),
) -> None:
    with session_scope() as session:
        try:
            result = complete_task(session, task_id, actual_minutes=actual)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        _print_completion(result)


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
    for col in ("id", "title", "project", "status", "prio", "est(min)", "due", "energy", "deep"):
        table.add_column(col)
    for t in tasks:
        due = "-"
        if t.due_date is not None:
            due = t.due_date.strftime("%Y-%m-%d %H:%M")
        table.add_row(
            str(t.id),
            t.title,
            str(t.project_id or "-"),
            t.status.value,
            str(t.priority),
            "-" if t.estimated_minutes is None else str(t.estimated_minutes),
            due,
            t.energy_required.value,
            "yes" if t.is_deep_work else "no",
        )
    console.print(table)


def _print_recommendation(result: RecommendationResult, *, limit: int) -> None:
    if result.conflicts:
        console.print("[bold yellow]Scheduling conflicts[/bold yellow]")
        for conflict in result.conflicts:
            console.print(f"  [yellow]! {conflict.message}[/yellow]")
        console.print()

    if result.top_pick is None:
        console.print("[dim]No eligible tasks to recommend.[/dim]")
        return

    console.print(
        f"[bold green]Recommended next:[/bold green] {result.top_pick.title} "
        f"(score {result.top_pick.score:.2f})"
    )
    _print_ranked_table(result.ranked[:limit], title=f"Ranked tasks (top {limit})")


def _print_ranked_table(ranked: list[RankedTask], *, title: str) -> None:
    table = Table(title=title)
    for col in ("#", "task", "score", "urgency", "importance", "goal", "time", "slack(h)"):
        table.add_column(col)
    for i, item in enumerate(ranked, start=1):
        b = item.breakdown
        slack = "-"
        if b.slack_minutes is not None:
            slack = f"{b.slack_minutes / 60:.1f}"
        pin = " [pin]" if item.pinned else ""
        table.add_row(
            str(i),
            item.title + pin,
            f"{item.score:.2f}",
            f"{b.urgency:.2f}",
            f"{b.importance:.2f}",
            f"{b.goal_alignment:.2f}",
            f"{b.time_cost:.2f}",
            slack,
        )
    console.print(table)


def _print_sync_result(result: SyncResult) -> None:
    console.print(
        "[green]Vault sync complete.[/green] "
        f"areas={result.areas}, goals={result.goals}, "
        f"projects={result.projects}, tasks={result.tasks}, "
        f"dropped={result.dropped_tasks}, skipped_files={result.skipped_files}"
    )
    for warning in result.warnings:
        console.print(f"[yellow]! {warning}[/yellow]")


def _print_plan(result: DayPlanResult) -> None:
    if result.conflicts:
        console.print("[bold yellow]Scheduling conflicts[/bold yellow]")
        for conflict in result.conflicts:
            console.print(f"  [yellow]! {conflict.message}[/yellow]")
        console.print()

    if not result.blocks:
        console.print("[dim]No blocks scheduled — no free slots or eligible tasks.[/dim]")
        return

    table = Table(title="Today's plan")
    for col in ("start", "end", "task", "kind", "energy", "rationale"):
        table.add_column(col)
    for block in result.blocks:
        table.add_row(
            block.start.strftime("%H:%M"),
            block.end.strftime("%H:%M"),
            block.title,
            block.kind.value,
            f"{block.energy_fit:.0%}",
            block.rationale,
        )
    console.print(table)
    console.print(
        f"[dim]Scheduled {result.total_scheduled_minutes} min "
        f"({result.deep_work_minutes} min deep work)[/dim]"
    )
    if result.unscheduled_task_ids:
        console.print(
            f"[yellow]{len(result.unscheduled_task_ids)} task(s) could not be scheduled.[/yellow]"
        )


def _print_rest(result: RestResult) -> None:
    color = {"yes": "green", "partial": "yellow", "no": "red"}[result.verdict.value]
    console.print(f"[bold {color}]Rest verdict: {result.verdict.value.upper()}[/bold {color}]")
    console.print(result.message)
    if result.tasks_to_clear:
        ids = ", ".join(str(i) for i in result.tasks_to_clear)
        console.print(f"[dim]Critical task ids: {ids}[/dim]")


def _print_completion(result: CompletionResult) -> None:
    task = result.task
    console.print(f"[green]Completed:[/green] {task.title}")
    console.print(
        f"  actual {result.log.actual_minutes} min "
        f"(est {result.log.estimated_minutes}, ratio {result.observed_ratio:.2f}×)"
    )
    if result.updated_area_ratio is not None:
        console.print(
            f"  area calibration updated → {result.updated_area_ratio:.2f}×"
        )
    if result.vault_path:
        console.print(f"  [dim]Vault updated: {result.vault_path}[/dim]")


def _print_overload(report: OverloadReport) -> None:
    colors = {"green": "green", "yellow": "yellow", "red": "red"}
    color = colors.get(report.severity.value, "white")
    console.print(f"[bold {color}]{report.severity.value.upper()}[/bold {color}] — {report.label}")
    if report.conflicts:
        console.print("[bold yellow]Conflicts[/bold yellow]")
        for conflict in report.conflicts:
            console.print(f"  [yellow]! {conflict.message}[/yellow]")
    if report.cut_list:
        console.print("[bold]Suggested cut-list[/bold] (lowest priority, non-critical):")
        for item in report.cut_list:
            why = explain_breakdown(item.breakdown)
            console.print(f"  - {item.title} ({item.score:.2f}) — {why}")


if __name__ == "__main__":
    app()
