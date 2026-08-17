"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { AiStatus } from "@/lib/api";
import { FadeIn } from "@/components/Motion";

const DEFAULT_LABEL = "your provider's default";

export function AiKeyForm({ initial }: { initial: AiStatus }) {
  const router = useRouter();
  const [status, setStatus] = useState<AiStatus>(initial);
  const [key, setKey] = useState("");
  const [model, setModel] = useState(
    initial.has_key && initial.model !== DEFAULT_LABEL ? initial.model : "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // With a key already saved you can change just the model; otherwise a key
  // is required.
  const canSave = status.has_key || key.length >= 20;

  async function save() {
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const response = await fetch("/api/settings/ai", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: key, model }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.error ?? "Couldn't save.");
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
      setModel("");
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
        <h2 className="eyebrow mb-1">AI writing</h2>
        {status.has_key ? (
          <p className="mb-4 text-sm text-emerald-400">AI is ON — writing with {status.model}.</p>
        ) : (
          <p className="mb-4 text-sm text-muted">
            AI is off — using free templates. Add an API key to switch it on.
          </p>
        )}

        <label className="label">AI provider key</label>
        <input
          type="password"
          className="input"
          placeholder={
            status.has_key ? "•••••••• (leave blank to keep)" : "sk-ant-… / sk-or-… / sk-… / nvapi-…"
          }
          value={key}
          onChange={(event) => setKey(event.target.value)}
          autoComplete="off"
        />
        <p className="mt-1.5 text-xs text-muted">
          Works with Anthropic (sk-ant-…), OpenRouter (sk-or-…), OpenAI (sk-…), or{" "}
          <span className="text-white/80">NVIDIA (nvapi-…)</span>. We detect the provider from the
          key. Stored encrypted; never shown again.
        </p>

        <label className="label mt-4">Model (optional)</label>
        <input
          className="input"
          placeholder="e.g. meta/llama-3.3-70b-instruct"
          value={model}
          onChange={(event) => setModel(event.target.value)}
          autoComplete="off"
        />
        <p className="mt-1.5 text-xs text-muted">
          Leave blank for the provider default. <span className="text-white/80">NVIDIA</span> is the
          most reliable free option — its default (
          <span className="text-white/80">meta/llama-3.3-70b-instruct</span>) runs on NVIDIA&apos;s
          free tier. Browse models at build.nvidia.com (or openrouter.ai/models).
        </p>

        <div className="mt-4 flex gap-2">
          <button className="btn" disabled={busy || !canSave} onClick={save}>
            {busy ? "Saving…" : status.has_key ? "Save changes" : "Save key"}
          </button>
          {status.has_key && (
            <button className="btn-ghost" disabled={busy} onClick={remove}>
              Remove
            </button>
          )}
        </div>

        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        {saved && <p className="mt-3 text-sm text-emerald-400">Saved.</p>}
      </section>
    </FadeIn>
  );
}
