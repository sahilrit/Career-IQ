"use client";

import { useRef } from "react";
import Link from "next/link";
import { motion, useScroll, useSpring, useTransform } from "framer-motion";
import { Reveal, Reveal3D } from "@/components/Motion";
import { Wordmark } from "@/components/Wordmark";
import { AuroraBackground } from "@/components/landing/AuroraBackground";
import { HeroStack } from "@/components/landing/HeroStack";

// --- Content -----------------------------------------------------------------

const CAPABILITIES = [
  {
    tag: "Career Brain",
    title: "One brain for your whole career.",
    body: "Every role, result, and skill in a single authoritative record. It's the source every résumé, application, and pitch is written from — so nothing is invented, nothing is exaggerated, and you never rewrite the same story twice.",
    points: ["Résumé & links in, structured profile out", "Grounds every AI draft in real facts"],
  },
  {
    tag: "Discovery",
    title: "It finds the work. You pick the winners.",
    body: "Jobs and freelance clients pulled in and scored against your actual profile — not a keyword feed to drown in. You wake up to a shortlist worth your time, ranked by how well it fits you.",
    points: ["Scored against your Career Brain", "Roles and retainer clients in one queue"],
  },
  {
    tag: "Applications",
    title: "A tailored application in the time it takes to read one.",
    body: "A résumé and cover letter rewritten for each posting, grounded in your facts. Turn autopilot on and it applies across open boards for you — with a human handoff before anything is sent.",
    points: ["Per-posting résumé + cover letter", "Apply and book interviews in-app"],
  },
  {
    tag: "Pitch Kit",
    title: "Turn a cold prospect into a signed client.",
    body: "Audit any storefront live, put a number on the revenue they're leaving on the table, and generate the proposal, outreach email, and Loom script to win the deal. Your freelance money-maker, in one click.",
    points: ["Live site audit → ROI in dollars", "Proposal, email & script, ready to send"],
  },
];

const SUITE = [
  ["Autopilot", "Applies across open ATS boards, safely, with you in the loop."],
  ["Client success", "Contracts, invoices, and outstanding balances tracked to the dollar."],
  ["Interview prep", "Role-specific questions and a company briefing before every call."],
  ["Personal brand", "Turn your wins into posts and case studies that get you found."],
  ["Learning lab", "Run experiments on your outreach and keep what actually converts."],
  ["Career intel", "Signals on roles, pay, and direction — where to point yourself next."],
];

const STEPS = [
  ["Build your brain", "Drop in your résumé or type it out. One record of everything you've done."],
  ["Find the work", "Roles and clients scored against you. A shortlist, not a firehose."],
  ["Win it", "Tailored applications and pitches. Apply, pitch, and book — in-app."],
];

const PLANS = [
  {
    name: "Free",
    price: "$0",
    note: "Everything to run your search",
    points: ["Career Brain", "Job & client discovery", "AI applications & pitch kits"],
    featured: false,
  },
  {
    name: "Pro",
    price: "$29",
    note: "For people who mean it",
    points: ["Everything in Free", "Autopilot applications", "Freelance acquisition engine", "Performance analytics"],
    featured: true,
  },
  {
    name: "Agency",
    price: "$99",
    note: "Run it for a whole roster",
    points: ["Everything in Pro", "Multiple workspaces", "Team members", "API access"],
    featured: false,
  },
];

// --- Scroll-linked capability row --------------------------------------------

function DepthRow({
  index,
  capability,
}: {
  index: number;
  capability: (typeof CAPABILITIES)[number];
}) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 0.9", "center 0.55"],
  });
  const progress = useSpring(scrollYProgress, { stiffness: 90, damping: 28, mass: 0.5 });
  const flip = index % 2 === 1;
  const x = useTransform(progress, [0, 1], [flip ? 90 : -90, 0]);
  const rotateY = useTransform(progress, [0, 1], [flip ? -14 : 14, 0]);
  const opacity = useTransform(progress, [0, 0.6], [0, 1]);

  return (
    <div
      ref={ref}
      className={`grid items-center gap-8 py-14 md:grid-cols-2 md:gap-16 ${flip ? "" : ""}`}
      style={{ perspective: 1300 }}
    >
      <motion.div
        style={{ x, rotateY, opacity, transformStyle: "preserve-3d" }}
        className={flip ? "md:order-2" : ""}
      >
        <div className="font-mono text-xs uppercase tracking-[0.22em] text-accent/80">
          {String(index + 1).padStart(2, "0")} · {capability.tag}
        </div>
        <h3 className="mt-4 font-display text-3xl font-medium tracking-tightest sm:text-4xl">
          {capability.title}
        </h3>
        <p className="mt-4 max-w-md text-base leading-relaxed text-muted">{capability.body}</p>
        <ul className="mt-6 space-y-2">
          {capability.points.map((p) => (
            <li key={p} className="flex items-start gap-2.5 text-sm text-white/80">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              {p}
            </li>
          ))}
        </ul>
      </motion.div>

      <motion.div
        style={{ opacity, transformStyle: "preserve-3d" }}
        className={flip ? "md:order-1" : ""}
      >
        <div className="relative">
          <div
            className="absolute -inset-6 rounded-[2rem] bg-accent/10 blur-3xl"
            aria-hidden
          />
          <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/10 bg-panel/70 p-6 shadow-card backdrop-blur">
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
              <span className="ml-2 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
                careeros / {capability.tag.toLowerCase().replace(/\s+/g, "-")}
              </span>
            </div>
            <div className="mt-5 flex h-full flex-col justify-center gap-3">
              <div className="font-display text-5xl font-semibold tracking-tightest text-accent/90">
                {String(index + 1).padStart(2, "0")}
              </div>
              <div className="space-y-2">
                <div className="h-2.5 w-11/12 rounded bg-white/12" />
                <div className="h-2.5 w-9/12 rounded bg-white/10" />
                <div className="h-2.5 w-10/12 rounded bg-white/[0.07]" />
                <div className="h-2.5 w-6/12 rounded bg-white/[0.07]" />
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// --- Page --------------------------------------------------------------------

export function Landing() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const heroText = useTransform(scrollYProgress, [0, 1], [0, -120]);
  const heroFade = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  return (
    <div className="relative overflow-hidden">
      <AuroraBackground />

      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-lineSoft/60 bg-ink/40 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <Wordmark />
          <nav className="hidden items-center gap-7 md:flex">
            <a href="#workspace" className="text-sm text-white/70 transition hover:text-white">
              Workspace
            </a>
            <a href="#suite" className="text-sm text-white/70 transition hover:text-white">
              Suite
            </a>
            <a href="#pricing" className="text-sm text-white/70 transition hover:text-white">
              Pricing
            </a>
          </nav>
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
        <section ref={heroRef} className="grid items-center gap-10 py-20 sm:py-28 lg:grid-cols-[1.05fr_1fr]">
          <motion.div style={{ y: heroText, opacity: heroFade }}>
            <Reveal>
              <div className="eyebrow mb-6">Career operating system</div>
              <h1 className="font-display text-5xl font-semibold leading-[1.02] tracking-tightest sm:text-6xl xl:text-7xl">
                Run your career like a <span className="italic text-accent">company.</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">
                CareerOS learns your entire track record, finds the roles and clients worth your
                time, and writes every application and pitch to win them. You review. It runs.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link href="/signup" className="btn">
                  Start free →
                </Link>
                <a href="#workspace" className="btn-ghost">
                  See how it works
                </a>
              </div>
              <p className="mt-6 font-mono text-xs uppercase tracking-[0.2em] text-muted/70">
                Free forever tier · No card · Bring your own AI key
              </p>
            </Reveal>
          </motion.div>

          <div className="[perspective:1300px]">
            <HeroStack />
          </div>
        </section>

        {/* Workspace — capability rows that arrive from depth */}
        <section id="workspace" className="border-t border-lineSoft py-16">
          <Reveal>
            <div className="eyebrow mb-3">The workspace</div>
            <h2 className="max-w-2xl font-display text-3xl font-medium tracking-tightest sm:text-4xl">
              A whole career team, working for one person.
            </h2>
            <p className="mt-4 max-w-xl text-muted">
              Four systems that hand off to each other — from a blank page to a booked interview or a
              signed client.
            </p>
          </Reveal>
          <div className="mt-6 divide-y divide-lineSoft">
            {CAPABILITIES.map((c, i) => (
              <DepthRow key={c.tag} index={i} capability={c} />
            ))}
          </div>
        </section>

        {/* Suite — the breadth, revealed with depth */}
        <section id="suite" className="border-t border-lineSoft py-20">
          <Reveal>
            <div className="eyebrow mb-3">And the rest of the org</div>
            <h2 className="mb-10 max-w-2xl font-display text-3xl font-medium tracking-tightest sm:text-4xl">
              Every department you'd hire for, already on staff.
            </h2>
          </Reveal>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {SUITE.map(([title, body], i) => (
              <Reveal3D key={title} delay={(i % 3) * 0.08}>
                <div className="group relative h-full overflow-hidden rounded-2xl border border-line bg-panel/60 p-6 backdrop-blur-sm transition hover:border-accent/40">
                  <div
                    className="pointer-events-none absolute -right-14 -top-14 h-36 w-36 rounded-full bg-accent/10 blur-2xl opacity-0 transition group-hover:opacity-100"
                    aria-hidden
                  />
                  <h3 className="font-display text-lg font-medium">{title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
                </div>
              </Reveal3D>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section className="border-t border-lineSoft py-20">
          <Reveal>
            <div className="eyebrow mb-3">How it works</div>
            <h2 className="mb-12 max-w-2xl font-display text-3xl font-medium tracking-tightest sm:text-4xl">
              Three moves, blank page to booked.
            </h2>
          </Reveal>
          <div className="grid gap-6 md:grid-cols-3">
            {STEPS.map(([title, body], i) => (
              <Reveal3D key={title} delay={i * 0.1}>
                <div className="card h-full p-7">
                  <div className="font-mono text-2xl text-accent">{String(i + 1).padStart(2, "0")}</div>
                  <h3 className="mt-4 font-display text-xl font-medium">{title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted">{body}</p>
                </div>
              </Reveal3D>
            ))}
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="border-t border-lineSoft py-20">
          <Reveal>
            <div className="eyebrow mb-3">Pricing</div>
            <h2 className="mb-10 font-display text-3xl font-medium tracking-tightest sm:text-4xl">
              Start free. Upgrade when it's already paid for itself.
            </h2>
          </Reveal>
          <div className="grid gap-5 md:grid-cols-3">
            {PLANS.map((plan, i) => (
              <Reveal3D key={plan.name} delay={i * 0.1}>
                <div className={`card h-full p-7 ${plan.featured ? "ring-1 ring-accent/60" : ""}`}>
                  {plan.featured && <div className="eyebrow mb-3">Most popular</div>}
                  <div className="font-display text-lg font-medium">{plan.name}</div>
                  <div className="mb-1 mt-1 font-display text-4xl font-semibold tracking-tightest">
                    {plan.price}
                    <span className="text-base font-normal text-muted">/mo</span>
                  </div>
                  <div className="mb-5 text-xs text-muted">{plan.note}</div>
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
              </Reveal3D>
            ))}
          </div>
        </section>

        {/* Closing */}
        <section className="border-t border-lineSoft py-24 text-center">
          <Reveal3D>
            <h2 className="mx-auto max-w-2xl font-display text-4xl font-medium tracking-tightest sm:text-5xl">
              Your next role is already out there.
              <br />
              <span className="italic text-accent">Go run at it.</span>
            </h2>
            <div className="mt-8">
              <Link href="/signup" className="btn">
                Start free →
              </Link>
            </div>
          </Reveal3D>
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
