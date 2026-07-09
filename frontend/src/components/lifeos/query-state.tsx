import { ApiError } from "@/lib/lifeos-api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function QueryState({
  isLoading,
  error,
  isEmpty,
  emptyLabel = "Nothing here yet.",
  children,
}: {
  isLoading: boolean;
  error: unknown;
  isEmpty?: boolean;
  emptyLabel?: string;
  children: React.ReactNode;
}) {
  if (isLoading) {
    return (
      <div className="text-sm text-muted-foreground py-6">Loading…</div>
    );
  }
  if (error) {
    const msg =
      error instanceof ApiError
        ? error.message
        : error instanceof Error
          ? error.message
          : "Unknown error";
    return (
      <Alert variant="destructive" className="my-4">
        <AlertTitle>Request failed</AlertTitle>
        <AlertDescription>{msg}</AlertDescription>
      </Alert>
    );
  }
  if (isEmpty) {
    return (
      <div className="text-sm text-muted-foreground py-6">{emptyLabel}</div>
    );
  }
  return <>{children}</>;
}
