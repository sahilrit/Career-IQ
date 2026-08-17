"use client";

import { useState } from "react";
import Link from "next/link";
import { FadeIn } from "@/components/Motion";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await fetch("/api/auth/reset-request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setSent(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <FadeIn>
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4 p-7">
        <h1 className="text-xl font-semibold">Reset your password</h1>
        {sent ? (
          <p className="text-sm text-muted">
            If that email has an account, a reset link is on its way. Check your inbox, then follow
            the link to set a new password.
          </p>
        ) : (
          <>
            <p className="text-sm text-muted">
              Enter your email and we&apos;ll send you a link to set a new password.
            </p>
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
            <button className="btn w-full" disabled={busy}>
              {busy ? "…" : "Send reset link"}
            </button>
          </>
        )}
        <p className="text-center text-sm text-muted">
          <Link href="/login" className="text-accentSoft hover:underline">
            Back to log in
          </Link>
        </p>
      </form>
    </FadeIn>
  );
}
