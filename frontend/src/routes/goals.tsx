import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import {
  api, qk,
  type Goal, type GoalCreate, type GoalUpdate, type Horizon,
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

export const Route = createFileRoute("/goals")({
  component: GoalsPage,
});

const HORIZONS: Horizon[] = ["short", "medium", "long"];

function GoalsPage() {
  const qc = useQueryClient();
  const [status, setStatus] = useState("all");
  const [areaFilter, setAreaFilter] = useState("all");
  const filters = useMemo(() => ({
    status: status === "all" ? undefined : status,
    area: areaFilter === "all" ? undefined : Number(areaFilter),
  }), [status, areaFilter]);

  const goals = useQuery({
    queryKey: qk.goals(filters),
    queryFn: () => api.listGoals(filters),
  });
  const areas = useQuery({ queryKey: qk.areas, queryFn: () => api.listAreas() });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["goals"] });

  const del = useMutation({
    mutationFn: (id: number) => api.deleteGoal(id),
    onSuccess: () => { toast.success("Deleted"); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });

  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Goal | null>(null);

  return (
    <AppShell>
      <div className="flex items-center gap-2 mb-6">
        <h1 className="text-2xl font-semibold mr-auto">Goals</h1>
        <Dialog open={creating} onOpenChange={setCreating}>
          <DialogTrigger asChild><Button>Add goal</Button></DialogTrigger>
          <GoalForm
            title="New goal" initial={null} areas={areas.data ?? []}
            onCancel={() => setCreating(false)}
            onSubmit={async (body) => {
              try { await api.createGoal(body as GoalCreate); toast.success("Created"); setCreating(false); invalidate(); }
              catch (e) { toast.error((e as Error).message); }
            }}
          />
        </Dialog>
      </div>

      <div className="flex gap-3 mb-4">
        <div>
          <Label>Status</Label>
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
        <div>
          <Label>Area</Label>
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
        isLoading={goals.isLoading} error={goals.error}
        isEmpty={!!goals.data && goals.data.length === 0}
      >
        {goals.data && (
          <ul className="divide-y border rounded-md text-sm">
            {goals.data.map((g) => (
              <li key={g.id} className="p-3 flex flex-wrap items-center gap-2">
                <span className="font-medium">{g.title}</span>
                <Badge variant="outline">{g.horizon}</Badge>
                <Badge variant="secondary">P{g.priority}</Badge>
                <span className="text-xs text-muted-foreground">
                  {g.progress}% · {g.status}
                </span>
                <div className="ml-auto flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => setEditing(g)}>Edit</Button>
                  <Button size="sm" variant="ghost" onClick={() => { if (confirm(`Delete "${g.title}"?`)) del.mutate(g.id); }}>Delete</Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </QueryState>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        {editing && (
          <GoalForm
            title="Edit goal" initial={editing} areas={areas.data ?? []}
            onCancel={() => setEditing(null)}
            onSubmit={async (body) => {
              try { await api.updateGoal(editing.id, body as GoalUpdate); toast.success("Saved"); setEditing(null); invalidate(); }
              catch (e) { toast.error((e as Error).message); }
            }}
          />
        )}
      </Dialog>
    </AppShell>
  );
}

function GoalForm({
  title, initial, areas, onSubmit, onCancel,
}: {
  title: string;
  initial: Goal | null;
  areas: import("@/lib/lifeos-api").Area[];
  onSubmit: (body: GoalCreate | GoalUpdate) => void | Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<GoalUpdate>({
    title: initial?.title ?? "",
    description: initial?.description ?? "",
    area_id: initial?.area_id ?? null,
    horizon: initial?.horizon ?? "medium",
    priority: initial?.priority ?? 3,
    progress: initial?.progress ?? 0,
    status: initial?.status ?? "active",
    target_date: initial?.target_date ?? null,
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
          <div>
            <Label>Area</Label>
            <Select
              value={form.area_id ? String(form.area_id) : "none"}
              onValueChange={(v) => setForm({ ...form, area_id: v === "none" ? null : Number(v) })}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {areas.map((a) => (<SelectItem key={a.id} value={String(a.id)}>{a.name}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Horizon</Label>
            <Select value={form.horizon ?? "medium"} onValueChange={(v) => setForm({ ...form, horizon: v as Horizon })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {HORIZONS.map((h) => <SelectItem key={h} value={h}>{h}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div><Label>Priority (1–5)</Label>
            <Input type="number" min={1} max={5} value={form.priority ?? 3}
              onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })} />
          </div>
          <div><Label>Progress %</Label>
            <Input type="number" min={0} max={100} value={form.progress ?? 0}
              onChange={(e) => setForm({ ...form, progress: Number(e.target.value) })} />
          </div>
          <div><Label>Target date</Label>
            <Input type="date"
              value={form.target_date ? form.target_date.slice(0, 10) : ""}
              onChange={(e) => setForm({ ...form, target_date: e.target.value || null })} />
          </div>
        </div>
        <div>
          <Label>Status</Label>
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
