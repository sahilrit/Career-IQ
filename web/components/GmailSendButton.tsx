"use client";

import { useState } from "react";
import Link from "next/link";

// Reusable one-click Gmail composer. Drop it anywhere a recipient/subject/body
// makes sense (Network contacts, Pitch Kit). Opens an inline panel, sends via
// the connected Google account, and guides the user to Settings if not connected.
export function GmailSendButton({
  defaultTo = "",
  defaultSubject = "",
  defaultBody = "",
  label = "Email",
  size = "sm",
}: {
  defaultTo?: string;
  defaultSubject?: string;
  defaultBody?: string;
  label?: string;
  size?: "sm" | "md";
}) {
  const [open, setOpen] = useState(false);
  const [to, setTo] = useState(defaultTo);
  const [subject, setSubject] = useState(defaultSubject);
  const [body, setBody] = useState(defaultBody);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsConnect, setNeedsConnect] = useState(false);
  const [sent, setSent] = useState(false);

  async function send() {
    setBusy(true);
    setError(null);
    setNeedsConnect(false);
    try {
      const response = await fetch("/api/integrations/gmail/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to, subject, body }),
      });
      const data = await response.json().catch(() => ({}));
      if (response.status === 409) {
        setNeedsConnect(true);
        return;
      }
      if (!response.ok) {
        setError(data.error ?? "Couldn't send the email.");
        return;
      }
      setSent(true);
      setTimeout(() => setOpen(false), 1200);
    } catch {
      setError("Something went wrong — try again.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        className={size === "md" ? "btn" : "btn-ghost text-xs"}
        onClick={() => {
          setSent(false);
          setOpen(true);
        }}
      >
        ✉ {label}
      </button>
    );
  }

  return (
    <div className="mt-2 w-full space-y-2 rounded-xl border border-line bg-ink/50 p-3">
      <input
        className="input"
        placeholder="To (email address)"
        value={to}
        onChange={(e) => setTo(e.target.value)}
      />
      <input
        className="input"
        placeholder="Subject"
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
      />
      <textarea
        className="input min-h-28 text-sm"
        placeholder="Message"
        value={body}
        onChange={(e) => setBody(e.target.value)}
      />
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="btn text-sm"
          disabled={busy || !to || !subject || !body}
          onClick={send}
        >
          {busy ? "Sending…" : "Send via Gmail"}
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
      {sent && <p className="text-sm text-emerald-400">Sent ✓</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
