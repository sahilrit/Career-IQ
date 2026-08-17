"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

export async function createExperiment(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const experiment_type = String(formData.get("experiment_type") ?? "");
  const name = String(formData.get("name") ?? "").trim();
  if (!experiment_type || !name) return { ok: false, error: "Type and name are required." };
  try {
    await api.createExperiment(token, { experiment_type, name });
    revalidatePath("/learning");
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof ApiError ? error.message : "Something went wrong." };
  }
}

export async function addVariant(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const experiment_id = String(formData.get("experiment_id") ?? "");
  const label = String(formData.get("label") ?? "").trim();
  if (!experiment_id || !label) return { ok: false, error: "Label is required." };
  try {
    await api.addVariant(token, { experiment_id, label });
    revalidatePath("/learning");
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof ApiError ? error.message : "Something went wrong." };
  }
}

export async function recordOutcome(formData: FormData): Promise<void> {
  const token = getToken();
  if (!token) return;
  const variant_id = String(formData.get("variant_id") ?? "");
  const outcome_type = String(formData.get("outcome_type") ?? "");
  if (!variant_id || !outcome_type) return;
  try {
    await api.recordOutcome(token, { variant_id, outcome_type });
    revalidatePath("/learning");
  } catch {
    // best-effort; the board re-renders on next load
  }
}
