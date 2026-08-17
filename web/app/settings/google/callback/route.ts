import { NextResponse } from "next/server";
import { api } from "@/lib/api";
import { getToken } from "@/lib/session";

// Google redirects the browser here after consent. We hold the httpOnly
// session cookie, so we can exchange the code server-side and store the
// connection, then bounce back to Settings.
export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const base = url.origin;
  const token = getToken();

  if (!token) return NextResponse.redirect(`${base}/login`);
  if (!code) return NextResponse.redirect(`${base}/settings?google=error`);

  try {
    await api.googleConnect(token, code);
    return NextResponse.redirect(`${base}/settings?google=connected`);
  } catch {
    return NextResponse.redirect(`${base}/settings?google=error`);
  }
}
