// Response of GET /health (backend: app/api/health.py HealthResponse).
export type Health = {
  status: string;
  swiggy_mode: string;
};
