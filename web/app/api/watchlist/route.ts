import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function GET() {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  try {
    return NextResponse.json(await api.watchlist(token));
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    return NextResponse.json({ error: "Couldn't load your watchlist." }, { status });
  }
}

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as {
    ats?: string;
    board_token?: string;
    display_name?: string;
  };
  if (!body.ats || !body.board_token) {
    return NextResponse.json({ error: "ats and board_token are required" }, { status: 400 });
  }
  try {
    return NextResponse.json(
      await api.watchCompany(token, {
        ats: body.ats,
        board_token: body.board_token,
        display_name: body.display_name,
      }),
    );
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't add that company.";
    return NextResponse.json({ error: message }, { status });
  }
}
