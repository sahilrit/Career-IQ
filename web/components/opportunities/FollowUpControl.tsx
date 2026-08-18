"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Application } from "@/lib/api";

export function FollowUpControl({ application }: { application: Application }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState(application.follow_up_date ?? "");
  const [toCalendar, setToCalendar] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function save(clear = false) {
    setBusy(true);
    setMsg(null);
    try {
      const response = await fetch(`/api/applications/${application.id}/follow-up`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: clear ? null : date || null,
          add_to_calendar: !clear && toCalendar,
        }),
      });
      const data = await response.json();
      if (!response.ok) setMsg(data.error ?? "Couldn't save.");
      else {
        if (data.calendar && toCalendar && !clear) {
          setMsg(data.calendar.created ? "Added to your calendar" : data.calendar.reason);
        }
        router.refresh();
        if (clear) setOpen(false);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-2">
      <button onClick={() => setOpen((o) => !o)} className="text-xs text-muted transition hover:text-white">
        {application.follow_up_date ? `Follow-up: ${application.follow_up_date}` : "Set follow-up"}
      </button>
      {open && (
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="input w-auto py-1.5 text-xs"
          />
          <label className="flex items-center gap-1.5 text-xs text-muted">
            <input
              type="checkbox"
              checked={toCalendar}
              onChange={(e) => setToCalendar(e.target.checked)}
            />
            Add to Google Calendar
          </label>
          <button onClick={() => save(false)} disabled={busy || !date} className="btn-ghost text-xs">
            {busy ? "Saving…" : "Save"}
          </button>
          {application.follow_up_date && (
            <button onClick={() => save(true)} disabled={busy} className="text-xs text-muted hover:text-white">
              Clear
            </button>
          )}
          {msg && <span className="text-xs text-amber-400">{msg}</span>}
        </div>
      )}
    </div>
  );
}
