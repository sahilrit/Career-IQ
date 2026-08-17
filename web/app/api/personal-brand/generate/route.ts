import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { project_id } = (await request.json()) as { project_id?: string };
  if (!project_id) return NextResponse.json({ error: "pick a project" }, { status: 400 });
  try {
    return NextResponse.json(await api.brandGenerate(token, project_id));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't generate content.";
    return NextResponse.json({ error: message }, { status });
  }
}
