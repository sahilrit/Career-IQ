// Typed client for careeros-api. Server components/route handlers call
// these with the caller's bearer token (read from the httpOnly cookie);
// the token never touches client-side JS.

export const API_BASE =
  process.env.CAREEROS_API_BASE ?? "http://localhost:8000";

export type Account = {
  user_id: string;
  email: string;
  full_name: string;
  workspace_id: string;
  role: string;
  is_admin: boolean;
};

export type Application = {
  id: string;
  job_title: string;
  company_name: string;
  status: string;
  match_score: number | null;
  job_url: string | null;
};

export type CareerBrain = {
  identity: {
    full_name: string;
    headline: string;
    summary: string;
    email: string;
  };
  skills: { name: string; proficiency: number }[];
  experiences: { title: string; company_name: string }[];
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  { token, method = "GET", body }: { token?: string; method?: string; body?: unknown } = {},
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export const api = {
  signup: (body: { email: string; password: string; full_name: string }) =>
    request<{ token: string }>("/auth/signup", { method: "POST", body }),
  login: (body: { email: string; password: string }) =>
    request<{ token: string }>("/auth/login", { method: "POST", body }),
  me: (token: string) => request<Account>("/auth/me", { token }),
  brain: (token: string) => request<CareerBrain>("/brain", { token }),
  applications: (token: string) => request<Application[]>("/applications", { token }),
  createBrain: (token: string, body: { full_name: string; email: string }) =>
    request<CareerBrain>("/brain", { token, method: "POST", body }),
  updateSummary: (token: string, summary: string) =>
    request<CareerBrain>("/brain/summary", { token, method: "PATCH", body: { summary } }),
  addSkill: (token: string, body: { name: string; proficiency?: number }) =>
    request<CareerBrain>("/brain/skills", { token, method: "POST", body }),
  addExperience: (
    token: string,
    body: { company_name: string; title: string; start_date: string; description?: string },
  ) => request<CareerBrain>("/brain/experience", { token, method: "POST", body }),
};
