"use server";

import { revalidatePath } from "next/cache";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

type Result = { ok: true } | { ok: false; error: string };

function fail(error: unknown): Result {
  return { ok: false, error: error instanceof ApiError ? error.message : "Something went wrong." };
}

export async function addClient(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const name = String(formData.get("name") ?? "").trim();
  if (!name) return { ok: false, error: "Client name is required." };
  try {
    await api.addClient(token, name);
    revalidatePath("/clients");
    return { ok: true };
  } catch (error) {
    return fail(error);
  }
}

export async function addContract(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const client_id = String(formData.get("client_id") ?? "");
  const title = String(formData.get("title") ?? "").trim();
  const rate = Number(formData.get("rate") ?? 0);
  const start_date = String(formData.get("start_date") ?? "");
  if (!client_id || !title || !start_date) {
    return { ok: false, error: "Title and start date are required." };
  }
  try {
    await api.addContract(token, { client_id, title, rate, start_date });
    revalidatePath("/clients");
    return { ok: true };
  } catch (error) {
    return fail(error);
  }
}

export async function addInvoice(_prev: unknown, formData: FormData): Promise<Result> {
  const token = getToken();
  if (!token) return { ok: false, error: "not authenticated" };
  const contract_id = String(formData.get("contract_id") ?? "");
  const amount = Number(formData.get("amount") ?? 0);
  const due_date = String(formData.get("due_date") ?? "");
  if (!contract_id || !amount || !due_date) {
    return { ok: false, error: "Amount and due date are required." };
  }
  try {
    await api.addInvoice(token, { contract_id, amount, due_date });
    revalidatePath("/clients");
    return { ok: true };
  } catch (error) {
    return fail(error);
  }
}
