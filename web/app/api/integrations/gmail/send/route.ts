import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as { to?: string; subject?: string; body?: string };
  if (!body.to || !body.subject || !body.body) {
    return NextResponse.json({ error: "to, subject and body are required" }, { status: 400 });
  }
  try {
    return NextResponse.json(
      await api.gmailSend(token, { to: body.to, subject: body.subject, body: body.body }),
    );
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't send the email.";
    return NextResponse.json({ error: message }, { status });
  }
}
