"use client";

import { useState } from "react";
import type { InterviewPrep } from "@/lib/api";
import { FadeIn } from "@/components/Motion";

function List({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="mb-4">
      <div className="mb-2 text-xs uppercase tracking-wide text-muted">{title}</div>
      <ul className="space-y-1.5">
        {items.map((item, index) => (
          <li key={index} className="rounded-lg border border-line bg-ink/40 px-3 py-2 text-sm">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function InterviewPrepForm() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prep, setPrep] = useState<InterviewPrep | null>(null);

  async function submit(formData: FormData) {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/interview/prep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: formData.get("job_title"),
          company_name: formData.get("company_name"),
          job_description: formData.get("job_description"),
        }),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Couldn't generate prep.");
      else setPrep(data);
    } catch {
      setError("Something went wrong — try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <FadeIn>
      <form action={submit} className="card mb-6 grid gap-3 p-6 sm:grid-cols-2">
        <input name="job_title" className="input" placeholder="Job title (e.g. PPC Manager)" required />
        <input name="company_name" className="input" placeholder="Company" required />
        <textarea
          name="job_description"
          className="input min-h-24 sm:col-span-2"
          placeholder="Paste the job description (optional, improves the questions)"
        />
        <div className="sm:col-span-2">
          <button className="btn" disabled={busy}>
            {busy ? "Preparing…" : "Prepare me for this interview"}
          </button>
        </div>
        {error && <p className="text-sm text-red-400 sm:col-span-2">{error}</p>}
      </form>

      {prep && (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="card p-6">
            <h2 className="mb-4 text-lg font-medium">Likely questions</h2>
            <List title="Role-specific" items={prep.questions.role_specific} />
            <List title="Technical" items={prep.questions.technical} />
            <List title="About the company" items={prep.questions.company_specific} />
            <div className="mb-1 text-xs uppercase tracking-wide text-muted">
              STAR answer prompts
            </div>
            <ul className="space-y-2">
              {prep.questions.star_prompts.map((prompt, index) => (
                <li key={index} className="rounded-lg border border-line bg-ink/40 px-3 py-2 text-sm">
                  <div className="font-medium">{prompt.question}</div>
                  <div className="text-muted">
                    Use: {prompt.achievement_description}
                    {prompt.metric ? ` (${prompt.metric})` : ""}
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="card p-6">
            <h2 className="mb-4 text-lg font-medium">Your one-page briefing</h2>
            <List title="Lead with these wins" items={prep.briefing.strongest_achievements} />
            <List title="Questions to ask them" items={prep.briefing.questions_to_ask} />
            <div className="mb-4">
              <div className="mb-2 text-xs uppercase tracking-wide text-muted">
                Compensation strategy
              </div>
              <p className="rounded-lg border border-line bg-ink/40 px-3 py-2 text-sm">
                {prep.briefing.compensation_strategy}
              </p>
            </div>
            <List title="Things to avoid" items={prep.briefing.things_to_avoid} />
          </section>
        </div>
      )}
    </FadeIn>
  );
}
