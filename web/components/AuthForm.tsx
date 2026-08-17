"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FadeIn } from "@/components/Motion";

type Mode = "login" | "signup";

export function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      // Call our own route so the token is set as an httpOnly cookie
      // server-side and never exposed to client JS.
      const response = await fetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.error ?? "Something went wrong.");
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <FadeIn>
      <form onSubmit={submit} className="card w-full max-w-md space-y-5 p-8 sm:p-10">
        <h1 className="font-display text-2xl font-semibold sm:text-3xl">
          {mode === "login" ? "Welcome back" : "Create your account"}
        </h1>
        {mode === "signup" && (
          <div>
            <label className="label">Full name</label>
            <input
              className="input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>
        )}
        <div>
          <label className="label">Email</label>
          <input
            className="input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">Password</label>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {mode === "signup" && (
            <p className="mt-1.5 text-xs text-muted">
              12+ characters, with an uppercase letter, a digit, and a symbol.
            </p>
          )}
          {mode === "login" && (
            <p className="mt-1.5 text-right text-xs">
              <Link href="/forgot" className="text-muted hover:text-white">
                Forgot password?
              </Link>
            </p>
          )}
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="btn w-full" disabled={busy}>
          {busy ? "…" : mode === "login" ? "Log in" : "Create account"}
        </button>
        <p className="text-center text-sm text-muted">
          {mode === "login" ? (
            <>
              No account?{" "}
              <Link href="/signup" className="text-accentSoft hover:underline">
                Sign up
              </Link>
            </>
          ) : (
            <>
              Already have one?{" "}
              <Link href="/login" className="text-accentSoft hover:underline">
                Log in
              </Link>
            </>
          )}
        </p>
      </form>
    </FadeIn>
  );
}
