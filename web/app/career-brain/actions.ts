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

export async function deleteSkill(id: string): Promise<Result> {
  return run((token) => api.deleteSkill(token, id));
}

export async function deleteExperience(id: string): Promise<Result> {
  return run((token) => api.deleteExperience(token, id));
}

export async function addEducation(_prev: unknown, formData: FormData): Promise<Result> {
  const institution = String(formData.get("institution") ?? "").trim();
  const credential = String(formData.get("credential") ?? "").trim();
  const field_of_study = String(formData.get("field_of_study") ?? "").trim() || undefined;
  const end_date = String(formData.get("end_date") ?? "").trim() || undefined;
  if (!institution || !credential) {
    return { ok: false, error: "Institution and credential are required." };
  }
  return run((token) => api.addEducation(token, { institution, credential, field_of_study, end_date }));
}

export async function deleteEducation(id: string): Promise<Result> {
  return run((token) => api.deleteEducation(token, id));
}

export async function addCertification(_prev: unknown, formData: FormData): Promise<Result> {
  const name = String(formData.get("name") ?? "").trim();
  const issuer = String(formData.get("issuer") ?? "").trim() || undefined;
  if (!name) return { ok: false, error: "Certification name is required." };
  return run((token) => api.addCertification(token, { name, issuer }));
}

export async function deleteCertification(id: string): Promise<Result> {
  return run((token) => api.deleteCertification(token, id));
}

export async function addProject(_prev: unknown, formData: FormData): Promise<Result> {
  const name = String(formData.get("name") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim();
  const url = String(formData.get("url") ?? "").trim() || undefined;
  if (!name) return { ok: false, error: "Project name is required." };
  return run((token) => api.addProject(token, { name, description, url }));
}

export async function deleteProject(id: string): Promise<Result> {
  return run((token) => api.deleteProject(token, id));
}

export async function addLanguage(_prev: unknown, formData: FormData): Promise<Result> {
  const name = String(formData.get("name") ?? "").trim();
  const proficiency = String(formData.get("proficiency") ?? "").trim() || undefined;
  if (!name) return { ok: false, error: "Language is required." };
  return run((token) => api.addLanguage(token, { name, proficiency }));
}

export async function deleteLanguage(id: string): Promise<Result> {
  return run((token) => api.deleteLanguage(token, id));
}

export async function addAward(_prev: unknown, formData: FormData): Promise<Result> {
  const title = String(formData.get("title") ?? "").trim();
  const issuer = String(formData.get("issuer") ?? "").trim() || undefined;
  if (!title) return { ok: false, error: "Award title is required." };
  return run((token) => api.addAward(token, { title, issuer }));
}

export async function deleteAward(id: string): Promise<Result> {
  return run((token) => api.deleteAward(token, id));
}
