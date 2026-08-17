"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { CalendarEvent, GoogleStatus } from "@/lib/api";
import { FadeIn } from "@/components/Motion";

export function GoogleCard({ initial }: { initial: GoogleStatus }) {
  const router = useRouter();
  const [status, setStatus] = useState<GoogleStatus>(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<CalendarEvent[] | null>(null);
  const [email, setEmail] = useState({ to: "", subject: "", body: "" });
  const [sent, setSent] = useState(false);

  useEffect(() => {
    if (!status.connected) return;
    fetch("/api/integrations/calendar/events")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setEvents(Array.isArray(data) ? data : []))
      .catch(() => setEvents([]));
  }, [status.connected]);

  async function connect() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/integrations/google/auth-url");
      const data = await response.json();
      if (!response.ok || !data.url) {
        setError(data.error ?? "Google isn't set up on the server yet.");
        return;
      }
      window.location.href = data.url;
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    setBusy(true);
    try {
      await fetch("/api/integrations/google", { method: "DELETE" });
      setStatus({ ...status, connected: false, email: null });
      setEvents(null);
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  async function sendEmail() {
    setBusy(true);
    setError(null);
    setSent(false);
    try {
      const response = await fetch("/api/integrations/gmail/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(email),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Couldn't send the email.");
      else {
        setSent(true);
        setEmail({ to: "", subject: "", body: "" });
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <FadeIn>
      <section className="card max-w-xl p-6">
        <h2 className="eyebrow mb-1">Google — Gmail &amp; Calendar</h2>
        {!status.configured ? (
          <p className="mb-2 text-sm text-muted">
            Not set up on the server yet. Once your Google keys are added, you&apos;ll be able to
            send outreach from Gmail and see your calendar here.
          </p>
        ) : status.connected ? (
          <p className="mb-4 text-sm text-emerald-400">Connected as {status.email}.</p>
        ) : (
          <p className="mb-4 text-sm text-muted">
            Connect your Google account to send outreach emails and manage interviews.
          </p>
        )}

        {status.configured && !status.connected && (
          <button className="btn" disabled={busy} onClick={connect}>
            {busy ? "…" : "Connect Google"}
          </button>
        )}

        {status.connected && (
          <>
            <div className="mb-4 flex items-center gap-2">
              <button className="btn-ghost text-sm" disabled={busy} onClick={disconnect}>
                Disconnect
              </button>
            </div>

            <div className="mb-4 rounded-xl border border-line bg-ink/40 p-4">
              <div className="eyebrow mb-2">Send an email</div>
              <div className="space-y-2">
                <input
                  className="input"
                  placeholder="To (email address)"
                  value={email.to}
                  onChange={(e) => setEmail({ ...email, to: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Subject"
                  value={email.subject}
                  onChange={(e) => setEmail({ ...email, subject: e.target.value })}
                />
                <textarea
                  className="input min-h-24"
                  placeholder="Message"
                  value={email.body}
                  onChange={(e) => setEmail({ ...email, body: e.target.value })}
                />
                <button
                  className="btn"
                  disabled={busy || !email.to || !email.subject || !email.body}
                  onClick={sendEmail}
                >
                  {busy ? "Sending…" : "Send via Gmail"}
                </button>
                {sent && <p className="text-sm text-emerald-400">Sent.</p>}
              </div>
            </div>

            <div className="rounded-xl border border-line bg-ink/40 p-4">
              <div className="eyebrow mb-2">Upcoming events</div>
              {events === null ? (
                <p className="text-sm text-muted">Loading…</p>
              ) : events.length === 0 ? (
                <p className="text-sm text-muted">Nothing coming up.</p>
              ) : (
                <ul className="space-y-1.5">
                  {events.map((event, index) => (
                    <li key={index} className="flex justify-between gap-3 text-sm">
                      <span className="truncate">{event.summary}</span>
                      <span className="shrink-0 text-muted">{event.start.slice(0, 16).replace("T", " ")}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}

        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      </section>
    </FadeIn>
  );
}
