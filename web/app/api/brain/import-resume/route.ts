import { NextResponse } from "next/server";
import { API_BASE, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

// Forward the uploaded résumé to careeros-api as multipart, server-side,
// with the bearer token from the httpOnly cookie. The file bytes never
// pass through client JS beyond the browser's own upload.
export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });

  const incoming = await request.formData();
  const file = incoming.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ error: "no file uploaded" }, { status: 400 });
  }

  const forward = new FormData();
  forward.append("file", file, file.name);

  try {
    const response = await fetch(`${API_BASE}/brain/import-resume`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: forward,
      cache: "no-store",
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message =
        (payload as { detail?: string }).detail ?? "Couldn't import that résumé.";
      return NextResponse.json({ error: message }, { status: response.status });
    }
    return NextResponse.json(payload);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    return NextResponse.json({ error: "Résumé import failed." }, { status });
  }
}
