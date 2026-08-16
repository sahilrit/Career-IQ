"use client";

import { useState } from "react";

type Package = { resume_text: string; cover_letter: string };

export function GenerateButton({ jobUrl }: { jobUrl: string | null }) {
  const [busy, setBusy] = useState(false);
  const [pkg, setPkg] = useState<Package | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!jobUrl) return null;

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/opportunities/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_url: jobUrl }),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Generation failed.");
      else setPkg(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3">
      <button onClick={generate} disabled={busy} className="btn-ghost text-sm">
        {busy ? "Generating…" : pkg ? "Regenerate" : "Generate resume & cover letter"}
      </button>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      {pkg && (
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div>
            <div className="mb-1 text-xs uppercase tracking-wide text-muted">Resume</div>
            <textarea readOnly className="input min-h-40 text-xs" value={pkg.resume_text} />
          </div>
          <div>
            <div className="mb-1 text-xs uppercase tracking-wide text-muted">Cover letter</div>
            <textarea readOnly className="input min-h-40 text-xs" value={pkg.cover_letter} />
          </div>
        </div>
      )}
    </div>
  );
}
