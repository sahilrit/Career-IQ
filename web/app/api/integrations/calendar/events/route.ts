import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function GET() {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  try {
    return NextResponse.json(await api.calendarEvents(token));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't load your calendar.";
    return NextResponse.json({ error: message }, { status });
  }
}
