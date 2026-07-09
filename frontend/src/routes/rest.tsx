import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, qk } from "@/lib/lifeos-api";
import { AppShell } from "@/components/lifeos/app-shell";
import { QueryState } from "@/components/lifeos/query-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/rest")({
  component: RestPage,
});

function RestPage() {
  const [hours, setHours] = useState(3);
  const rest = useQuery({
    queryKey: qk.rest(hours),
    queryFn: () => api.getRest(hours),
  });

  return (
    <AppShell>
      <h1 className="text-2xl font-semibold mb-6">Rest check</h1>
      <div className="flex items-end gap-3 mb-4">
        <div>
          <Label htmlFor="h">Hours of rest</Label>
          <Input
            id="h"
            type="number"
            min={0.5}
            step={0.5}
            value={hours}
            onChange={(e) => setHours(Math.max(0.5, Number(e.target.value) || 0.5))}
            className="w-32"
          />
        </div>
        <Button onClick={() => rest.refetch()}>Check</Button>
      </div>
      <QueryState isLoading={rest.isLoading} error={rest.error}>
        {rest.data && (
          <div className="space-y-3 text-sm">
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
                Tasks to clear first: {rest.data.tasks_to_clear.join(", ")}
              </p>
            )}
            {rest.data.conflicts_after_rest.length > 0 && (
              <div>
                <div className="text-xs text-muted-foreground mb-1">
                  Conflicts if you rest
                </div>
                <ul className="space-y-1">
                  {rest.data.conflicts_after_rest.map((c, i) => (
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
    </AppShell>
  );
}
