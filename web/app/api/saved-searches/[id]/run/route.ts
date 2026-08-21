import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { send_email } = (await request.json()) as { send_email?: boolean };
  try {
    return NextResponse.json(await api.runSavedSearch(token, params.id, send_email ?? false));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't run.";
    return NextResponse.json({ error: message }, { status });
  }
}
