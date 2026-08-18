import { NextResponse } from "next/server";
import { api, ApiError } from "@/lib/api";
import { getToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = getToken();
  if (!token) return NextResponse.json({ error: "not authenticated" }, { status: 401 });
  const body = (await request.json()) as { question?: string; answer?: string; job_title?: string };
  if (!body.question || !body.answer) {
    return NextResponse.json({ error: "question and answer are required" }, { status: 400 });
  }
  try {
    const feedback = await api.practiceAnswer(token, {
      question: body.question,
      answer: body.answer,
      job_title: body.job_title,
    });
    return NextResponse.json(feedback);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const message = error instanceof ApiError ? error.message : "Couldn't score that answer.";
    return NextResponse.json({ error: message }, { status });
  }
}
