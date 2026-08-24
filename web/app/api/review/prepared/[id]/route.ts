import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

// Mark a prepared application submitted (you applied) or dismissed — either
// way it drops off the review queue.
export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { status } = (await request.json()) as { status?: "submitted" | "dismissed" };
  try {
    return NextResponse.json(await api.reviewUpdate(token, params.id, status ?? "dismissed"));
  } catch (error) {
    const code = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't update.";
    return NextResponse.json({ error: message }, { status: code });
  }
}
