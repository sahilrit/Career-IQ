import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

// Manage the workspace Anthropic key server-side; the key travels straight
// to the API and is never stored in client JS.
function unauthorized() {
  return NextResponse.json({ error: "not authenticated" }, { status: 401 });
}

function fail(error: unknown, fallback: string) {
  const status = error instanceof ApiError ? error.status : 500;
  const message = error instanceof ApiError ? error.message : fallback;
  return NextResponse.json({ error: message }, { status });
}

export async function GET() {
  const token = getToken();
  if (!token) return unauthorized();
  try {
    return NextResponse.json(await api.aiStatus(token));
  } catch (error) {
    return fail(error, "Couldn't read AI settings.");
  }
}

export async function PUT(request: Request) {
  const token = getToken();
  if (!token) return unauthorized();
  const { api_key } = (await request.json()) as { api_key?: string };
  if (!api_key) return NextResponse.json({ error: "missing api_key" }, { status: 400 });
  try {
    return NextResponse.json(await api.setAiKey(token, api_key));
  } catch (error) {
    return fail(error, "Couldn't save the key.");
  }
}

export async function DELETE() {
  const token = getToken();
  if (!token) return unauthorized();
  try {
    return NextResponse.json(await api.deleteAiKey(token));
  } catch (error) {
    return fail(error, "Couldn't remove the key.");
  }
}
