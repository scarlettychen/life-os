import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, qk } from "@/lib/lifeos-api";
import { AppShell } from "@/components/lifeos/app-shell";
import { QueryState } from "@/components/lifeos/query-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CompleteTaskDialog } from "@/routes/index";

export const Route = createFileRoute("/plan")({
  component: PlanPage,
});

function PlanPage() {
  const plan = useQuery({ queryKey: qk.plan, queryFn: () => api.getPlan() });
  const [completeFor, setCompleteFor] = useState<{ id: number; title: string } | null>(null);

  return (
    <AppShell>
      <div className="flex items-center gap-2 mb-6">
        <h1 className="text-2xl font-semibold mr-auto">Today's plan</h1>
        <Button variant="outline" onClick={() => plan.refetch()}>Refresh plan</Button>
      </div>
      <QueryState
        isLoading={plan.isLoading}
        error={plan.error}
        isEmpty={!!plan.data && plan.data.blocks.length === 0}
        emptyLabel="No blocks scheduled."
      >
        {plan.data && (
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Scheduled {plan.data.total_scheduled_minutes}m · Deep work{" "}
              {plan.data.deep_work_minutes}m · Unscheduled task IDs:{" "}
              {plan.data.unscheduled_task_ids.join(", ") || "none"}
            </div>
            <ul className="divide-y border rounded-md">
              {plan.data.blocks.map((b, i) => (
                <li key={i} className="p-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs text-muted-foreground w-28">
                      {fmt(b.start)}–{fmt(b.end)}
                    </span>
                    <span className="font-medium">{b.title}</span>
                    <Badge variant="outline">{b.kind}</Badge>
                    <Badge variant="secondary">{b.status}</Badge>
                    <span className="ml-auto text-xs text-muted-foreground">
                      fit {b.energy_fit.toFixed(2)}
                    </span>
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
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {b.rationale}
                  </div>
                </li>
              ))}
            </ul>
            {plan.data.conflicts.length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-1">Conflicts</div>
                <ul className="space-y-1">
                  {plan.data.conflicts.map((c, i) => (
                    <li key={i} className="text-xs border-l-2 border-destructive pl-2">
                      <Badge variant="destructive" className="mr-2">{c.kind}</Badge>
                      {c.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </QueryState>
      <CompleteTaskDialog
        target={completeFor}
        onOpenChange={(o) => !o && setCompleteFor(null)}
      />
    </AppShell>
  );
}

function fmt(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
