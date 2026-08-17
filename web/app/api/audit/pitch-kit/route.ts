import { NextResponse } from "next/server";
import { api, ApiError, type PitchKitInput } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as PitchKitInput;
  if (!body.company_name) {
    return NextResponse.json({ error: "company name is required" }, { status: 400 });
  }
  try {
    return NextResponse.json(await api.pitchKit(token, body));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't build the pitch kit.";
    return NextResponse.json({ error: message }, { status });
  }
}
