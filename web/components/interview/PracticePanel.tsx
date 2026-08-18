"use client";

import { useState } from "react";
import type { PracticeFeedback } from "@/lib/api";

export function PracticePanel() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PracticeFeedback | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/interview/practice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, answer }),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Couldn't score that answer.");
      else setResult(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card p-6">
      <h2 className="eyebrow mb-1">Practice</h2>
      <p className="mb-4 text-sm text-muted">
        Rehearse an answer and get instant coaching on structure, specificity, and impact.
      </p>
      <div className="space-y-3">
        <input
          className="input"
          placeholder="Interview question — e.g. Tell me about a time you drove growth."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <textarea
          className="input min-h-32"
          placeholder="Your answer…"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
        />
        <button
          onClick={submit}
          disabled={busy || !question.trim() || !answer.trim()}
          className="btn"
        >
          {busy ? "Scoring…" : "Get feedback"}
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

      {result && (
        <div className="mt-5 space-y-3 border-t border-lineSoft pt-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-display text-2xl font-semibold text-accent">
              {result.rating}/5
            </span>
            <Chip on={result.has_metrics} label="metrics" />
            <Chip on={result.uses_star} label="STAR structure" />
            <span className="text-xs text-muted">{result.word_count} words</span>
            <span
              className={
                result.ai_used
                  ? "rounded-full bg-accent/20 px-2 py-0.5 text-[10px] font-medium text-accentSoft"
                  : "rounded-full border border-line px-2 py-0.5 text-[10px] font-medium text-muted"
              }
            >
              {result.ai_used ? "✨ AI coach" : "Instant score"}
            </span>
          </div>
          <p className="text-sm leading-relaxed text-white/85">{result.feedback}</p>
          {result.improvements.length > 0 && (
            <ul className="space-y-1.5 text-sm text-muted">
              {result.improvements.map((tip) => (
                <li key={tip} className="flex items-start gap-2">
                  <span className="mt-1 text-accent">→</span>
                  {tip}
                </li>
              ))}
            </ul>
          )}
          {result.ai_error && (
            <p className="text-xs text-amber-400">
              AI coach unavailable, showing instant score — {result.ai_error}
            </p>
          )}
        </div>
      )}
    </section>
  );
}

function Chip({ on, label }: { on: boolean; label: string }) {
  return (
    <span
      className={`rounded-full border px-2.5 py-0.5 text-xs ${
        on ? "border-emerald-500/40 text-emerald-400" : "border-line text-muted"
      }`}
    >
      {on ? "✓" : "✗"} {label}
    </span>
  );
}
