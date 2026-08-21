import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as {
    kind: string;
    target_role?: string;
    send?: boolean;
    subject?: string;
    body?: string;
  };
  try {
    return NextResponse.json(await api.outreach(token, params.id, body));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't draft that email.";
    return NextResponse.json({ error: message }, { status });
  }
}
