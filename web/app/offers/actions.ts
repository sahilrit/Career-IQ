"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

export async function addOffer(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const company_name = String(formData.get("company_name") ?? "").trim();
  const job_title = String(formData.get("job_title") ?? "").trim();
  if (!company_name || !job_title) return { ok: false, error: "Company and title are required." };
  const num = (key: string) => Number(formData.get(key) ?? 0) || 0;
  try {
    await api.addOffer(token, {
      company_name,
      job_title,
      base_salary: num("base_salary"),
      bonus: num("bonus"),
      equity_value: num("equity_value"),
      benefits_value: num("benefits_value"),
      stability_score: num("stability_score") || 3,
      growth_score: num("growth_score") || 3,
      reputation_score: num("reputation_score") || 3,
    });
    revalidatePath("/offers");
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof ApiError ? error.message : "Failed to add offer." };
  }
}
