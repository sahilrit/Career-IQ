import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";

export async function POST(request: Request) {
  const { token, new_password } = (await request.json()) as {
    token?: string;
    new_password?: string;
  };
  if (!token || !new_password) {
    return NextResponse.json({ error: "token and new password are required" }, { status: 400 });
  }
  try {
    return NextResponse.json(await api.resetConfirm(token, new_password));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't reset the password.";
    return NextResponse.json({ error: message }, { status });
  }
}
