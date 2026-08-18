import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { to, note } = (await request.json()) as { to?: string; note?: string };
  if (!to) return NextResponse.json({ error: "missing target status" }, { status: 400 });
  try {
    const application = await api.advanceApplication(token, params.id, to, note ?? "");
    return NextResponse.json(application);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Update failed.";
    return NextResponse.json({ error: message }, { status });
  }
}
