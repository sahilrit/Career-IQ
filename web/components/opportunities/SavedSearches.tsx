"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { SavedSearch } from "@/lib/api";

export function SavedSearches({ initial }: { initial: SavedSearch[] }) {
  const router = useRouter();
  const [searches, setSearches] = useState(initial);
  const [keywords, setKeywords] = useState("");
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState<Record<string, string>>({});

  async function add() {
    const list = keywords
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);
    if (list.length === 0) return;
    setBusy(true);
    try {
      const response = await fetch("/api/saved-searches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keywords: list, remote_only: true }),
      });
      if (response.ok) {
        const created = (await response.json()) as SavedSearch;
        setSearches((s) => [...s, created]);
        setKeywords("");
      }
    } finally {
      setBusy(false);
    }
  }

  async function run(id: string) {
    setResults((r) => ({ ...r, [id]: "Checking…" }));
    const response = await fetch(`/api/saved-searches/${id}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ send_email: true }),
    });
    const data = await response.json();
    if (!response.ok) {
      setResults((r) => ({ ...r, [id]: data.error ?? "Couldn't check." }));
      return;
    }
    const emailNote = data.emailed
      ? " — emailed to you"
      : data.email_configured
        ? ""
        : " (set up email to get these daily)";
    setResults((r) => ({
      ...r,
      [id]: data.new_count === 0 ? "No new matches yet" : `${data.new_count} new match(es)${emailNote}`,
    }));
    router.refresh();
  }

  async function remove(id: string) {
    await fetch(`/api/saved-searches/${id}`, { method: "DELETE" });
    setSearches((s) => s.filter((x) => x.id !== id));
  }

  return (
    <div className="card mb-6 p-5">
      <div className="eyebrow mb-2">Saved searches</div>
      <p className="mb-3 text-sm text-muted">
        Save a search and check it for only the new matches since last time.
      </p>
      <div className="flex flex-wrap gap-2">
        <input
          className="input flex-1"
          placeholder="Keywords, comma-separated — e.g. growth, ppc, lifecycle"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
        />
        <button onClick={add} disabled={busy || !keywords.trim()} className="btn-ghost text-sm">
          Save search
        </button>
      </div>

      {searches.length > 0 && (
        <ul className="mt-4 space-y-2">
          {searches.map((s) => (
            <li
              key={s.id}
              className="flex flex-wrap items-center gap-3 rounded-lg border border-lineSoft bg-ink/40 px-3 py-2"
            >
              <span className="text-sm text-white/85">{s.keywords.join(", ")}</span>
              <button
                onClick={() => run(s.id)}
                className="text-xs text-accentSoft transition hover:underline"
              >
                Check for new matches
              </button>
              {results[s.id] && <span className="text-xs text-muted">{results[s.id]}</span>}
              <button
                onClick={() => remove(s.id)}
                className="ml-auto text-xs text-muted transition hover:text-white"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
