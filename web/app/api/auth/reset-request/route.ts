import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";

export async function POST(request: Request) {
  const { email } = (await request.json()) as { email?: string };
  if (!email) return NextResponse.json({ error: "email is required" }, { status: 400 });
  try {
    return NextResponse.json(await api.resetRequest(email));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    return NextResponse.json({ error: "Couldn't send the reset email." }, { status });
  }
}
