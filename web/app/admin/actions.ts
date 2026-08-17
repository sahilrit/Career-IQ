"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

export async function activatePlan(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const workspace_id = String(formData.get("workspace_id") ?? "").trim();
  const tier = String(formData.get("tier") ?? "").trim();
  if (!workspace_id || !tier) return { ok: false, error: "Pick a workspace and tier." };
  try {
    await api.adminActivate(token, { workspace_id, tier });
    revalidatePath("/admin");
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof ApiError ? error.message : "Activation failed.",
    };
  }
}
