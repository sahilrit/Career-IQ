import Link from "next/link";
import type { ReactNode } from "react";

// Shared shell for the public legal pages (no auth, no app Shell).
export function LegalPage({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <Link href="/" className="text-sm text-muted transition hover:text-white">
        ← CareerOS
      </Link>
      <h1 className="mt-6 text-3xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 text-sm text-muted">Last updated: 17 August 2026</p>

      <div className="mt-4 rounded-xl border border-line bg-panel/60 p-4 text-sm text-muted">
        This is a general starting template, not legal advice. Have it reviewed by a
        qualified professional and replace the bracketed placeholders before you rely on it.
      </div>

      <div className="legal mt-8 space-y-6 text-sm leading-relaxed text-white/85">{children}</div>

      <div className="mt-12 border-t border-line pt-6 text-sm text-muted">
        <Link href="/terms" className="mr-4 transition hover:text-white">
          Terms
        </Link>
        <Link href="/privacy" className="transition hover:text-white">
          Privacy
        </Link>
      </div>
    </div>
  );
}

export function Section({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <section>
      <h2 className="mb-2 text-lg font-medium text-white">{heading}</h2>
      <div className="space-y-2">{children}</div>
    </section>
  );
}
