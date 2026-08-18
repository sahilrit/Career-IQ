import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { notes } = (await request.json()) as { notes?: string };
  try {
    const application = await api.updateApplicationNotes(token, params.id, notes ?? "");
    return NextResponse.json(application);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Update failed.";
    return NextResponse.json({ error: message }, { status });
  }
}
