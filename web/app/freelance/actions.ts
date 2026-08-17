"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

export async function addProspect(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const name = String(formData.get("name") ?? "").trim();
  const website = String(formData.get("website") ?? "").trim();
  if (!name || !website) return { ok: false, error: "Name and website are required." };
  try {
    await api.addProspect(token, {
      name,
      website,
      industry: String(formData.get("industry") ?? "").trim(),
    });
    revalidatePath("/freelance");
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof ApiError ? error.message : "Failed to add prospect.",
    };
  }
}
