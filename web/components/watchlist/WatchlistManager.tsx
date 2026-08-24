"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { WatchedCompany, WatchlistNewPosting } from "@/lib/api";

const ATS_OPTIONS = [
  { value: "greenhouse", label: "Greenhouse" },
  { value: "lever", label: "Lever" },
  { value: "ashby", label: "Ashby" },
];

export function WatchlistManager({ initial }: { initial: WatchedCompany[] }) {
  const router = useRouter();
  const [watched, setWatched] = useState<WatchedCompany[]>(initial);
  const [form, setForm] = useState({ ats: "greenhouse", board_token: "", display_name: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [found, setFound] = useState<WatchlistNewPosting[] | null>(null);
  const [checkNote, setCheckNote] = useState<string | null>(null);

  async function addCompany() {
    if (!form.board_token.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/watchlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.error ?? "Couldn't add that company.");
        return;
      }
      setWatched((prev) => [
        ...prev.filter((c) => !(c.ats === data.ats && c.board_token === data.board_token)),
        data,
      ]);
      setForm({ ats: form.ats, board_token: "", display_name: "" });
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  async function remove(company: WatchedCompany) {
    await fetch(`/api/watchlist/${company.ats}/${company.board_token}`, { method: "DELETE" });
    setWatched((prev) =>
      prev.filter((c) => !(c.ats === company.ats && c.board_token === company.board_token)),
    );
    router.refresh();
  }

  async function check() {
    setBusy(true);
    setError(null);
    setFound(null);
    setCheckNote(null);
    try {
      const response = await fetch("/api/watchlist/check", { method: "POST" });
      const data = await response.json();
      if (!response.ok) {
        setError(data.error ?? "Couldn't check the boards.");
        return;
      }
      setFound(data.new_postings);
      setCheckNote(
        data.baselined > 0 && data.new_postings.length === 0
          ? `Set a baseline for ${data.baselined} newly-added board(s). New roles will show from now on.`
          : data.new_postings.length === 0
            ? `No new roles across ${data.checked} board(s).`
            : `${data.new_postings.length} new role(s) across ${data.checked} board(s).`,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="card p-5">
        <div className="eyebrow mb-3">Watch a company</div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex flex-col text-sm">
            <span className="label">ATS</span>
            <select
              className="input"
              value={form.ats}
              onChange={(e) => setForm({ ...form, ats: e.target.value })}
            >
              {ATS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <div className="flex-1">
            <span className="label">Board token</span>
            <input
              className="input"
              placeholder="stripe"
              value={form.board_token}
              onChange={(e) => setForm({ ...form, board_token: e.target.value })}
            />
          </div>
          <div className="flex-1">
            <span className="label">Display name (optional)</span>
            <input
              className="input"
              placeholder="Stripe"
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
            />
          </div>
          <button className="btn" disabled={busy || !form.board_token.trim()} onClick={addCompany}>
            {busy ? "…" : "Watch"}
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      </div>

      <div className="card p-5">
        <div className="mb-3 flex items-center justify-between">
          <div className="eyebrow">Watched companies</div>
          {watched.length > 0 && (
            <button className="btn-ghost text-sm" disabled={busy} onClick={check}>
              {busy ? "Checking…" : "Check for new roles"}
            </button>
          )}
        </div>
        {watched.length === 0 ? (
          <p className="text-sm text-muted">Nothing watched yet — add a company above.</p>
        ) : (
          <ul className="divide-y divide-line">
            {watched.map((company) => (
              <li
                key={`${company.ats}:${company.board_token}`}
                className="flex items-center justify-between py-2.5"
              >
                <div>
                  <span className="text-white">
                    {company.display_name || company.board_token}
                  </span>
                  <span className="ml-2 chip">{company.ats}</span>
                </div>
                <button
                  className="text-sm text-muted hover:text-red-400"
                  onClick={() => remove(company)}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
        {checkNote && <p className="mt-3 text-sm text-emerald-400">{checkNote}</p>}
      </div>

      {found && found.length > 0 && (
        <div className="card p-5">
          <div className="eyebrow mb-3">New roles</div>
          <ul className="space-y-2">
            {found.map((posting) => (
              <li key={posting.external_id} className="flex justify-between gap-3 text-sm">
                <a
                  href={posting.url}
                  target="_blank"
                  rel="noreferrer"
                  className="truncate text-white hover:text-accent"
                >
                  {posting.title}
                </a>
                <span className="shrink-0 text-muted">{posting.company_name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
