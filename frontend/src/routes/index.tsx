import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api, qk, type CompleteTaskBody } from "@/lib/lifeos-api";
import { formatMessageDates, fmtTime } from "@/lib/format";
import { AppShell } from "@/components/lifeos/app-shell";
import { QueryState } from "@/components/lifeos/query-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export const Route = createFileRoute("/")({
  component: Dashboard,
});

const NOW_LIMIT = 5;
const REST_HOURS = 3;

function Dashboard() {
  const router = useRouter();
  const qc = useQueryClient();
  const [loaded, setLoaded] = useState(false);

  const now = useQuery({
    queryKey: qk.now(NOW_LIMIT),
    queryFn: () => api.getNow(NOW_LIMIT),
    enabled: loaded,
  });
  const plan = useQuery({
    queryKey: qk.plan,
    queryFn: () => api.getPlan(),
    enabled: loaded,
  });
  const rest = useQuery({
    queryKey: qk.rest(REST_HOURS),
    queryFn: () => api.getRest(REST_HOURS),
    enabled: loaded,
  });
  const calibration = useQuery({
    queryKey: qk.calibration,
    queryFn: () => api.getCalibration(),
    enabled: loaded,
  });

  const sync = useMutation({
    mutationFn: () => api.syncVault(),
    onSuccess: () => {
      toast.success("Vault sync started");
      qc.invalidateQueries();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const [completeFor, setCompleteFor] = useState<{ id: number; title: string } | null>(null);

  const refreshAll = () => {
    setLoaded(true);
    void now.refetch();
    void plan.refetch();
    void rest.refetch();
    void calibration.refetch();
  };

  return (
    <AppShell>
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <h1 className="text-2xl font-semibold mr-auto">Dashboard</h1>
        <Button
          variant="outline"
          onClick={() => {
            refreshAll();
            router.invalidate();
          }}
        >
          Refresh
        </Button>
        <Button
          variant="outline"
          onClick={() => sync.mutate()}
          disabled={sync.isPending}
        >
          {sync.isPending ? "Syncing…" : "Sync vault"}
        </Button>
      </div>

      {!loaded ? (
        <p className="text-sm text-muted-foreground py-8">
          Click Refresh to load your dashboard.
        </p>
      ) : (
      <div className="grid gap-6 lg:grid-cols-2">
        {/* NOW */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>What to work on now</CardTitle>
            <Button size="sm" variant="secondary" onClick={() => now.refetch()}>
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            <QueryState
              isLoading={now.isLoading}
              error={now.error}
              isEmpty={!!now.data && now.data.ranked.length === 0}
              emptyLabel="No eligible tasks. Add or unblock some tasks."
            >
              {now.data && (
                <div className="space-y-4">
                  {now.data.top_pick && (
                    <div className="border rounded-md p-3 bg-accent/30">
                      <div className="text-xs text-muted-foreground">Top pick</div>
                      <div className="font-medium">{now.data.top_pick.title}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        score {now.data.top_pick.score.toFixed(2)}
                      </div>
                      <Button
                        size="sm"
                        className="mt-2"
                        onClick={() =>
                          setCompleteFor({
                            id: now.data!.top_pick!.task_id,
                            title: now.data!.top_pick!.title,
                          })
                        }
                      >
                        Complete top pick
                      </Button>
                    </div>
                  )}
                  <div>
                    <div className="text-xs text-muted-foreground mb-2">
                      Ranked ({now.data.eligible_count} eligible)
                    </div>
                    <ul className="divide-y border rounded-md">
                      {now.data.ranked.map((r) => (
                        <li key={r.task_id} className="p-3 text-sm">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{r.title}</span>
                            {r.pinned && <Badge variant="secondary">pinned</Badge>}
                            {!r.eligible && <Badge variant="outline">ineligible</Badge>}
                            <span className="ml-auto text-muted-foreground">
                              score {r.score.toFixed(2)}
                            </span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <ConflictList conflicts={now.data.conflicts} />
                </div>
              )}
            </QueryState>
          </CardContent>
        </Card>

        {/* PLAN */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Today's plan</CardTitle>
            <Button size="sm" variant="secondary" onClick={() => plan.refetch()}>
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            <QueryState
              isLoading={plan.isLoading}
              error={plan.error}
              isEmpty={!!plan.data && plan.data.blocks.length === 0}
              emptyLabel="No blocks scheduled."
            >
              {plan.data && (
                <div className="space-y-3">
                  <div className="text-xs text-muted-foreground">
                    Scheduled {plan.data.total_scheduled_minutes}m · Deep work{" "}
                    {plan.data.deep_work_minutes}m · Unscheduled{" "}
                    {plan.data.unscheduled_task_ids.length}
                  </div>
                  <ul className="divide-y border rounded-md">
                    {plan.data.blocks.map((b, i) => (
                      <li key={i} className="p-3 text-sm flex flex-wrap gap-2">
                        <span className="text-xs text-muted-foreground">
                          {fmtTime(b.start)}–{fmtTime(b.end)}
                        </span>
                        <span className="font-medium">{b.title}</span>
                        <Badge variant="outline">{b.kind}</Badge>
                        <Badge variant="secondary">{b.status}</Badge>
                        <div className="w-full text-xs text-muted-foreground">
                          {b.rationale}
                        </div>
                        {b.task_id && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() =>
                              setCompleteFor({ id: b.task_id!, title: b.title })
                            }
                          >
                            Complete
                          </Button>
                        )}
                      </li>
                    ))}
                  </ul>
                  <ConflictList conflicts={plan.data.conflicts} />
                </div>
              )}
            </QueryState>
          </CardContent>
        </Card>

        {/* REST */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Rest check</CardTitle>
            <Button size="sm" variant="secondary" onClick={() => rest.refetch()}>
              Check
            </Button>
          </CardHeader>
          <CardContent>
            <QueryState isLoading={rest.isLoading} error={rest.error}>
              {rest.data && (
                <div className="space-y-2 text-sm">
                  <Badge
                    variant={
                      rest.data.verdict === "yes"
                        ? "default"
                        : rest.data.verdict === "partial"
                          ? "secondary"
                          : "destructive"
                    }
                  >
                    {rest.data.verdict}
                  </Badge>
                  <p>{rest.data.message}</p>
                  <p className="text-muted-foreground">
                    Minimum work required: {rest.data.minimum_work_minutes}m
                  </p>
                  {rest.data.tasks_to_clear.length > 0 && (
                    <p className="text-muted-foreground">
                      Clear task IDs first: {rest.data.tasks_to_clear.join(", ")}
                    </p>
                  )}
                  <ConflictList conflicts={rest.data.conflicts_after_rest} />
                </div>
              )}
            </QueryState>
          </CardContent>
        </Card>

        {/* CALIBRATION */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Estimation calibration</CardTitle>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => calibration.refetch()}
            >
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            <QueryState
              isLoading={calibration.isLoading}
              error={calibration.error}
              isEmpty={!!calibration.data && calibration.data.length === 0}
              emptyLabel="No calibration data yet."
            >
              {calibration.data && (
                <ul className="divide-y border rounded-md text-sm">
                  {calibration.data.map((c, i) => (
                    <li key={i} className="p-3 flex items-center gap-2">
                      <span>{c.area_id === null ? "Global" : `Area ${c.area_id}`}</span>
                      <span className="ml-auto font-mono">
                        {c.ratio.toFixed(2)}× ({c.sample_count} samples)
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </QueryState>
          </CardContent>
        </Card>
      </div>
      )}

      <CompleteTaskDialog
        target={completeFor}
        onOpenChange={(o) => !o && setCompleteFor(null)}
        simple
      />
    </AppShell>
  );
}

function ConflictList({
  conflicts,
}: {
  conflicts: import("@/lib/lifeos-api").ScheduleConflict[];
}) {
  if (!conflicts?.length) return null;
  return (
    <div>
      <div className="text-xs text-muted-foreground mb-1">Conflicts</div>
      <ul className="space-y-1">
        {conflicts.map((c, i) => (
          <li key={i} className="text-xs border-l-2 border-destructive pl-2">
            <Badge variant="destructive" className="mr-2">
              {c.kind}
            </Badge>
            {formatMessageDates(c.message)}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function CompleteTaskDialog({
  target,
  onOpenChange,
  simple = false,
}: {
  target: { id: number; title: string } | null;
  onOpenChange: (open: boolean) => void;
  simple?: boolean;
}) {
  const qc = useQueryClient();
  const [actual, setActual] = useState<string>("");
  const [energyBefore, setEnergyBefore] = useState<string>("");
  const [energyAfter, setEnergyAfter] = useState<string>("");

  const mutation = useMutation({
    mutationFn: (body: CompleteTaskBody) => api.completeTask(target!.id, body),
    onSuccess: (res) => {
      toast.success(
        `Done. Observed ratio ${res.observed_ratio.toFixed(2)}×`,
      );
      qc.invalidateQueries({ queryKey: ["now"] });
      qc.invalidateQueries({ queryKey: qk.plan });
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: qk.calibration });
      onOpenChange(false);
      setActual("");
      setEnergyBefore("");
      setEnergyAfter("");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const submit = () => {
    if (simple) {
      mutation.mutate({});
      return;
    }
    const body: CompleteTaskBody = {};
    if (actual !== "") body.actual_minutes = Number(actual);
    if (energyBefore !== "") body.energy_before = Number(energyBefore);
    if (energyAfter !== "") body.energy_after = Number(energyAfter);
    mutation.mutate(body);
  };

  return (
    <Dialog open={!!target} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Complete task</DialogTitle>
        </DialogHeader>
        {target && (
          <div className="space-y-4">
            <div className="text-sm">{target.title}</div>
            {!simple && (
              <div className="grid gap-3">
                <div>
                  <Label htmlFor="actual">Actual minutes (optional)</Label>
                  <Input
                    id="actual"
                    type="number"
                    min={0}
                    value={actual}
                    onChange={(e) => setActual(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="eb">Energy before (0–1)</Label>
                    <Input
                      id="eb"
                      type="number"
                      min={0}
                      max={1}
                      step={0.1}
                      value={energyBefore}
                      onChange={(e) => setEnergyBefore(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="ea">Energy after (0–1)</Label>
                    <Input
                      id="ea"
                      type="number"
                      min={0}
                      max={1}
                      step={0.1}
                      value={energyAfter}
                      onChange={(e) => setEnergyAfter(e.target.value)}
                    />
                  </div>
                </div>
              </div>
            )}
            <DialogFooter>
              <Button variant="ghost" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button onClick={submit} disabled={mutation.isPending}>
                {mutation.isPending ? "Saving…" : "Complete"}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
