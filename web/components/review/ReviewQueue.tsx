"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { PreparedApplication } from "@/lib/api";
import { FadeIn } from "@/components/Motion";

export function ReviewQueue({ initial }: { initial: PreparedApplication[] }) {
  const router = useRouter();
  const [items, setItems] = useState<PreparedApplication[]>(initial);
  const [openId, setOpenId] = useState<string | null>(null);
  const [, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  async function update(id: string, status: "submitted" | "dismissed") {
    const previous = items;
    setItems((current) => current.filter((item) => item.id !== id)); // optimistic
    setError(null);
    try {
      const response = await fetch(`/api/review/prepared/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) throw new Error();
      startTransition(() => router.refresh());
    } catch {
      setItems(previous); // roll back on failure
      setError("Couldn't update — try again.");
    }
  }

  if (items.length === 0) {
    return (
      <div className="card p-6 text-muted">
        Nothing to review yet. Run <span className="text-white/80">prepare &amp; review</span>{" "}
        (mode 2 in <code className="rounded bg-panel px-1.5 py-0.5 text-white/80">apply.sh</code>) to
        fill captcha-gated forms — they&apos;ll show up here for you to finish.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && <p className="text-sm text-red-400">{error}</p>}
      {items.map((item) => {
        const open = openId === item.id;
        return (
          <FadeIn key={item.id}>
            <div className="card p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-medium text-white/90">{item.job_title}</div>
                  <div className="text-sm text-muted">
                    {item.company_name}
                    {item.match_score != null && (
                      <span className="ml-2 text-emerald-400">
                        {Math.round(item.match_score * 100)}% match
                      </span>
                    )}
                  </div>
                </div>
                <a
                  href={item.apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn shrink-0"
                >
                  Open form ↗
                </a>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  className="btn-ghost text-sm"
                  onClick={() => setOpenId(open ? null : item.id)}
                >
                  {open ? "Hide cover letter" : "Show cover letter"}
                </button>
                <button className="btn-ghost text-sm" onClick={() => update(item.id, "submitted")}>
                  ✓ I applied
                </button>
                <button
                  className="btn-ghost text-sm text-muted"
                  onClick={() => update(item.id, "dismissed")}
                >
                  Dismiss
                </button>
              </div>

              {open && (
                <pre className="mt-3 whitespace-pre-line rounded-lg bg-panel p-4 text-sm text-white/80">
                  {item.cover_letter || "(no cover letter generated)"}
                </pre>
              )}
            </div>
          </FadeIn>
        );
      })}
    </div>
  );
}
