"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Application } from "@/lib/api";

// The forward transitions the domain allows (mirrors ALLOWED_STATUS_TRANSITIONS
// in careeros-career-brain). Only valid next moves are offered; the backend
// still enforces the rule.
const NEXT: Record<string, string[]> = {
  discovered: ["qualified", "withdrawn"],
  qualified: ["applied", "withdrawn"],
  applied: ["in_review", "rejected", "withdrawn"],
  in_review: ["interviewing", "rejected", "withdrawn"],
  interviewing: ["offer", "rejected", "withdrawn"],
  offer: ["accepted", "rejected", "withdrawn"],
  accepted: [],
  rejected: [],
  withdrawn: [],
};

const TONE: Record<string, string> = {
  qualified: "text-emerald-400 border-emerald-500/40",
  applied: "text-sky-400 border-sky-500/40",
  in_review: "text-sky-400 border-sky-500/40",
  interviewing: "text-amber-400 border-amber-500/40",
  offer: "text-emerald-400 border-emerald-500/40",
  accepted: "text-emerald-400 border-emerald-500/40",
  rejected: "text-red-400 border-red-500/40",
  withdrawn: "text-muted border-line",
};

const label = (s: string) => s.replace(/_/g, " ");

export function StatusControl({ application }: { application: Application }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notesOpen, setNotesOpen] = useState(false);
  const [notes, setNotes] = useState(application.notes ?? "");
  const [savedNote, setSavedNote] = useState(false);

  const nextStates = NEXT[application.status] ?? [];

  async function move(to: string) {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`/api/applications/${application.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to }),
      });
      if (!response.ok) setError((await response.json()).error ?? "Couldn't update status.");
      else router.refresh();
    } finally {
      setBusy(false);
    }
  }

  async function saveNotes() {
    setBusy(true);
    setError(null);
    setSavedNote(false);
    try {
      const response = await fetch(`/api/applications/${application.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes }),
      });
      if (!response.ok) setError((await response.json()).error ?? "Couldn't save notes.");
      else {
        setSavedNote(true);
        router.refresh();
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 border-t border-lineSoft pt-3">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`rounded-full border px-2.5 py-0.5 text-xs ${TONE[application.status] ?? "text-muted border-line"}`}
        >
          {label(application.status)}
        </span>
        {nextStates.length > 0 && <span className="text-xs text-muted">→</span>}
        {nextStates.map((to) => (
          <button
            key={to}
            onClick={() => move(to)}
            disabled={busy}
            className="rounded-full border border-line px-2.5 py-0.5 text-xs text-white/80 transition hover:border-accent/50 hover:text-white disabled:opacity-50"
          >
            {label(to)}
          </button>
        ))}
        <button
          onClick={() => setNotesOpen((o) => !o)}
          className="ml-auto text-xs text-muted transition hover:text-white"
        >
          {application.notes ? "Notes ✎" : "Add note"}
        </button>
      </div>

      {notesOpen && (
        <div className="mt-3">
          <textarea
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              setSavedNote(false);
            }}
            placeholder="Recruiter name, referral, next step…"
            className="input min-h-20 text-sm"
          />
          <div className="mt-2 flex items-center gap-3">
            <button onClick={saveNotes} disabled={busy} className="btn-ghost text-xs">
              {busy ? "Saving…" : "Save note"}
            </button>
            {savedNote && <span className="text-xs text-emerald-400">Saved</span>}
          </div>
        </div>
      )}

      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </div>
  );
}
