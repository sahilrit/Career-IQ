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

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as {
    summary?: string;
    start_iso?: string;
    end_iso?: string;
    attendees?: string[];
  };
  if (!body.summary || !body.start_iso || !body.end_iso) {
    return NextResponse.json({ error: "title, start and end are required" }, { status: 400 });
  }
  try {
    return NextResponse.json(
      await api.calendarCreate(token, {
        summary: body.summary,
        start_iso: body.start_iso,
        end_iso: body.end_iso,
        attendees: body.attendees ?? [],
      }),
    );
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't create the event.";
    return NextResponse.json({ error: message }, { status });
  }
}
