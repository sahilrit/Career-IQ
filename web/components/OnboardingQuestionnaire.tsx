"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

// First-run questionnaire: a few quick questions so the app can tailor itself
// (what to search for, salary floor, remote, and job-vs-freelance emphasis).
// Shown on the dashboard until the person tells us what they're after.
const FOCUS: [string, string, string][] = [
  ["job", "Find a job", "Full-time roles"],
  ["freelance", "Win clients", "Freelance / contract"],
  ["both", "Both", "Jobs and freelance"],
];

export function OnboardingQuestionnaire() {
  const router = useRouter();
  const [focus, setFocus] = useState("job");
  const [titles, setTitles] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(true);
  const [minSalary, setMinSalary] = useState("");
  const [busy, setBusy] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  async function save() {
    setBusy(true);
    try {
      const desired_titles = titles
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      const response = await fetch("/api/brain/preferences", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          focus,
          desired_titles,
          remote_only: remoteOnly,
          min_salary: minSalary ? Number(minSalary) : null,
        }),
      });
      if (response.ok) {
        setDismissed(true);
        router.refresh();
      }
    } finally {
      setBusy(false);
    }
  }

  if (dismissed) return null;

  return (
    <section className="card mb-6 border-accent/30 p-6">
      <div className="eyebrow mb-1">Let's tailor CareerOS to you</div>
      <p className="mb-4 text-sm text-muted">
        Four quick questions so your matches, salary guidance, and search fit what you actually want.
      </p>

      <div className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm text-white/80">What are you here to do?</label>
          <div className="flex flex-wrap gap-2">
            {FOCUS.map(([value, label, hint]) => (
              <button
                key={value}
                onClick={() => setFocus(value)}
                className={`rounded-xl border px-4 py-2 text-left text-sm transition ${
                  focus === value ? "border-accent/60 bg-accent/[0.06]" : "border-line text-muted"
                }`}
              >
                <div className="font-medium text-white">{label}</div>
                <div className="text-xs text-muted">{hint}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-white/80">
            What roles or work are you targeting?
          </label>
          <input
            className="input"
            placeholder="e.g. Performance Marketer, Growth Lead, Paid Social"
            value={titles}
            onChange={(e) => setTitles(e.target.value)}
          />
        </div>

        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1.5 block text-sm text-white/80">Minimum salary (optional)</label>
            <input
              className="input w-44"
              type="number"
              placeholder="e.g. 120000"
              value={minSalary}
              onChange={(e) => setMinSalary(e.target.value)}
            />
          </div>
          <label className="flex items-center gap-2 pb-2.5 text-sm text-white/80">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
            />
            Remote only
          </label>
        </div>

        <div className="flex items-center gap-4">
          <button onClick={save} disabled={busy} className="btn">
            {busy ? "Saving…" : "Save & personalize"}
          </button>
          <button onClick={() => setDismissed(true)} className="text-sm text-muted hover:text-white">
            Skip for now
          </button>
        </div>
      </div>
    </section>
  );
}
