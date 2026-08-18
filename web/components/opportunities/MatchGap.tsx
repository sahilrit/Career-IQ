"use client";

import { useState } from "react";
import type { MatchGap as Gap } from "@/lib/api";

// Turns the bare match % into a to-do list: which of your skills the posting
// wants (matched) and which of its keywords are missing from your Career Brain.
export function MatchGap({ applicationId }: { applicationId: string }) {
  const [open, setOpen] = useState(false);
  const [gap, setGap] = useState<Gap | null>(null);
  const [busy, setBusy] = useState(false);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !gap) {
      setBusy(true);
      try {
        const response = await fetch(`/api/applications/${applicationId}/gap`);
        if (response.ok) setGap(await response.json());
      } finally {
        setBusy(false);
      }
    }
  }

  return (
    <div className="mt-2">
      <button onClick={toggle} className="text-xs text-muted transition hover:text-white">
        {open ? "Hide match detail" : "Why this match?"}
      </button>
      {open && (
        <div className="mt-2 text-xs">
          {busy && <span className="text-muted">Analyzing…</span>}
          {gap && !gap.available && (
            <span className="text-muted">Re-run search to analyze this posting.</span>
          )}
          {gap && gap.available && (
            <div className="space-y-2">
              <div>
                <span className="text-muted">Your skills they want: </span>
                {gap.matched_skills.length === 0 ? (
                  <span className="text-muted">none detected</span>
                ) : (
                  <span className="inline-flex flex-wrap gap-1.5">
                    {gap.matched_skills.map((s) => (
                      <span
                        key={s}
                        className="rounded-full border border-emerald-500/40 px-2 py-0.5 text-emerald-400"
                      >
                        {s}
                      </span>
                    ))}
                  </span>
                )}
              </div>
              {gap.missing_keywords.length > 0 && (
                <div>
                  <span className="text-muted">Missing from your Brain: </span>
                  <span className="inline-flex flex-wrap gap-1.5">
                    {gap.missing_keywords.map((s) => (
                      <span
                        key={s}
                        className="rounded-full border border-amber-500/40 px-2 py-0.5 text-amber-400"
                      >
                        {s}
                      </span>
                    ))}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
