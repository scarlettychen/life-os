import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api, qk } from "@/lib/lifeos-api";
import { AppShell } from "@/components/lifeos/app-shell";
import { QueryState } from "@/components/lifeos/query-state";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/calibrate")({
  component: CalibratePage,
});

function CalibratePage() {
  const c = useQuery({
    queryKey: qk.calibration,
    queryFn: () => api.getCalibration(),
  });
  const areas = useQuery({ queryKey: qk.areas, queryFn: () => api.listAreas() });
  const areaMap = new Map((areas.data ?? []).map((a) => [a.id, a.name]));

  return (
    <AppShell>
      <div className="flex items-center gap-2 mb-6">
        <h1 className="text-2xl font-semibold mr-auto">Estimation calibration</h1>
        <Button variant="outline" onClick={() => c.refetch()}>Refresh</Button>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Ratios &gt; 1 mean tasks take longer than estimated. Updates automatically as
        you complete tasks.
      </p>
      <QueryState
        isLoading={c.isLoading}
        error={c.error}
        isEmpty={!!c.data && c.data.length === 0}
        emptyLabel="No calibration data yet — complete some tasks first."
      >
        {c.data && (
          <ul className="divide-y border rounded-md text-sm">
            {c.data.map((row, i) => (
              <li key={i} className="p-3 flex items-center gap-2">
                <span className="font-medium">
                  {row.area_id === null
                    ? "Global (fallback)"
                    : (areaMap.get(row.area_id) ?? `Area ${row.area_id}`)}
                </span>
                <span className="ml-auto font-mono">
                  {row.ratio.toFixed(2)}× · {row.sample_count} samples
                </span>
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </AppShell>
  );
}
