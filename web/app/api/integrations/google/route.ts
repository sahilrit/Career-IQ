import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function DELETE() {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  try {
    return NextResponse.json(await api.googleDisconnect(token));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    return NextResponse.json({ error: "Couldn't disconnect." }, { status });
  }
}
