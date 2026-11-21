"use client";

import { useHealth } from "@/lib/mutations/health";

// Temporary: proves the /api proxy reaches FastAPI. Remove once the real landing page exists.
export function BackendStatus() {
  const { data, isPending, isError } = useHealth();

  if (isPending) return <p className="text-sm text-muted-foreground">Checking backend…</p>;
  if (isError) return <p className="text-sm text-destructive">Backend unreachable</p>;
  return (
    <p className="text-sm text-muted-foreground">
      Backend: {data.status} · Swiggy mode: {data.swiggy_mode}
    </p>
  );
}
