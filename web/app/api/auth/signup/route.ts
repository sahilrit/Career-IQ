import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { SESSION_COOKIE } from "@/lib/session";

export async function POST(request: Request) {
  const { email, password, full_name } = (await request.json()) as {
    email: string;
    password: string;
    full_name: string;
  };
  try {
    const { token } = await api.signup({ email, password, full_name });
    const response = NextResponse.json({ ok: true });
    response.cookies.set(SESSION_COOKIE, token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 7,
    });
    return response;
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : "Could not sign up — is the API running?";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
