"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

export async function recordPerformance(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const category = String(formData.get("category") ?? "");
  const metric_name = String(formData.get("metric_name") ?? "").trim();
  const value = Number(formData.get("value") ?? 0);
  if (!category || !metric_name) return { ok: false, error: "Category and metric are required." };
  try {
    await api.ceoRecord(token, { category, metric_name, value });
    revalidatePath("/ceo");
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof ApiError ? error.message : "Something went wrong." };
  }
}

export async function computeAllocation(): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  try {
    await api.ceoCompute(token);
    revalidatePath("/ceo");
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof ApiError ? error.message : "Something went wrong." };
  }
}
