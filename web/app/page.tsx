import Link from "next/link";
import { redirect } from "next/navigation";
import { getToken } from "@/lib/session";
import { FadeIn, Stagger, StaggerItem } from "@/components/Motion";

const STEPS = [
  {
    n: "01",
    title: "Build your Career Brain",
    body: "Upload your résumé or type it in. One authoritative record of your experience, skills, and wins — the source everything else is written from.",
  },
  {
    n: "02",
    title: "Find the right work",
    body: "Jobs and freelance clients discovered and scored against your real profile — matches worth your time, not a firehose.",
  },
  {
    n: "03",
    title: "Win it",
    body: "Tailored résumés, cover letters, and pitch kits — written by AI, grounded in your facts. Apply, pitch, and book interviews without leaving the app.",
  },
];

const FEATURES = [
  ["Career Brain", "One authoritative profile powering every résumé and pitch."],
  ["Opportunity discovery", "Jobs and freelance clients found and scored for you."],
  ["AI applications", "Tailored résumé and cover letter for every posting."],
  ["Autopilot", "Applies across open ATS boards — safely, with handoffs."],
  ["Freelance engine", "Prospects, live site audits, pitch kits, clients, and income."],
  ["Private by design", "Your workspace is isolated, encrypted, and yours to export or delete."],
];

const PLANS = [
  { name: "Free", price: "$0", points: ["Career Brain", "Job discovery", "Basic applications"] },
  {
    name: "Pro",
    price: "$29",
    points: ["Everything in Free", "Autopilot", "Freelance acquisition", "Analytics"],
    featured: true,
  },
  {
    name: "Agency",
    price: "$99",
    points: ["Everything in Pro", "Multiple workspaces", "Team members", "API access"],
  },
];

function Wordmark() {
  return (
    <span className="flex items-center gap-2.5">
      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent font-display text-base font-semibold text-accentInk shadow-glow">
        C
      </span>
      <span className="font-display text-xl font-semibold tracking-tightest">CareerOS</span>
    </span>
  );
}

export default function Home() {
  if (getToken()) redirect("/dashboard");

  return (
    <div className="mx-auto max-w-6xl px-5 py-6 sm:px-8">
      <header className="flex items-center justify-between">
        <Wordmark />
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm text-white/75 transition hover:text-white">
            Log in
          </Link>
          <Link href="/signup" className="btn text-sm">
            Get started
          </Link>
        </div>
      </header>

      {/* Hero — the thesis */}
      <FadeIn>
        <section className="py-24 sm:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <div className="eyebrow mb-6">The operating system for your career</div>
            <h1 className="font-display text-5xl font-semibold leading-[1.02] tracking-tightest sm:text-7xl">
              Run your career like a{" "}
              <span className="italic text-accent">company.</span>
            </h1>
            <p className="mx-auto mt-7 max-w-2xl text-lg leading-relaxed text-muted">
              CareerOS turns your real experience into a Career Brain, finds the jobs and freelance
              clients worth pursuing, and writes the applications and pitches to win them — on
              autopilot when you want it.
            </p>
            <div className="mt-9 flex items-center justify-center gap-3">
              <Link href="/signup" className="btn">
                Start free →
              </Link>
              <Link href="/login" className="btn-ghost">
                Log in
              </Link>
            </div>
            <p className="mt-6 font-mono text-xs uppercase tracking-[0.2em] text-muted/70">
              No credit card · Free forever tier · Bring your own AI key
            </p>
          </div>
        </section>
      </FadeIn>

      {/* How it works — a real sequence */}
      <section className="border-t border-lineSoft py-20">
        <h2 className="mb-12 max-w-2xl font-display text-3xl font-medium tracking-tightest sm:text-4xl">
          Three moves, from blank page to booked interview.
        </h2>
        <Stagger>
          <div className="grid gap-6 md:grid-cols-3">
            {STEPS.map((step) => (
              <StaggerItem key={step.n}>
                <div className="card h-full p-7">
                  <div className="font-mono text-2xl text-accent">{step.n}</div>
                  <h3 className="mt-4 font-display text-xl font-medium">{step.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted">{step.body}</p>
                </div>
              </StaggerItem>
            ))}
          </div>
        </Stagger>
      </section>

      {/* Feature grid */}
      <section className="border-t border-lineSoft py-20">
        <div className="eyebrow mb-3">Everything in one workspace</div>
        <h2 className="mb-10 max-w-2xl font-display text-3xl font-medium tracking-tightest sm:text-4xl">
          A whole career team, working for one person — you.
        </h2>
        <div className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(([title, body]) => (
            <div key={title} className="bg-panel p-7">
              <h3 className="font-display text-lg font-medium">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="border-t border-lineSoft py-20">
        <div className="eyebrow mb-3">Pricing</div>
        <h2 className="mb-10 font-display text-3xl font-medium tracking-tightest sm:text-4xl">
          Start free. Upgrade when it pays for itself.
        </h2>
        <div className="grid gap-5 md:grid-cols-3">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`card p-7 ${plan.featured ? "ring-1 ring-accent/60" : ""}`}
            >
              {plan.featured && <div className="eyebrow mb-3">Most popular</div>}
              <div className="font-display text-lg font-medium">{plan.name}</div>
              <div className="mb-5 mt-1 font-display text-4xl font-semibold tracking-tightest">
                {plan.price}
                <span className="text-base font-normal text-muted">/mo</span>
              </div>
              <ul className="mb-7 space-y-2 text-sm text-muted">
                {plan.points.map((point) => (
                  <li key={point} className="flex items-start gap-2">
                    <span className="mt-1 text-accent">·</span>
                    {point}
                  </li>
                ))}
              </ul>
              <Link href="/signup" className={plan.featured ? "btn w-full" : "btn-ghost w-full"}>
                Get started
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Closing */}
      <section className="border-t border-lineSoft py-24 text-center">
        <h2 className="mx-auto max-w-2xl font-display text-3xl font-medium tracking-tightest sm:text-5xl">
          Your next role is out there. Go run at it.
        </h2>
        <div className="mt-8">
          <Link href="/signup" className="btn">
            Start free →
          </Link>
        </div>
      </section>

      <footer className="flex flex-col items-center justify-between gap-3 border-t border-lineSoft py-8 text-sm text-muted sm:flex-row">
        <Wordmark />
        <div className="flex items-center gap-4">
          <Link href="/terms" className="transition hover:text-white">
            Terms
          </Link>
          <Link href="/privacy" className="transition hover:text-white">
            Privacy
          </Link>
        </div>
      </footer>
    </div>
  );
}
