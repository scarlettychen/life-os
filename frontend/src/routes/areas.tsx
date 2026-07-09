import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api, qk, type Area, type AreaCreate, type AreaUpdate } from "@/lib/lifeos-api";
import { AppShell } from "@/components/lifeos/app-shell";
import { QueryState } from "@/components/lifeos/query-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export const Route = createFileRoute("/areas")({
  component: AreasPage,
});

function AreasPage() {
  const qc = useQueryClient();
  const areas = useQuery({ queryKey: qk.areas, queryFn: () => api.listAreas() });
  const invalidate = () => qc.invalidateQueries({ queryKey: qk.areas });

  const del = useMutation({
    mutationFn: (id: number) => api.deleteArea(id),
    onSuccess: () => { toast.success("Deleted"); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });

  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Area | null>(null);

  return (
    <AppShell>
      <div className="flex items-center gap-2 mb-6">
        <h1 className="text-2xl font-semibold mr-auto">Areas</h1>
        <Dialog open={creating} onOpenChange={setCreating}>
          <DialogTrigger asChild><Button>Add area</Button></DialogTrigger>
          <AreaForm
            title="New area"
            initial={null}
            onCancel={() => setCreating(false)}
            onSubmit={async (body) => {
              try {
                await api.createArea(body as AreaCreate);
                toast.success("Created"); setCreating(false); invalidate();
              } catch (e) { toast.error((e as Error).message); }
            }}
          />
        </Dialog>
      </div>
      <QueryState
        isLoading={areas.isLoading}
        error={areas.error}
        isEmpty={!!areas.data && areas.data.length === 0}
      >
        {areas.data && (
          <ul className="divide-y border rounded-md text-sm">
            {areas.data.map((a) => (
              <li key={a.id} className="p-3 flex items-center gap-3">
                <span
                  className="inline-block w-4 h-4 rounded"
                  style={{ backgroundColor: a.color || "#888" }}
                />
                <span className="font-medium">{a.name}</span>
                <span className="text-muted-foreground text-xs">{a.key}</span>
                <span className="ml-auto text-xs text-muted-foreground">
                  target {(a.target_allocation * 100).toFixed(0)}% · {a.active ? "active" : "inactive"}
                </span>
                <Button size="sm" variant="ghost" onClick={() => setEditing(a)}>Edit</Button>
                <Button
                  size="sm" variant="ghost"
                  onClick={() => { if (confirm(`Delete "${a.name}"?`)) del.mutate(a.id); }}
                >Delete</Button>
              </li>
            ))}
          </ul>
        )}
      </QueryState>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        {editing && (
          <AreaForm
            title="Edit area"
            initial={editing}
            onCancel={() => setEditing(null)}
            onSubmit={async (body) => {
              try {
                await api.updateArea(editing.id, body as AreaUpdate);
                toast.success("Saved"); setEditing(null); invalidate();
              } catch (e) { toast.error((e as Error).message); }
            }}
          />
        )}
      </Dialog>
    </AppShell>
  );
}

function AreaForm({
  title, initial, onSubmit, onCancel,
}: {
  title: string;
  initial: Area | null;
  onSubmit: (body: AreaCreate | AreaUpdate) => void | Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    key: initial?.key ?? "",
    name: initial?.name ?? "",
    target_allocation: initial?.target_allocation ?? 0.25,
    color: initial?.color ?? "#4f46e5",
    active: initial?.active ?? true,
  });
  return (
    <DialogContent>
      <DialogHeader><DialogTitle>{title}</DialogTitle></DialogHeader>
      <div className="grid gap-3">
        {!initial && (
          <div>
            <Label>Key (slug)</Label>
            <Input value={form.key} onChange={(e) => setForm({ ...form, key: e.target.value })} />
          </div>
        )}
        <div>
          <Label>Name</Label>
          <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <Label>Target allocation (0–1)</Label>
          <Input
            type="number" min={0} max={1} step={0.05}
            value={form.target_allocation}
            onChange={(e) => setForm({ ...form, target_allocation: Number(e.target.value) })}
          />
        </div>
        <div>
          <Label>Color</Label>
          <Input type="color" value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })} />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <Switch checked={form.active} onCheckedChange={(c) => setForm({ ...form, active: c })} />
          Active
        </label>
      </div>
      <DialogFooter>
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button
          onClick={() => {
            if (!form.name.trim()) { toast.error("Name required"); return; }
            if (!initial && !form.key.trim()) { toast.error("Key required"); return; }
            const body = initial
              ? { name: form.name, target_allocation: form.target_allocation, color: form.color, active: form.active }
              : form;
            onSubmit(body);
          }}
        >Save</Button>
      </DialogFooter>
    </DialogContent>
  );
}
