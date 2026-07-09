import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api, type BriefResult } from "@/lib/lifeos-api";
import { AppShell } from "@/components/lifeos/app-shell";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export const Route = createFileRoute("/brief")({
  component: BriefPage,
});

function BriefPage() {
  const [result, setResult] = useState<BriefResult | null>(null);

  const preview = useMutation({
    mutationFn: () => api.previewBrief(),
    onSuccess: (r) => { setResult(r); toast.success("Preview ready"); },
    onError: (e: Error) => toast.error(e.message),
  });
  const write = useMutation({
    mutationFn: () => api.writeBrief(),
    onSuccess: (r) => { setResult(r); toast.success(`Written to ${r.path}`); },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <AppShell>
      <h1 className="text-2xl font-semibold mb-6">Daily brief</h1>
      <div className="flex gap-3 mb-4">
        <Button variant="secondary" onClick={() => preview.mutate()} disabled={preview.isPending}>
          {preview.isPending ? "Loading…" : "Preview brief"}
        </Button>
        <Button onClick={() => write.mutate()} disabled={write.isPending}>
          {write.isPending ? "Writing…" : "Write to vault"}
        </Button>
      </div>
      {result && (
        <div className="space-y-3">
          <Alert>
            <AlertTitle>{result.written ? "Written" : "Preview"}</AlertTitle>
            <AlertDescription>{result.path}</AlertDescription>
          </Alert>
          <pre className="border rounded-md p-4 text-xs whitespace-pre-wrap bg-muted/30 overflow-auto max-h-[70vh]">
            {result.content}
          </pre>
        </div>
      )}
    </AppShell>
  );
}
