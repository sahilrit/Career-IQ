"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

export async function addIncome(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const source = String(formData.get("source") ?? "");
  const source_name = String(formData.get("source_name") ?? "").trim();
  const amount = Number(formData.get("amount") ?? 0);
  const received_date = String(formData.get("received_date") ?? "");
  if (!source || !source_name || !amount || !received_date) {
    return { ok: false, error: "All fields are required." };
  }
  try {
    await api.addIncome(token, { source, source_name, amount, received_date });
    revalidatePath("/finance");
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof ApiError ? error.message : "Something went wrong." };
  }
}
