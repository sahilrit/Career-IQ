"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function AccountDataCard() {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function del() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/account", { method: "DELETE" });
      if (!response.ok) {
        setError((await response.json()).error ?? "Couldn't delete account.");
        return;
      }
      router.push("/login");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card p-6">
      <h2 className="mb-1 text-sm uppercase tracking-wide text-muted">Account &amp; data</h2>
      <p className="mb-4 text-sm text-muted">
        Export everything CareerOS holds about you, or permanently delete your account.
      </p>

      <a href="/api/account/export" className="btn-ghost text-sm">
        Download my data (JSON)
      </a>

      <div className="mt-6 border-t border-red-500/20 pt-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-400">
          Danger zone
        </div>
        {!confirming ? (
          <button
            onClick={() => setConfirming(true)}
            className="mt-2 rounded-full border border-red-500/40 px-4 py-2 text-sm text-red-400 transition hover:bg-red-500/10"
          >
            Delete my account
          </button>
        ) : (
          <div className="mt-3 space-y-3">
            <p className="text-sm text-white/85">
              This permanently deletes your account and all your data — Career Brain, applications,
              documents, everything. This cannot be undone. Type <b>DELETE</b> to confirm.
            </p>
            <input
              className="input max-w-xs"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="DELETE"
            />
            <div className="flex items-center gap-3">
              <button
                onClick={del}
                disabled={busy || text !== "DELETE"}
                className="rounded-full bg-red-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-600 disabled:opacity-40"
              >
                {busy ? "Deleting…" : "Permanently delete"}
              </button>
              <button
                onClick={() => {
                  setConfirming(false);
                  setText("");
                }}
                className="text-sm text-muted hover:text-white"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </div>
    </section>
  );
}
