import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { keywords, remote_only } = (await request.json()) as {
    keywords?: string[];
    remote_only?: boolean;
  };
  try {
    const saved = await api.createSavedSearch(token, keywords ?? [], remote_only ?? true);
    return NextResponse.json(saved);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't save.";
    return NextResponse.json({ error: message }, { status });
  }
}
