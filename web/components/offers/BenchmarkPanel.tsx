"use client";

import { useState } from "react";
import type { Benchmark } from "@/lib/api";

const LEVELS = ["", "entry", "mid", "senior", "lead"];

export function BenchmarkPanel() {
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("");
  const [anchor, setAnchor] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Benchmark | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function estimate() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/offers/benchmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role,
          level: level || null,
          anchor_salary: anchor ? Number(anchor) : null,
        }),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Couldn't estimate.");
      else setResult(data);
    } finally {
      setBusy(false);
    }
  }

  const money = (n: number) =>
    result ? `${result.currency} ${n.toLocaleString()}` : `${n.toLocaleString()}`;

  return (
    <section className="card mb-6 p-5">
      <div className="eyebrow mb-2">Pay benchmark</div>
      <p className="mb-3 text-sm text-muted">
        A rough target range for a role before you apply or negotiate. Add a comparable salary you
        know for a sharper, local number.
      </p>
      <div className="flex flex-wrap gap-2">
        <input
          className="input flex-1"
          placeholder="Target role — e.g. Senior Growth Marketer"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        />
        <select
          className="input w-auto"
          value={level}
          onChange={(e) => setLevel(e.target.value)}
        >
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {l ? l[0].toUpperCase() + l.slice(1) : "Auto level"}
            </option>
          ))}
        </select>
        <input
          className="input w-40"
          type="number"
          placeholder="Comparable $ (optional)"
          value={anchor}
          onChange={(e) => setAnchor(e.target.value)}
        />
        <button onClick={estimate} disabled={busy || !role.trim()} className="btn text-sm">
          {busy ? "Estimating…" : "Estimate"}
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

      {result && (
        <div className="mt-5 border-t border-lineSoft pt-4">
          <div className="grid grid-cols-3 gap-3 text-center">
            {[
              ["Low", result.low],
              ["Midpoint", result.mid],
              ["High", result.high],
            ].map(([label, value]) => (
              <div key={label as string} className="rounded-xl border border-line bg-ink/40 p-3">
                <div className="text-xs text-muted">{label}</div>
                <div className="mt-1 font-display text-lg font-semibold">{money(value as number)}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 rounded-xl border border-accent/30 bg-accent/[0.06] p-3">
            <div className="text-xs text-accent/90">Suggested ask</div>
            <div className="font-display text-2xl font-semibold text-white">
              {money(result.suggested_ask)}
            </div>
          </div>
          <p className="mt-3 text-sm text-white/80">
            {result.rationale}{" "}
            <span className="text-muted">({result.confidence})</span>
          </p>
          <p className="mt-2 text-xs text-muted">{result.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
