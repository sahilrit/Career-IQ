import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { job_url } = (await request.json()) as { job_url?: string };
  if (!job_url) return NextResponse.json({ error: "missing job_url" }, { status: 400 });
  try {
    const pkg = await api.generatePackage(token, job_url);
    return NextResponse.json(pkg);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Generation failed.";
    return NextResponse.json({ error: message }, { status });
  }
}
