// Pure API call: GET /health. No React here.
import { request } from "@/lib/http";
import type { Health } from "@/lib/types/health";

export function getHealth(): Promise<Health> {
  return request<Health>("/health");
}
