import { Link, useRouterState } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api, qk } from "@/lib/lifeos-api";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/tasks", label: "Tasks" },
  { to: "/plan", label: "Plan" },
  { to: "/areas", label: "Areas" },
  { to: "/goals", label: "Goals" },
  { to: "/projects", label: "Projects" },
  { to: "/rest", label: "Rest" },
  { to: "/calibrate", label: "Calibration" },
  { to: "/review", label: "Review" },
  { to: "/brief", label: "Brief" },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const health = useQuery({
    queryKey: qk.health,
    queryFn: () => api.health(),
    retry: false,
    refetchInterval: 30_000,
  });

  const ok = health.data?.status === "ok";
  const badgeColor = health.isLoading
    ? "bg-muted text-muted-foreground"
    : ok
      ? "bg-green-500/15 text-green-700 dark:text-green-400"
      : "bg-destructive/15 text-destructive";

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="border-b">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center gap-4">
          <div className="font-semibold">LifeOS</div>
          <nav className="flex flex-wrap gap-1 text-sm">
            {NAV.map((n) => (
              <Link
                key={n.to}
                to={n.to}
                className={cn(
                  "px-3 py-1.5 rounded-md hover:bg-accent",
                  pathname === n.to && "bg-accent font-medium",
                )}
              >
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2 text-xs">
            <span className={cn("px-2 py-1 rounded-full", badgeColor)}>
              {health.isLoading
                ? "checking backend…"
                : ok
                  ? "backend ok"
                  : "backend unreachable"}
            </span>
            <span className="text-muted-foreground hidden sm:inline">
              {api.apiUrl}
            </span>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}
