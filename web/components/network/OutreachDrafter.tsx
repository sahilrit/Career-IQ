"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Contact } from "@/lib/api";

const KINDS: [string, string][] = [
  ["intro", "Intro"],
  ["referral", "Referral"],
  ["thank_you", "Thank-you"],
];

export function OutreachDrafter({ contact }: { contact: Contact }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState("intro");
  const [targetRole, setTargetRole] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [aiUsed, setAiUsed] = useState(false);

  async function draft() {
    setBusy(true);
    setStatus(null);
    try {
      const response = await fetch(`/api/contacts/${contact.id}/outreach`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, target_role: targetRole }),
      });
      const data = await response.json();
      if (!response.ok) setStatus(data.error ?? "Couldn't draft.");
      else {
        setSubject(data.subject);
        setBody(data.body);
        setAiUsed(data.ai_used);
      }
    } finally {
      setBusy(false);
    }
  }

  async function send() {
    setBusy(true);
    setStatus(null);
    try {
      const response = await fetch(`/api/contacts/${contact.id}/outreach`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, send: true, subject, body }),
      });
      const data = await response.json();
      if (!response.ok) setStatus(data.error ?? "Couldn't send.");
      else if (data.sent) {
        setStatus("Sent and logged to the timeline ✓");
        router.refresh();
      } else {
        setStatus(data.reason ?? "Not sent.");
      }
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="btn-ghost mt-3 text-sm">
        Draft outreach
      </button>
    );
  }

  return (
    <div className="mt-3 border-t border-lineSoft pt-3">
      <div className="flex flex-wrap items-center gap-2">
        {KINDS.map(([value, label]) => (
          <button
            key={value}
            onClick={() => setKind(value)}
            className={`rounded-full border px-3 py-1 text-xs transition ${
              kind === value ? "border-accent/60 text-white" : "border-line text-muted"
            }`}
          >
            {label}
          </button>
        ))}
        {kind === "referral" && (
          <input
            className="input w-auto py-1.5 text-xs"
            placeholder="Target role"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
          />
        )}
        <button onClick={draft} disabled={busy} className="btn-ghost text-xs">
          {busy ? "Drafting…" : subject ? "Redraft" : "Draft"}
        </button>
      </div>

      {subject && (
        <div className="mt-3 space-y-2">
          <input
            className="input text-sm"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          />
          <textarea
            className="input min-h-40 text-sm"
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
          <div className="flex items-center gap-3">
            <button onClick={send} disabled={busy || !contact.email} className="btn text-sm">
              {busy ? "Sending…" : "Send via Gmail"}
            </button>
            {aiUsed && (
              <span className="rounded-full bg-accent/20 px-2 py-0.5 text-[10px] font-medium text-accentSoft">
                ✨ AI-written
              </span>
            )}
            {!contact.email && <span className="text-xs text-muted">No email on file</span>}
          </div>
        </div>
      )}
      {status && <p className="mt-2 text-sm text-amber-400">{status}</p>}
    </div>
  );
}
