import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { api, ApiError } from "@/lib/api";
import { getToken, SESSION_COOKIE } from "@/lib/session";

export async function DELETE() {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  try {
    const result = await api.deleteAccount(token);
    cookies().delete(SESSION_COOKIE);
    return NextResponse.json(result);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't delete account.";
    return NextResponse.json({ error: message }, { status });
  }
}
