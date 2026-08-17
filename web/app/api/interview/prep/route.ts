import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as {
    job_title?: string;
    company_name?: string;
    job_description?: string;
  };
  if (!body.job_title || !body.company_name) {
    return NextResponse.json({ error: "job title and company are required" }, { status: 400 });
  }
  try {
    const prep = await api.interviewPrep(token, {
      job_title: body.job_title,
      company_name: body.company_name,
      job_description: body.job_description ?? "",
    });
    return NextResponse.json(prep);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't generate prep.";
    return NextResponse.json({ error: message }, { status });
  }
}
