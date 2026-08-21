import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as {
    role: string;
    level?: string | null;
    anchor_salary?: number | null;
  };
  try {
    return NextResponse.json(await api.benchmark(token, body));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't estimate.";
    return NextResponse.json({ error: message }, { status });
  }
}
