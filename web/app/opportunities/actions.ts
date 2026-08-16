"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type SearchResult =
  | { ok: true; discovered: number; qualified: number }
  | { ok: false; error: string };

export async function runSearch(_prev: unknown, formData: FormData): Promise<SearchResult> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const keywords = String(formData.get("keywords") ?? "")
    .split(",")
    .map((k) => k.trim())
    .filter(Boolean);
  if (keywords.length === 0) return { ok: false, error: "Enter at least one keyword." };
  const remote_only = formData.get("remote_only") === "on";
  try {
    const summary = await api.searchJobs(token, { keywords, remote_only });
    revalidatePath("/opportunities");
    revalidatePath("/dashboard");
    return { ok: true, ...summary };
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return { ok: false, error: "Create your Career Brain first." };
    }
    return {
      ok: false,
      error: error instanceof ApiError ? error.message : "Search failed — is the API running?",
    };
  }
}
