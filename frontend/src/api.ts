// Cienki klient API. Bledy backendu (FastAPI `detail`) sa zamieniane na czytelny tekst po polsku.

export class ApiError extends Error {}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = data && typeof data === "object" && "detail" in data ? String((data as { detail: unknown }).detail) : res.statusText;
    throw new ApiError(detail);
  }
  return data as T;
}

export const api = {
  get: <T,>(p: string) => request<T>("GET", p),
  post: <T,>(p: string, b?: unknown) => request<T>("POST", p, b),
  put: <T,>(p: string, b?: unknown) => request<T>("PUT", p, b),
  del: <T,>(p: string) => request<T>("DELETE", p),
};

export type Project = { id: string; name: string; root_path: string; created_at: string; jobs?: number; variants?: number };
export type Job = { id: string; kind: string; state: string; error: string | null; created_at: string; updated_at: string };
export type JobEvent = { event: string; detail: Record<string, unknown>; at: string };
export type Shot = { index: number; start_s: number; end_s: number; frames: number; prompt: string };
export type PlanResult = { shots: Shot[]; warnings: string[] };
export type Command = { cwd: string; argv: string[]; env: Record<string, string>; script: string; expected_output?: string; warnings: string[]; errors: string[] };
export type PrepareResult = { job: Job; command: Command };
export type Variant = { id: string; review_status: string; created_at: string; kind: string | null; abs_path: string | null; frames: number | null; fps: number | null };
export type Clip = { clip_id: string; source_path: string; source_in: number; source_out: number; timeline_start: number };
export type Status = {
  llm: { runtime: string; status: string; detail?: string; models?: string[] };
  vram: { status: string; gpus?: { gpu: number; total_b: number; used_b: number }[]; detail?: string };
  render: { allowed: boolean; reason: string };
  render_enabled: boolean;
  note: string;
};
export type PromptFile = { name: string; rel_path: string };
