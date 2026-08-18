import { NextResponse } from "next/server";
import { API_BASE } from "@/lib/api";
import { getToken } from "@/lib/session";

// Streams the PDF from the backend through the same origin so the httpOnly
// session cookie authenticates the download (the browser can't attach the
// bearer token itself).
export async function GET(_request: Request, { params }: { params: { id: string } }) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const upstream = await fetch(`${API_BASE}/documents/${params.id}/pdf`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!upstream.ok) {
    return NextResponse.json({ error: "Couldn't export PDF." }, { status: upstream.status });
  }
  return new Response(await upstream.arrayBuffer(), {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition":
        upstream.headers.get("content-disposition") ?? 'attachment; filename="document.pdf"',
    },
  });
}
