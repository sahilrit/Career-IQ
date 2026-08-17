"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

export async function addContact(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const name = String(formData.get("name") ?? "").trim();
  if (!name) return { ok: false, error: "Name is required." };
  try {
    await api.addContact(token, {
      name,
      role: String(formData.get("role") ?? "prospect"),
      organization_name: String(formData.get("organization_name") ?? "").trim(),
      email: String(formData.get("email") ?? "").trim() || null,
    });
    revalidatePath("/network");
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof ApiError ? error.message : "Failed to add contact.",
    };
  }
}
