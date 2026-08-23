import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function PATCH(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as {
    focus?: string;
    desired_titles?: string[];
    remote_only?: boolean;
    min_salary?: number | null;
  };
  try {
    return NextResponse.json(await api.updatePreferences(token, body));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't save.";
    return NextResponse.json({ error: message }, { status });
  }
}
