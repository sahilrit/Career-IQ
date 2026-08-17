import Link from "next/link";
import { redirect } from "next/navigation";
import { getToken } from "@/lib/session";
import { Reveal, Float } from "@/components/Motion";
import { Wordmark } from "@/components/Wordmark";
import { AuroraBackground } from "@/components/landing/AuroraBackground";
import { ProductPreview } from "@/components/landing/ProductPreview";

const STEPS = [
  {
    n: "01",
    title: "Build your Career Brain",
    body: "Upload your résumé or type it in. One authoritative record of your experience — the source everything is written from.",
  },
  {
    n: "02",
    title: "Find the right work",
    body: "Jobs and freelance clients discovered and scored against your real profile. Matches worth your time, not a firehose.",
  },
  {
    n: "03",
    title: "Win it",
    body: "Tailored résumés, cover letters, and pitch kits — grounded in your facts. Apply, pitch, and book interviews in-app.",
  },
];

const PLANS = [
  { name: "Free", price: "$0", points: ["Career Brain", "Job discovery", "Applications & pitch kits"] },
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

function FeatureCard({
  title,
  body,
  className = "",
  large = false,
}: {
  title: string;
  body: string;
  className?: string;
  large?: boolean;
}) {
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border border-line bg-panel/70 p-6 backdrop-blur-sm transition hover:border-accent/40 ${className}`}
    >
      <div
        className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-accent/10 blur-2xl opacity-0 transition group-hover:opacity-100"
        aria-hidden
      />
      <h3 className={`font-display font-medium ${large ? "text-2xl" : "text-lg"}`}>{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
      {large && (
        <div className="mt-6 grid grid-cols-3 gap-2">
          {["Résumé", "Skills", "Wins"].map((t) => (
            <div key={t} className="rounded-lg border border-line bg-ink/50 p-3">
              <div className="font-mono text-[10px] uppercase tracking-widest text-accent/80">{t}</div>
              <div className="mt-2 h-1.5 w-10/12 rounded bg-white/10" />
              <div className="mt-1 h-1.5 w-8/12 rounded bg-white/[0.07]" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Home() {
  if (getToken()) redirect("/dashboard");

  return (
    <div className="relative overflow-hidden">
      <AuroraBackground />

      {/* Sticky glass header */}
      <header className="sticky top-0 z-30 border-b border-lineSoft/60 bg-ink/50 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <Wordmark />
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-white/75 transition hover:text-white">
              Log in
            </Link>
            <Link href="/signup" className="btn text-sm">
              Get started
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        {/* Hero */}
        <section className="grid items-center gap-12 py-20 sm:py-28 lg:grid-cols-2">
          <Reveal>
            <div className="eyebrow mb-6">The operating system for your career</div>
            <h1 className="font-display text-5xl font-semibold leading-[1.02] tracking-tightest sm:text-6xl">
              Run your career like a <span className="italic text-accent">company.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">
              CareerOS turns your real experience into a Career Brain, finds the jobs and freelance
              clients worth pursuing, and writes the applications and pitches to win them — on
              autopilot when you want it.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
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
          </Reveal>

          <Float className="[perspective:1200px]">
            <ProductPreview />
          </Float>
        </section>

        {/* How it works */}
        <section className="border-t border-lineSoft py-20">
          <Reveal>
            <div className="eyebrow mb-3">How it works</div>
            <h2 className="mb-12 max-w-2xl font-display text-3xl font-medium tracking-tightest sm:text-4xl">
              Three moves, from blank page to booked interview.
            </h2>
          </Reveal>
          <div className="grid gap-6 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <Reveal key={step.n} delay={i * 0.1}>
                <div className="card h-full p-7">
                  <div className="font-mono text-2xl text-accent">{step.n}</div>
                  <h3 className="mt-4 font-display text-xl font-medium">{step.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted">{step.body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* Bento features */}
        <section className="border-t border-lineSoft py-20">
          <Reveal>
            <div className="eyebrow mb-3">Everything in one workspace</div>
            <h2 className="mb-10 max-w-2xl font-display text-3xl font-medium tracking-tightest sm:text-4xl">
              A whole career team, working for one person — you.
            </h2>
          </Reveal>
          <Reveal>
            <div className="grid gap-4 md:grid-cols-3 md:grid-rows-3">
              <FeatureCard
                large
                className="md:col-span-2 md:row-span-2"
                title="Career Brain"
                body="One authoritative profile of your experience, skills, and wins — the single source every résumé, cover letter, and pitch is generated from. Nothing fabricated."
              />
              <FeatureCard
                title="AI applications"
                body="A tailored résumé and cover letter for every posting, in seconds."
              />
              <FeatureCard
                title="Opportunity discovery"
                body="Jobs and freelance clients found and scored against your profile."
              />
              <FeatureCard
                title="Autopilot"
                body="Applies across open ATS boards — safely, with human handoffs."
                className="md:col-span-1"
              />
              <FeatureCard
                title="Freelance engine"
                body="Prospects, live site audits, pitch kits, clients, and income — the whole money-maker."
                className="md:col-span-2"
              />
            </div>
          </Reveal>
        </section>

        {/* Pricing */}
        <section className="border-t border-lineSoft py-20">
          <Reveal>
            <div className="eyebrow mb-3">Pricing</div>
            <h2 className="mb-10 font-display text-3xl font-medium tracking-tightest sm:text-4xl">
              Start free. Upgrade when it pays for itself.
            </h2>
          </Reveal>
          <div className="grid gap-5 md:grid-cols-3">
            {PLANS.map((plan, i) => (
              <Reveal key={plan.name} delay={i * 0.1}>
                <div className={`card h-full p-7 ${plan.featured ? "ring-1 ring-accent/60" : ""}`}>
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
              </Reveal>
            ))}
          </div>
        </section>

        {/* Closing */}
        <section className="border-t border-lineSoft py-24 text-center">
          <Reveal>
            <h2 className="mx-auto max-w-2xl font-display text-4xl font-medium tracking-tightest sm:text-5xl">
              Your next role is out there. Go run at it.
            </h2>
            <div className="mt-8">
              <Link href="/signup" className="btn">
                Start free →
              </Link>
            </div>
          </Reveal>
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
    </div>
  );
}
