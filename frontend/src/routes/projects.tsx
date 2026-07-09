import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import {
  api, qk,
  type Project, type ProjectCreate, type ProjectUpdate,
} from "@/lib/lifeos-api";
import { AppShell } from "@/components/lifeos/app-shell";
import { QueryState } from "@/components/lifeos/query-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";

export const Route = createFileRoute("/projects")({
  component: ProjectsPage,
});

function ProjectsPage() {
  const qc = useQueryClient();
  const [status, setStatus] = useState("all");
  const [areaFilter, setAreaFilter] = useState("all");
  const filters = useMemo(() => ({
    status: status === "all" ? undefined : status,
    area: areaFilter === "all" ? undefined : Number(areaFilter),
  }), [status, areaFilter]);

  const projects = useQuery({
    queryKey: qk.projects(filters),
    queryFn: () => api.listProjects(filters),
  });
  const areas = useQuery({ queryKey: qk.areas, queryFn: () => api.listAreas() });
  const goals = useQuery({ queryKey: qk.goals(), queryFn: () => api.listGoals() });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["projects"] });

  const del = useMutation({
    mutationFn: (id: number) => api.deleteProject(id),
    onSuccess: () => { toast.success("Deleted"); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });

  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);

  return (
    <AppShell>
      <div className="flex items-center gap-2 mb-6">
        <h1 className="text-2xl font-semibold mr-auto">Projects</h1>
        <Dialog open={creating} onOpenChange={setCreating}>
          <DialogTrigger asChild><Button>Add project</Button></DialogTrigger>
          <ProjectForm
            title="New project" initial={null}
            areas={areas.data ?? []} goals={goals.data ?? []}
            onCancel={() => setCreating(false)}
            onSubmit={async (body) => {
              try { await api.createProject(body as ProjectCreate); toast.success("Created"); setCreating(false); invalidate(); }
              catch (e) { toast.error((e as Error).message); }
            }}
          />
        </Dialog>
      </div>

      <div className="flex gap-3 mb-4">
        <div><Label>Status</Label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="done">Done</SelectItem>
              <SelectItem value="dropped">Dropped</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div><Label>Area</Label>
          <Select value={areaFilter} onValueChange={setAreaFilter}>
            <SelectTrigger className="w-52"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {(areas.data ?? []).map((a) => (
                <SelectItem key={a.id} value={String(a.id)}>{a.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <QueryState
        isLoading={projects.isLoading} error={projects.error}
        isEmpty={!!projects.data && projects.data.length === 0}
      >
        {projects.data && (
          <ul className="divide-y border rounded-md text-sm">
            {projects.data.map((p) => (
              <li key={p.id} className="p-3 flex flex-wrap items-center gap-2">
                <span className="font-medium">{p.title}</span>
                <Badge variant="outline">{p.status}</Badge>
                <Badge variant="secondary">P{p.priority}</Badge>
                <span className="text-xs text-muted-foreground">
                  {p.progress}%{p.estimated_effort_hours !== null ? ` · ${p.estimated_effort_hours}h` : ""}
                </span>
                <div className="ml-auto flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => setEditing(p)}>Edit</Button>
                  <Button size="sm" variant="ghost" onClick={() => { if (confirm(`Delete "${p.title}"?`)) del.mutate(p.id); }}>Delete</Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </QueryState>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        {editing && (
          <ProjectForm
            title="Edit project" initial={editing}
            areas={areas.data ?? []} goals={goals.data ?? []}
            onCancel={() => setEditing(null)}
            onSubmit={async (body) => {
              try { await api.updateProject(editing.id, body as ProjectUpdate); toast.success("Saved"); setEditing(null); invalidate(); }
              catch (e) { toast.error((e as Error).message); }
            }}
          />
        )}
      </Dialog>
    </AppShell>
  );
}

function ProjectForm({
  title, initial, areas, goals, onSubmit, onCancel,
}: {
  title: string;
  initial: Project | null;
  areas: import("@/lib/lifeos-api").Area[];
  goals: import("@/lib/lifeos-api").Goal[];
  onSubmit: (body: ProjectCreate | ProjectUpdate) => void | Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<ProjectUpdate>({
    title: initial?.title ?? "",
    description: initial?.description ?? "",
    area_id: initial?.area_id ?? null,
    goal_id: initial?.goal_id ?? null,
    estimated_effort_hours: initial?.estimated_effort_hours ?? null,
    priority: initial?.priority ?? 3,
    progress: initial?.progress ?? 0,
    status: initial?.status ?? "active",
  });
  return (
    <DialogContent className="max-w-xl">
      <DialogHeader><DialogTitle>{title}</DialogTitle></DialogHeader>
      <div className="grid gap-3">
        <div><Label>Title</Label>
          <Input value={form.title ?? ""} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </div>
        <div><Label>Description</Label>
          <Textarea value={form.description ?? ""} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div><Label>Area</Label>
            <Select value={form.area_id ? String(form.area_id) : "none"}
              onValueChange={(v) => setForm({ ...form, area_id: v === "none" ? null : Number(v) })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {areas.map((a) => (<SelectItem key={a.id} value={String(a.id)}>{a.name}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
          <div><Label>Goal</Label>
            <Select value={form.goal_id ? String(form.goal_id) : "none"}
              onValueChange={(v) => setForm({ ...form, goal_id: v === "none" ? null : Number(v) })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {goals.map((g) => (<SelectItem key={g.id} value={String(g.id)}>{g.title}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div><Label>Effort (h)</Label>
            <Input type="number" min={0} step={0.5}
              value={form.estimated_effort_hours ?? ""}
              onChange={(e) => setForm({ ...form, estimated_effort_hours: e.target.value === "" ? null : Number(e.target.value) })} />
          </div>
          <div><Label>Priority (1–5)</Label>
            <Input type="number" min={1} max={5} value={form.priority ?? 3}
              onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })} />
          </div>
          <div><Label>Progress %</Label>
            <Input type="number" min={0} max={100} value={form.progress ?? 0}
              onChange={(e) => setForm({ ...form, progress: Number(e.target.value) })} />
          </div>
        </div>
        <div><Label>Status</Label>
          <Select value={form.status ?? "active"} onValueChange={(v) => setForm({ ...form, status: v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="active">active</SelectItem>
              <SelectItem value="paused">paused</SelectItem>
              <SelectItem value="done">done</SelectItem>
              <SelectItem value="dropped">dropped</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <DialogFooter>
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => {
          if (!form.title?.trim()) { toast.error("Title required"); return; }
          onSubmit(form);
        }}>Save</Button>
      </DialogFooter>
    </DialogContent>
  );
}
