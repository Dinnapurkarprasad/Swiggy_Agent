// Low-level fetch helper for the FastAPI backend, reached through the /api proxy in
// next.config.ts. Only files in lib/api/ should call this.

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(`API error ${status}`);
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    credentials: "include", // send the party_session login cookie
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body?.detail ?? body);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
