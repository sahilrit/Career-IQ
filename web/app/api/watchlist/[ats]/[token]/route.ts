import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ ats: string; token: string }> },
) {
  const authToken = getToken();
  if (!authToken) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { ats, token: boardToken } = await params;
  try {
    return NextResponse.json(await api.unwatchCompany(authToken, ats, boardToken));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    return NextResponse.json({ error: "Couldn't remove that company." }, { status });
  }
}
