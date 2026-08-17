"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { AiStatus } from "@/lib/api";
import { FadeIn } from "@/components/Motion";

export function AiKeyForm({ initial }: { initial: AiStatus }) {
  const router = useRouter();
  const [status, setStatus] = useState<AiStatus>(initial);
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function save() {
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const response = await fetch("/api/settings/ai", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: key }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.error ?? "Couldn't save the key.");
        return;
      }
      setStatus(data);
      setKey("");
      setSaved(true);
      router.refresh();
    } catch {
      setError("Save failed — check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const response = await fetch("/api/settings/ai", { method: "DELETE" });
      const data = await response.json();
      if (!response.ok) {
        setError(data.error ?? "Couldn't remove the key.");
        return;
      }
      setStatus(data);
      router.refresh();
    } catch {
      setError("Remove failed — try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <FadeIn>
      <section className="card max-w-xl p-6">
        <h2 className="mb-1 text-sm uppercase tracking-wide text-muted">AI writing</h2>
        {status.has_key ? (
          <p className="mb-4 text-sm text-emerald-400">
            AI is ON — cover letters are written by {status.model}.
          </p>
        ) : (
          <p className="mb-4 text-sm text-muted">
            AI is off — using free templates. Add your Anthropic API key to switch it on.
          </p>
        )}

        <label className="label">Anthropic API key</label>
        <input
          type="password"
          className="input"
          placeholder="sk-ant-…"
          value={key}
          onChange={(event) => setKey(event.target.value)}
          autoComplete="off"
        />
        <p className="mt-1.5 text-xs text-muted">
          Create one at console.anthropic.com (add ~$5 credit). Stored encrypted; never shown again.
        </p>

        <div className="mt-4 flex gap-2">
          <button className="btn" disabled={busy || key.length < 20} onClick={save}>
            {busy ? "Saving…" : status.has_key ? "Replace key" : "Save key"}
          </button>
          {status.has_key && (
            <button className="btn-ghost" disabled={busy} onClick={remove}>
              Remove
            </button>
          )}
        </div>

        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        {saved && <p className="mt-3 text-sm text-emerald-400">Saved. AI is on.</p>}
      </section>
    </FadeIn>
  );
}
