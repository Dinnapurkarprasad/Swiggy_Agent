// TanStack Query hook for the health check. Components use this, never lib/api/ directly.
import { useQuery } from "@tanstack/react-query";

import { getHealth } from "@/lib/api/health";

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: getHealth });
}
