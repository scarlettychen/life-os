import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import {
  api,
  qk,
  type Task,
  type TaskCreate,
  type TaskStatus,
  type TaskUpdate,
  type Energy,
} from "@/lib/lifeos-api";
import { AppShell } from "@/components/lifeos/app-shell";
import { QueryState } from "@/components/lifeos/query-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { CompleteTaskDialog } from "@/routes/index";

export const Route = createFileRoute("/tasks")({
  component: TasksPage,
});

const STATUSES: TaskStatus[] = ["todo", "in_progress", "blocked", "done", "dropped"];
const ENERGIES: Energy[] = ["low", "medium", "high"];

function TasksPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("todo");
  const [projectFilter, setProjectFilter] = useState<string>("all");

  const filters = useMemo(
    () => ({
      status: statusFilter === "all" ? undefined : statusFilter,
      project: projectFilter === "all" ? undefined : Number(projectFilter),
    }),
    [statusFilter, projectFilter],
  );

  const tasks = useQuery({
    queryKey: qk.tasks(filters),
    queryFn: () => api.listTasks(filters),
  });
  const areas = useQuery({ queryKey: qk.areas, queryFn: () => api.listAreas() });
  const goals = useQuery({ queryKey: qk.goals(), queryFn: () => api.listGoals() });
  const projects = useQuery({
    queryKey: qk.projects(),
    queryFn: () => api.listProjects(),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["tasks"] });

  const patch = useMutation({
    mutationFn: ({ id, body }: { id: number; body: TaskUpdate }) =>
      api.updateTask(id, body),
    onSuccess: () => invalidate(),
    onError: (e: Error) => toast.error(e.message),
  });
  const del = useMutation({
    mutationFn: (id: number) => api.deleteTask(id),
    onSuccess: () => {
      toast.success("Deleted");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const [editing, setEditing] = useState<Task | null>(null);
  const [creating, setCreating] = useState(false);
  const [completeFor, setCompleteFor] = useState<{ id: number; title: string } | null>(null);

  return (
    <AppShell>
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <h1 className="text-2xl font-semibold mr-auto">Tasks</h1>
        <Dialog open={creating} onOpenChange={setCreating}>
          <DialogTrigger asChild>
            <Button>Add task</Button>
          </DialogTrigger>
          <TaskFormDialog
            title="New task"
            initial={null}
            areas={areas.data ?? []}
            goals={goals.data ?? []}
            projects={projects.data ?? []}
            onCancel={() => setCreating(false)}
            onSubmit={async (body) => {
              try {
                await api.createTask(body as TaskCreate);
                toast.success("Task created");
                setCreating(false);
                invalidate();
              } catch (e) {
                toast.error((e as Error).message);
              }
            }}
          />
        </Dialog>
      </div>

      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <Label>Status</Label>
          <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as TaskStatus | "all")}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {STATUSES.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Project</Label>
          <Select value={projectFilter} onValueChange={setProjectFilter}>
            <SelectTrigger className="w-52"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {(projects.data ?? []).map((p) => (
                <SelectItem key={p.id} value={String(p.id)}>{p.title}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button variant="outline" onClick={() => tasks.refetch()}>
          Refresh
        </Button>
      </div>

      <QueryState
        isLoading={tasks.isLoading}
        error={tasks.error}
        isEmpty={!!tasks.data && tasks.data.length === 0}
        emptyLabel="No tasks match the filters."
      >
        {tasks.data && (
          <ul className="divide-y border rounded-md">
            {tasks.data.map((t) => (
              <li key={t.id} className="p-3 text-sm flex flex-wrap gap-2 items-center">
                <span className="font-medium">{t.title}</span>
                <Badge variant="outline">{t.status}</Badge>
                <Badge variant="secondary">P{t.priority}</Badge>
                <Badge variant="outline">{t.energy_required}</Badge>
                {t.is_deep_work && <Badge>deep</Badge>}
                {t.pinned && <Badge variant="secondary">pinned</Badge>}
                {t.due_date && (
                  <span className="text-muted-foreground text-xs">
                    due {t.due_date.slice(0, 10)}
                    {t.is_hard_deadline ? " (hard)" : ""}
                  </span>
                )}
                {t.estimated_minutes !== null && (
                  <span className="text-muted-foreground text-xs">
                    est {t.estimated_minutes}m
                  </span>
                )}
                <div className="ml-auto flex gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      patch.mutate({ id: t.id, body: { pinned: !t.pinned } })
                    }
                  >
                    {t.pinned ? "Unpin" : "Pin"}
                  </Button>
                  <Select
                    value={t.status}
                    onValueChange={(v) =>
                      patch.mutate({ id: t.id, body: { status: v as TaskStatus } })
                    }
                  >
                    <SelectTrigger className="h-8 w-32"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {STATUSES.map((s) => (
                        <SelectItem key={s} value={s}>{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setCompleteFor({ id: t.id, title: t.title })}
                  >
                    Done
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setEditing(t)}>
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (confirm(`Delete "${t.title}"?`)) del.mutate(t.id);
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </QueryState>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        {editing && (
          <TaskFormDialog
            title="Edit task"
            initial={editing}
            areas={areas.data ?? []}
            goals={goals.data ?? []}
            projects={projects.data ?? []}
            onCancel={() => setEditing(null)}
            onSubmit={async (body) => {
              try {
                await api.updateTask(editing.id, body);
                toast.success("Saved");
                setEditing(null);
                invalidate();
              } catch (e) {
                toast.error((e as Error).message);
              }
            }}
          />
        )}
      </Dialog>

      <CompleteTaskDialog
        target={completeFor}
        onOpenChange={(o) => !o && setCompleteFor(null)}
      />
    </AppShell>
  );
}

function TaskFormDialog({
  title,
  initial,
  areas,
  goals,
  projects,
  onSubmit,
  onCancel,
}: {
  title: string;
  initial: Task | null;
  areas: import("@/lib/lifeos-api").Area[];
  goals: import("@/lib/lifeos-api").Goal[];
  projects: import("@/lib/lifeos-api").Project[];
  onSubmit: (body: TaskCreate | TaskUpdate) => void | Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<TaskUpdate>(() => ({
    title: initial?.title ?? "",
    notes: initial?.notes ?? "",
    area_id: initial?.area_id ?? null,
    goal_id: initial?.goal_id ?? null,
    project_id: initial?.project_id ?? null,
    estimated_minutes: initial?.estimated_minutes ?? null,
    due_date: initial?.due_date ?? null,
    is_hard_deadline: initial?.is_hard_deadline ?? false,
    priority: initial?.priority ?? 3,
    energy_required: initial?.energy_required ?? "medium",
    is_deep_work: initial?.is_deep_work ?? false,
    pinned: initial?.pinned ?? false,
    status: initial?.status ?? "todo",
  }));

  const set = <K extends keyof TaskUpdate>(k: K, v: TaskUpdate[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  return (
    <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
      </DialogHeader>
      <div className="grid gap-3">
        <div>
          <Label>Title</Label>
          <Input
            value={form.title ?? ""}
            onChange={(e) => set("title", e.target.value)}
          />
        </div>
        <div>
          <Label>Notes</Label>
          <Textarea
            value={form.notes ?? ""}
            onChange={(e) => set("notes", e.target.value)}
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <Label>Area</Label>
            <Select
              value={form.area_id ? String(form.area_id) : "none"}
              onValueChange={(v) => set("area_id", v === "none" ? null : Number(v))}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {areas.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>{a.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Goal</Label>
            <Select
              value={form.goal_id ? String(form.goal_id) : "none"}
              onValueChange={(v) => set("goal_id", v === "none" ? null : Number(v))}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {goals.map((g) => (
                  <SelectItem key={g.id} value={String(g.id)}>{g.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Project</Label>
            <Select
              value={form.project_id ? String(form.project_id) : "none"}
              onValueChange={(v) => set("project_id", v === "none" ? null : Number(v))}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>{p.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <Label>Estimated minutes</Label>
            <Input
              type="number"
              min={0}
              value={form.estimated_minutes ?? ""}
              onChange={(e) =>
                set(
                  "estimated_minutes",
                  e.target.value === "" ? null : Number(e.target.value),
                )
              }
            />
          </div>
          <div>
            <Label>Due date</Label>
            <Input
              type="datetime-local"
              value={form.due_date ? form.due_date.slice(0, 16) : ""}
              onChange={(e) =>
                set("due_date", e.target.value ? new Date(e.target.value).toISOString() : null)
              }
            />
          </div>
          <div>
            <Label>Priority (1–5)</Label>
            <Input
              type="number"
              min={1}
              max={5}
              value={form.priority ?? 3}
              onChange={(e) => set("priority", Number(e.target.value))}
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>Energy</Label>
            <Select
              value={form.energy_required ?? "medium"}
              onValueChange={(v) => set("energy_required", v as Energy)}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {ENERGIES.map((e) => (
                  <SelectItem key={e} value={e}>{e}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {initial && (
            <div>
              <Label>Status</Label>
              <Select
                value={form.status ?? "todo"}
                onValueChange={(v) => set("status", v as TaskStatus)}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
        <div className="flex flex-wrap gap-4 pt-2">
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={!!form.is_hard_deadline}
              onCheckedChange={(c) => set("is_hard_deadline", !!c)}
            />
            Hard deadline
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={!!form.is_deep_work}
              onCheckedChange={(c) => set("is_deep_work", !!c)}
            />
            Deep work
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={!!form.pinned}
              onCheckedChange={(c) => set("pinned", !!c)}
            />
            Pinned
          </label>
        </div>
      </div>
      <DialogFooter>
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button
          onClick={() => {
            if (!form.title?.trim()) {
              toast.error("Title is required");
              return;
            }
            onSubmit(form);
          }}
        >
          Save
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}
