"use client";

import { useState } from "react";
import Link from "next/link";

// One-click interview booking: creates a Google Calendar event and emails the
// invite to the interviewer. Guides to Settings if Google isn't connected.
export function BookInterviewButton({ defaultSummary = "Interview" }: { defaultSummary?: string }) {
  const [open, setOpen] = useState(false);
  const [summary, setSummary] = useState(defaultSummary);
  const [start, setStart] = useState(""); // datetime-local value
  const [minutes, setMinutes] = useState(45);
  const [attendee, setAttendee] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsConnect, setNeedsConnect] = useState(false);
  const [link, setLink] = useState<string | null>(null);

  async function book() {
    setBusy(true);
    setError(null);
    setNeedsConnect(false);
    setLink(null);
    try {
      const startDate = new Date(start);
      if (Number.isNaN(startDate.getTime())) {
        setError("Pick a date and time.");
        return;
      }
      const endDate = new Date(startDate.getTime() + minutes * 60_000);
      const response = await fetch("/api/integrations/calendar/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          summary,
          start_iso: startDate.toISOString(),
          end_iso: endDate.toISOString(),
          attendees: attendee ? [attendee] : [],
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (response.status === 409) {
        setNeedsConnect(true);
        return;
      }
      if (!response.ok) {
        setError(data.error ?? "Couldn't create the event.");
        return;
      }
      setLink(data.html_link ?? null);
    } catch {
      setError("Something went wrong — try again.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button type="button" className="btn" onClick={() => setOpen(true)}>
        📅 Book interview
      </button>
    );
  }

  return (
    <div className="mt-2 max-w-md space-y-2 rounded-xl border border-line bg-ink/50 p-3">
      <input
        className="input"
        placeholder="Event title"
        value={summary}
        onChange={(e) => setSummary(e.target.value)}
      />
      <div className="flex gap-2">
        <input
          className="input"
          type="datetime-local"
          value={start}
          onChange={(e) => setStart(e.target.value)}
        />
        <select
          className="input max-w-32"
          value={minutes}
          onChange={(e) => setMinutes(Number(e.target.value))}
        >
          <option value={30}>30 min</option>
          <option value={45}>45 min</option>
          <option value={60}>60 min</option>
        </select>
      </div>
      <input
        className="input"
        placeholder="Interviewer email (optional — sends an invite)"
        value={attendee}
        onChange={(e) => setAttendee(e.target.value)}
      />
      <div className="flex items-center gap-2">
        <button type="button" className="btn text-sm" disabled={busy || !start} onClick={book}>
          {busy ? "Booking…" : "Add to calendar"}
        </button>
        <button type="button" className="btn-ghost text-sm" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
      {needsConnect && (
        <p className="text-sm text-muted">
          Connect your Google account first —{" "}
          <Link href="/settings" className="text-accentSoft hover:underline">
            open Settings
          </Link>
          .
        </p>
      )}
      {link && (
        <p className="text-sm text-emerald-400">
          Added ✓{" "}
          <a href={link} target="_blank" rel="noreferrer" className="underline">
            view event
          </a>
        </p>
      )}
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
