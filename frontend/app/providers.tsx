"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

// TanStack Query caches API responses and handles loading/error states and polling.
// One QueryClient per browser tab, created once (useState keeps it across re-renders).
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 10_000 } } }),
  );
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
