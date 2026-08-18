import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { date, add_to_calendar } = (await request.json()) as {
    date?: string | null;
    add_to_calendar?: boolean;
  };
  try {
    const result = await api.setFollowUp(token, params.id, date ?? null, add_to_calendar ?? false);
    return NextResponse.json(result);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't set reminder.";
    return NextResponse.json({ error: message }, { status });
  }
}
