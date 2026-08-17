"use client";

import { useState } from "react";
import Link from "next/link";
import { FadeIn } from "@/components/Motion";

export function ResetPasswordForm({ token }: { token: string }) {
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const response = await fetch("/api/auth/reset-confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Couldn't reset the password.");
      else setDone(true);
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <div className="card w-full max-w-sm p-7 text-sm text-muted">
        This reset link is missing its token. Request a new one from{" "}
        <Link href="/forgot" className="text-accentSoft hover:underline">
          the reset page
        </Link>
        .
      </div>
    );
  }

  return (
    <FadeIn>
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4 p-7">
        <h1 className="text-xl font-semibold">Set a new password</h1>
        {done ? (
          <p className="text-sm text-emerald-400">
            Password updated. You can now{" "}
            <Link href="/login" className="hover:underline">
              log in
            </Link>
            .
          </p>
        ) : (
          <>
            <div>
              <label className="label">New password</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
              <p className="mt-1.5 text-xs text-muted">
                12+ characters, with an uppercase letter, a digit, and a symbol.
              </p>
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <button className="btn w-full" disabled={busy}>
              {busy ? "…" : "Reset password"}
            </button>
          </>
        )}
      </form>
    </FadeIn>
  );
}
