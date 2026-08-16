"use server";

// Server actions for Career Brain mutations. Each reads the httpOnly
// session cookie and calls the API server-side, then revalidates the page.
// The bearer token never reaches the client.

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

function requireToken(): string {
  const token = getToken();
  if (!token) throw new Error("not authenticated");
  return token;
}

async function run(action: (token: string) => Promise<unknown>): Promise<Result> {
  try {
    await action(requireToken());
    revalidatePath("/career-brain");
    revalidatePath("/dashboard");
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof ApiError ? error.message : "Something went wrong." };
  }
}

export async function createBrain(_prev: unknown, formData: FormData): Promise<Result> {
  const full_name = String(formData.get("full_name") ?? "").trim();
  const email = String(formData.get("email") ?? "").trim();
  if (!full_name || !email) return { ok: false, error: "Name and email are required." };
  return run((token) => api.createBrain(token, { full_name, email }));
}

export async function updateSummary(_prev: unknown, formData: FormData): Promise<Result> {
  const summary = String(formData.get("summary") ?? "");
  return run((token) => api.updateSummary(token, summary));
}

export async function addSkill(_prev: unknown, formData: FormData): Promise<Result> {
  const name = String(formData.get("name") ?? "").trim();
  if (!name) return { ok: false, error: "Skill name is required." };
  return run((token) => api.addSkill(token, { name }));
}

export async function addExperience(_prev: unknown, formData: FormData): Promise<Result> {
  const company_name = String(formData.get("company_name") ?? "").trim();
  const title = String(formData.get("title") ?? "").trim();
  const start_date = String(formData.get("start_date") ?? "").trim();
  if (!company_name || !title || !start_date) {
    return { ok: false, error: "Company, title, and start date are required." };
  }
  return run((token) => api.addExperience(token, { company_name, title, start_date }));
}
