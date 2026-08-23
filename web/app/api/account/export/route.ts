import { NextResponse } from "next/server";
import { API_BASE } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function GET() {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const upstream = await fetch(`${API_BASE}/account/export`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!upstream.ok) {
    return NextResponse.json({ error: "Couldn't export your data." }, { status: upstream.status });
  }
  return new Response(await upstream.arrayBuffer(), {
    headers: {
      "Content-Type": "application/json",
      "Content-Disposition": 'attachment; filename="careeros-export.json"',
    },
  });
}
