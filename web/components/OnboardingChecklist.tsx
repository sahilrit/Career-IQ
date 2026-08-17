import Link from "next/link";
import type { Onboarding } from "@/lib/api";

// Server component — renders the first-run checklist; hides itself once
// every step is done.
export function OnboardingChecklist({ data }: { data: Onboarding }) {
  if (data.complete) return null;
  return (
    <section className="card mb-6 p-6">
      <h2 className="mb-1 text-sm uppercase tracking-wide text-muted">Get set up</h2>
      <p className="mb-4 text-sm text-muted">A few steps to get the most out of CareerOS.</p>
      <ul className="space-y-2">
        {data.steps.map((step) => (
          <li key={step.key}>
            <Link
              href={step.href}
              className={`flex items-center gap-3 rounded-lg border border-line px-3 py-2 text-sm transition hover:border-accentSoft ${
                step.done ? "text-muted" : "text-white"
              }`}
            >
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs ${
                  step.done ? "bg-accent/20 text-accentSoft" : "border border-line"
                }`}
              >
                {step.done ? "✓" : ""}
              </span>
              <span className={step.done ? "line-through" : ""}>{step.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
