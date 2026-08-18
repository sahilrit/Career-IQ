import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const { content } = (await request.json()) as { content?: string };
  try {
    const document = await api.editDocument(token, params.id, content ?? "");
    return NextResponse.json(document);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't save.";
    return NextResponse.json({ error: message }, { status });
  }
}
