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

export type RankedOffer = {
  company_name: string;
  job_title: string;
  base_salary: number;
  opportunity_value: number;
};

export type Contact = {
  id: string;
  name: string;
  role: string;
  organization_name: string;
  stage: string | null;
};

export type Prospect = {
  id: string;
  name: string;
  website: string;
  industry: string;
  stage: string | null;
};

export type PlanInfo = {
  tier: string;
  name: string;
  monthly_price_usd: number;
  features: string[];
  is_current: boolean;
  checkout_url: string | null;
};

export type Billing = { current_tier: string; status: string; plans: PlanInfo[] };

export type AiStatus = { has_key: boolean; model: string };

export type AutopilotRun = {
  id: string;
  ran_at: string;
  discovered: number;
  submitted: number;
  qualified_total: number;
  outcomes: { job_title: string; company_name: string; submitted: boolean; reason: string }[];
};

export type Customer = {
  name: string;
  email: string;
  role: string;
  workspace_id: string;
  plan: string;
  status: string;
  joined: string;
};

export type AdminOverview = {
  accounts: number;
  paying_workspaces: number;
  mrr: number;
  customers: Customer[];
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
  searchJobs: (
    token: string,
    body: { keywords: string[]; remote_only: boolean; limit?: number },
  ) => request<{ discovered: number; qualified: number }>("/opportunities/search", {
    token,
    method: "POST",
    body,
  }),
  generatePackage: (token: string, job_url: string) =>
    request<{ resume_text: string; cover_letter: string; ai_used: boolean }>(
      "/opportunities/generate",
      { token, method: "POST", body: { job_url } },
    ),
  aiStatus: (token: string) => request<AiStatus>("/settings/ai", { token }),
  setAiKey: (token: string, api_key: string) =>
    request<AiStatus>("/settings/ai", { token, method: "PUT", body: { api_key } }),
  deleteAiKey: (token: string) =>
    request<AiStatus>("/settings/ai", { token, method: "DELETE" }),
  offers: (token: string) => request<RankedOffer[]>("/offers", { token }),
  addOffer: (token: string, body: Record<string, unknown>) =>
    request<RankedOffer[]>("/offers", { token, method: "POST", body }),
  contacts: (token: string) => request<Contact[]>("/contacts", { token }),
  addContact: (
    token: string,
    body: { name: string; role: string; organization_name: string; email: string | null },
  ) => request<Contact>("/contacts", { token, method: "POST", body }),
  prospects: (token: string) => request<Prospect[]>("/freelance/prospects", { token }),
  addProspect: (token: string, body: { name: string; website: string; industry: string }) =>
    request<Prospect>("/freelance/prospects", { token, method: "POST", body }),
  billing: (token: string) => request<Billing>("/billing", { token }),
  autopilotRuns: (token: string) => request<AutopilotRun[]>("/autopilot/runs", { token }),
  adminOverview: (token: string) => request<AdminOverview>("/admin/overview", { token }),
  adminActivate: (token: string, body: { workspace_id: string; tier: string }) =>
    request<AdminOverview>("/admin/activate", { token, method: "POST", body }),
};
