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

export type StatusChange = { status: string; changed_at: string; note: string };
export type Application = {
  id: string;
  job_title: string;
  company_name: string;
  status: string;
  match_score: number | null;
  job_url: string | null;
  notes?: string;
  history?: StatusChange[];
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
  email: string | null;
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

export type OnboardingStep = { key: string; label: string; href: string; done: boolean };
export type Onboarding = { steps: OnboardingStep[]; complete: boolean };

export type GoogleStatus = { configured: boolean; connected: boolean; email: string | null };
export type CalendarEvent = { summary: string; start: string; html_link: string };

export type StarPrompt = { question: string; achievement_description: string; metric: string | null };
export type InterviewPrep = {
  questions: {
    role_specific: string[];
    technical: string[];
    company_specific: string[];
    star_prompts: StarPrompt[];
  };
  briefing: {
    company_name: string;
    job_title: string;
    strongest_achievements: string[];
    questions_to_ask: string[];
    compensation_strategy: string;
    things_to_avoid: string[];
  };
  briefing_text: string;
};

export type BrandProject = { id: string; name: string };
export type BrandContent = {
  case_study: { title: string; problem: string; approach: string; result: string };
  linkedin: string;
  x_thread: string[];
  portfolio: string;
  blog: string;
};

export type ClientContract = {
  id: string;
  title: string;
  rate: number;
  status: string;
  outstanding: number;
};
export type ClientRow = {
  id: string;
  name: string;
  lifecycle_stage: string | null;
  contracts: ClientContract[];
};

export type AllocationPlan = {
  allocations: Record<string, number>;
  generated_at: string;
  disclaimer: string;
} | null;
export type CeoOverview = { latest: AllocationPlan; history: AllocationPlan[] };

export type VariantRow = {
  id: string;
  label: string;
  sent: number;
  responses: number;
  response_rate: number | null;
};
export type ExperimentRow = {
  id: string;
  name: string;
  type: string;
  status: string;
  variants: VariantRow[];
  winner: string | null;
};

export type IncomeRecord = {
  id: string;
  source: string;
  source_name: string;
  amount: number;
  received_date: string;
};
export type FinanceOverview = {
  records: IncomeRecord[];
  total: number;
  monthly: { year: number; month: number; total: number }[];
  trend: string | null;
};

export type RankedSubject = {
  subject: string;
  combined_score: number;
  supporting_signal_count: number;
  sources: string[];
};
export type CareerIntel = {
  direction_summary: string;
  recommendations: Record<string, RankedSubject[]>;
};

export type PitchFinding = { category: string; detail: string; recommendation: string };
export type PitchRoi = {
  current_monthly_revenue: number;
  assumed_uplift_pct: number;
  projected_additional_monthly_revenue: number;
  projected_additional_annual_revenue: number;
  disclaimer: string;
} | null;
export type PitchKit = {
  findings: PitchFinding[];
  roi: PitchRoi;
  email: string;
  linkedin_message: string;
  loom_script: string;
  proposal: string;
  ai_used: boolean;
  ai_error: string | null;
  pdf_base64: string;
};
export type PitchKitInput = {
  company_name: string;
  website: string;
  industry: string;
  monthly_visitors?: number | null;
  conversion_rate?: number | null;
  average_order_value?: number | null;
  ads: { headline: string; body_text: string; cta: string; landing_page_url: string }[];
};

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
  onboarding: (token: string) => request<Onboarding>("/onboarding", { token }),
  googleStatus: (token: string) => request<GoogleStatus>("/integrations/google", { token }),
  googleAuthUrl: (token: string) =>
    request<{ url: string }>("/integrations/google/auth-url", { token }),
  googleConnect: (token: string, code: string) =>
    request<{ connected: boolean; email: string }>("/integrations/google/connect", {
      token,
      method: "POST",
      body: { code },
    }),
  googleDisconnect: (token: string) =>
    request<{ connected: boolean }>("/integrations/google", { token, method: "DELETE" }),
  gmailSend: (token: string, body: { to: string; subject: string; body: string }) =>
    request<{ sent: boolean }>("/integrations/gmail/send", { token, method: "POST", body }),
  calendarEvents: (token: string) =>
    request<CalendarEvent[]>("/integrations/calendar/events", { token }),
  calendarCreate: (
    token: string,
    body: { summary: string; start_iso: string; end_iso: string; attendees: string[] },
  ) =>
    request<{ id: string; html_link: string }>("/integrations/calendar/events", {
      token,
      method: "POST",
      body,
    }),
  resetRequest: (email: string) =>
    request<{ message: string }>("/auth/reset/request", { method: "POST", body: { email } }),
  resetConfirm: (token: string, new_password: string) =>
    request<{ message: string }>("/auth/reset/confirm", {
      method: "POST",
      body: { token, new_password },
    }),
  brain: (token: string) => request<CareerBrain>("/brain", { token }),
  applications: (token: string) => request<Application[]>("/applications", { token }),
  advanceApplication: (token: string, id: string, to: string, note = "") =>
    request<Application>(`/applications/${id}/status`, {
      token,
      method: "POST",
      body: { to, note },
    }),
  updateApplicationNotes: (token: string, id: string, notes: string) =>
    request<Application>(`/applications/${id}`, { token, method: "PATCH", body: { notes } }),
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
    request<{
      resume_text: string;
      cover_letter: string;
      ai_used: boolean;
      ai_error: string | null;
    }>("/opportunities/generate", { token, method: "POST", body: { job_url } }),
  aiStatus: (token: string) => request<AiStatus>("/settings/ai", { token }),
  setAiKey: (token: string, api_key: string, model: string) =>
    request<AiStatus>("/settings/ai", { token, method: "PUT", body: { api_key, model } }),
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

  interviewPrep: (
    token: string,
    body: { job_title: string; company_name: string; job_description: string },
  ) => request<InterviewPrep>("/interview/prep", { token, method: "POST", body }),

  brandProjects: (token: string) => request<BrandProject[]>("/personal-brand/projects", { token }),
  brandGenerate: (token: string, project_id: string) =>
    request<BrandContent>("/personal-brand/generate", {
      token,
      method: "POST",
      body: { project_id },
    }),

  clients: (token: string) => request<ClientRow[]>("/clients", { token }),
  addClient: (token: string, name: string) =>
    request<{ id: string; name: string }>("/clients", { token, method: "POST", body: { name } }),
  addContract: (
    token: string,
    body: { client_id: string; title: string; rate: number; start_date: string },
  ) => request<{ id: string }>("/clients/contracts", { token, method: "POST", body }),
  addInvoice: (token: string, body: { contract_id: string; amount: number; due_date: string }) =>
    request<{ id: string }>("/clients/invoices", { token, method: "POST", body }),

  ceo: (token: string) => request<CeoOverview>("/ceo", { token }),
  ceoRecord: (token: string, body: { category: string; metric_name: string; value: number }) =>
    request<{ ok: boolean }>("/ceo/performance", { token, method: "POST", body }),
  ceoCompute: (token: string) =>
    request<AllocationPlan>("/ceo/compute", { token, method: "POST", body: {} }),

  experiments: (token: string) => request<ExperimentRow[]>("/learning", { token }),
  createExperiment: (token: string, body: { experiment_type: string; name: string }) =>
    request<{ id: string }>("/learning/experiments", { token, method: "POST", body }),
  addVariant: (token: string, body: { experiment_id: string; label: string }) =>
    request<{ id: string }>("/learning/variants", { token, method: "POST", body }),
  recordOutcome: (token: string, body: { variant_id: string; outcome_type: string }) =>
    request<{ ok: boolean }>("/learning/outcomes", { token, method: "POST", body }),

  finance: (token: string) => request<FinanceOverview>("/finance/income", { token }),
  addIncome: (
    token: string,
    body: {
      source: string;
      source_name: string;
      amount: number;
      received_date: string;
      hours_worked?: number | null;
    },
  ) => request<{ id: string }>("/finance/income", { token, method: "POST", body }),

  pitchKit: (token: string, body: PitchKitInput) =>
    request<PitchKit>("/audit/pitch-kit", { token, method: "POST", body }),

  careerIntel: (token: string) => request<CareerIntel>("/career-intel", { token }),
  addSignal: (token: string, body: { category: string; subject: string; score: number }) =>
    request<{ ok: boolean }>("/career-intel/signals", { token, method: "POST", body }),
};
