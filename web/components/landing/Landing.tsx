"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { Field3D } from "@/components/looks/Field3D";
import { CursorGlow, Drift } from "@/components/looks/Interactive";

const ACCENT = "#f0b544";

const MOMENTS = [
  {
    tag: "Career Brain",
    title: "It starts with a brain.",
    body: "Everything you've ever done — every role, result, and skill — in one record the AI actually uses. Every draft is grounded in it. Nothing is invented.",
    metric: { value: "100%", label: "Grounded in your facts" },
    chips: ["Meta Ads", "Growth", "SQL", "Lifecycle", "CRO"],
  },
  {
    tag: "Discovery",
    title: "It finds the work.",
    body: "Roles and freelance clients, pulled in and scored against your real profile. You wake up to a shortlist worth your time — not a feed to drown in.",
    metric: { value: "96", label: "Top match today" },
    rows: [["Growth Lead · Ramp", 96], ["Sr. PPC · Linear", 91], ["Retainer · Acme", 88]] as [string, number][],
  },
  {
    tag: "Applications",
    title: "It writes to win.",
    body: "A résumé and cover letter tailored to every posting, in seconds. Turn on autopilot and it applies for you — with a human check before anything sends.",
    metric: { value: "8s", label: "Draft ready" },
  },
  {
    tag: "Pitch Kit",
    title: "It closes clients.",
    body: "Audit any storefront live, put a number on the money they're leaving on the table, and generate the proposal, email, and script that signs them.",
    metric: { value: "$1.8M", label: "Revenue found / yr" },
  },
];

const SUITE = [
  "Autopilot",
  "Interview prep",
  "Client success",
  "Personal brand",
  "Learning lab",
  "Career intel",
  "Finance",
  "CEO agent",
];

const PLANS = [
  { name: "Free", price: "$0", note: "Everything to run your search", points: ["Career Brain", "Discovery", "AI applications & pitch kits"], featured: false },
  { name: "Pro", price: "$29", note: "For people who mean it", points: ["Everything in Free", "Autopilot", "Freelance engine", "Analytics"], featured: true },
  { name: "Agency", price: "$99", note: "Run a whole roster", points: ["Everything in Pro", "Multiple workspaces", "Team members", "API access"], featured: false },
];

// A refined, cursor-tilting glass panel — the small product moment.
function MomentVisual({ moment, index }: { moment: (typeof MOMENTS)[number]; index: number }) {
  return (
    <div className="relative mx-auto w-full max-w-md" style={{ perspective: 1400 }}>
      <div className="absolute -inset-10 rounded-[3rem] bg-accent/10 blur-3xl" aria-hidden />
      <div
        className="relative rounded-2xl border border-white/12 bg-gradient-to-br from-white/[0.06] to-white/[0.02] p-6 shadow-2xl backdrop-blur-xl"
        style={{
          transformStyle: "preserve-3d",
          transform:
            "rotateX(calc(var(--my,0) * -10deg)) rotateY(calc(var(--mx,0) * 12deg)) translate3d(calc(var(--mx,0) * 16px), calc(var(--my,0) * 16px), 0)",
          willChange: "transform",
        }}
      >
        <div
          className="pointer-events-none absolute inset-0 rounded-2xl"
          style={{ background: "linear-gradient(140deg, rgba(255,255,255,0.14), transparent 42%)" }}
          aria-hidden
        />
        <div className="flex items-center justify-between" style={{ transform: "translateZ(30px)" }}>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/55">
            careeros / {moment.tag.toLowerCase().replace(/\s+/g, "-")}
          </span>
          <span className="h-2 w-2 rounded-full" style={{ background: ACCENT }} />
        </div>

        <div
          className="mt-5 inline-flex flex-col rounded-xl border border-accent/30 bg-accent/10 px-4 py-3"
          style={{ transform: "translateZ(60px)" }}
        >
          <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-accent/90">
            {moment.metric.label}
          </span>
          <span className="mt-0.5 font-display text-3xl font-semibold text-white">{moment.metric.value}</span>
        </div>

        {/* body varies by moment */}
        <div className="mt-5" style={{ transform: "translateZ(24px)" }}>
          {moment.chips && (
            <div className="flex flex-wrap gap-1.5">
              {moment.chips.map((c) => (
                <span key={c} className="rounded-full border border-white/12 bg-white/[0.05] px-2.5 py-1 text-[11px] text-white/80">
                  {c}
                </span>
              ))}
            </div>
          )}
          {moment.rows && (
            <div className="space-y-3">
              {moment.rows.map(([label, score]) => (
                <div key={label}>
                  <div className="flex justify-between text-[11px] text-white/80">
                    <span>{label}</span>
                    <span className="font-mono" style={{ color: ACCENT }}>{score}</span>
                  </div>
                  <div className="mt-1.5 h-1.5 w-full rounded-full bg-white/10">
                    <div className="h-1.5 rounded-full" style={{ width: `${score}%`, background: ACCENT }} />
                  </div>
                </div>
              ))}
            </div>
          )}
          {!moment.chips && !moment.rows && (
            <div className="space-y-2.5">
              <div className="h-2.5 w-11/12 rounded bg-white/22" />
              <div className="h-2.5 w-9/12 rounded bg-white/16" />
              <div className="h-2.5 w-10/12 rounded bg-white/12" />
              <div className="h-2.5 w-6/12 rounded bg-white/10" />
              <div className="mt-4 inline-flex rounded-full px-4 py-1.5 text-[11px] font-medium" style={{ background: ACCENT, color: "#221704" }}>
                ✨ AI-written
              </div>
            </div>
          )}
        </div>
      </div>
      <span className="pointer-events-none absolute -left-2 -top-6 font-mono text-xs text-white/25">
        0{index + 1}
      </span>
    </div>
  );
}

function Moment({ moment, index }: { moment: (typeof MOMENTS)[number]; index: number }) {
  const flip = index % 2 === 1;
  return (
    <section className="grid items-center gap-12 py-24 sm:py-32 md:grid-cols-2 md:gap-20">
      <motion.div
        className={flip ? "md:order-2" : ""}
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "0px 0px -20% 0px" }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      >
        <Drift strength={10}>
          <div className="font-mono text-xs uppercase tracking-[0.28em] text-accent">{moment.tag}</div>
          <h2 className="mt-5 font-display text-4xl font-medium leading-[1.05] tracking-tight sm:text-5xl">
            {moment.title}
          </h2>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-white/65">{moment.body}</p>
        </Drift>
      </motion.div>

      <motion.div
        className={flip ? "md:order-1" : ""}
        initial={{ opacity: 0, y: 60, scale: 0.96 }}
        whileInView={{ opacity: 1, y: 0, scale: 1 }}
        viewport={{ once: true, margin: "0px 0px -20% 0px" }}
        transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
      >
        <MomentVisual moment={moment} index={index} />
      </motion.div>
    </section>
  );
}

export function Landing() {
  const rootRef = useRef<HTMLDivElement>(null);
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, -80]);
  const heroFade = useTransform(scrollYProgress, [0, 0.85], [1, 0]);

  // One loop drives every cursor-reactive layer via CSS vars.
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let mx = 0, my = 0, tmx = 0, tmy = 0, gx = window.innerWidth / 2, gy = window.innerHeight * 0.4, tgx = gx, tgy = gy, raf = 0;
    const onMove = (e: MouseEvent) => {
      tmx = e.clientX / window.innerWidth - 0.5;
      tmy = e.clientY / window.innerHeight - 0.5;
      tgx = e.clientX;
      tgy = e.clientY;
    };
    const tick = () => {
      mx += (tmx - mx) * 0.07;
      my += (tmy - my) * 0.07;
      gx += (tgx - gx) * 0.12;
      gy += (tgy - gy) * 0.12;
      root.style.setProperty("--mx", mx.toFixed(4));
      root.style.setProperty("--my", my.toFixed(4));
      root.style.setProperty("--gx", `${gx.toFixed(1)}px`);
      root.style.setProperty("--gy", `${gy.toFixed(1)}px`);
      raf = requestAnimationFrame(tick);
    };
    window.addEventListener("mousemove", onMove);
    tick();
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  return (
    <div ref={rootRef} className="relative min-h-screen w-full overflow-hidden bg-ink text-white">
      {/* Continuous ambient particle field */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-ink" />
        <Field3D accent={ACCENT} density={190} speed={1.7} />
        <div
          className="absolute inset-0"
          style={{ background: "radial-gradient(ellipse 65% 55% at 50% 40%, transparent 45%, rgba(0,0,0,0.6) 100%)" }}
        />
      </div>
      <CursorGlow />

      <div className="relative z-10">
        {/* Header */}
        <header className="sticky top-0 z-30 border-b border-white/5 bg-ink/30 backdrop-blur-xl">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5 sm:px-10">
            <div className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent font-display text-base font-semibold text-accentInk shadow-glow">
                C
              </span>
              <span className="font-display text-lg font-semibold tracking-tight">CareerOS</span>
            </div>
            <nav className="hidden items-center gap-8 text-sm text-white/60 md:flex">
              <a href="#moments" className="transition hover:text-white">Product</a>
              <a href="#suite" className="transition hover:text-white">Suite</a>
              <a href="#pricing" className="transition hover:text-white">Pricing</a>
            </nav>
            <div className="flex items-center gap-4">
              <Link href="/login" className="text-sm text-white/70 transition hover:text-white">Log in</Link>
              <Link href="/signup" className="rounded-full bg-accent px-5 py-2 text-sm font-medium text-accentInk">
                Get started
              </Link>
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-6xl px-6 sm:px-10">
          {/* Hero */}
          <section ref={heroRef} className="flex min-h-[88vh] flex-col items-center justify-center text-center">
            <motion.div style={{ y: heroY, opacity: heroFade }}>
              <Drift strength={6}>
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                  className="font-mono text-xs uppercase tracking-[0.32em] text-accent"
                >
                  The operating system for your career
                </motion.div>
              </Drift>
              <Drift strength={22}>
                <motion.h1
                  initial={{ opacity: 0, y: 28 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.9, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
                  className="mx-auto mt-7 max-w-4xl font-display font-semibold leading-[0.98] tracking-tight"
                  style={{ fontSize: "clamp(2.9rem, 8vw, 6rem)" }}
                >
                  Run your career like a <span className="italic text-accent">company.</span>
                </motion.h1>
              </Drift>
              <Drift strength={14}>
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.9, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}
                  className="mx-auto mt-7 max-w-xl text-lg leading-relaxed text-white/65"
                >
                  One workspace that knows everything you've done — then finds the work worth your time
                  and writes what it takes to win it.
                </motion.p>
              </Drift>
              <Drift strength={10}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.9, delay: 0.24, ease: [0.22, 1, 0.36, 1] }}
                  className="mt-9 flex flex-wrap items-center justify-center gap-3"
                >
                  <Link href="/signup" className="rounded-full bg-accent px-7 py-3.5 text-sm font-medium text-accentInk transition hover:brightness-105">
                    Start free →
                  </Link>
                  <a href="#moments" className="rounded-full border border-white/20 bg-white/5 px-7 py-3.5 text-sm backdrop-blur-sm transition hover:bg-white/10">
                    See how it works
                  </a>
                </motion.div>
              </Drift>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1, duration: 1 }}
              className="absolute bottom-8"
            >
              <motion.div
                animate={{ y: [0, 8, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="font-mono text-[10px] uppercase tracking-[0.3em] text-white/35"
              >
                Scroll
              </motion.div>
            </motion.div>
          </section>

          {/* Statement */}
          <section className="py-24 text-center sm:py-36">
            <motion.h2
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "0px 0px -25% 0px" }}
              transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
              className="mx-auto max-w-3xl font-display text-3xl font-medium leading-[1.15] tracking-tight text-white/90 sm:text-5xl"
            >
              A whole career team,
              <br />
              <span className="text-white/45">working for one person.</span>
            </motion.h2>
          </section>

          {/* Moments */}
          <div id="moments">
            {MOMENTS.map((m, i) => (
              <Moment key={m.tag} moment={m} index={i} />
            ))}
          </div>

          {/* Suite */}
          <section id="suite" className="py-24 text-center sm:py-32">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "0px 0px -20% 0px" }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="font-mono text-xs uppercase tracking-[0.28em] text-accent">And the rest of the org</div>
              <h2 className="mx-auto mt-5 max-w-2xl font-display text-3xl font-medium tracking-tight sm:text-4xl">
                Every department you'd hire for, already on staff.
              </h2>
              <div className="mx-auto mt-10 flex max-w-3xl flex-wrap justify-center gap-3">
                {SUITE.map((s) => (
                  <span key={s} className="rounded-full border border-white/12 bg-white/[0.04] px-5 py-2.5 text-sm text-white/80 backdrop-blur-sm transition hover:border-accent/40 hover:text-white">
                    {s}
                  </span>
                ))}
              </div>
            </motion.div>
          </section>

          {/* Pricing */}
          <section id="pricing" className="py-24 sm:py-32">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "0px 0px -20% 0px" }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="mb-12 text-center"
            >
              <div className="font-mono text-xs uppercase tracking-[0.28em] text-accent">Pricing</div>
              <h2 className="mx-auto mt-5 max-w-2xl font-display text-3xl font-medium tracking-tight sm:text-4xl">
                Start free. Upgrade when it's already paid for itself.
              </h2>
            </motion.div>
            <div className="grid gap-5 md:grid-cols-3">
              {PLANS.map((plan, i) => (
                <motion.div
                  key={plan.name}
                  initial={{ opacity: 0, y: 40 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "0px 0px -10% 0px" }}
                  transition={{ duration: 0.7, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
                  className={`rounded-2xl border p-7 backdrop-blur-xl ${plan.featured ? "border-accent/50 bg-accent/[0.06]" : "border-white/12 bg-white/[0.03]"}`}
                >
                  {plan.featured && <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-accent">Most popular</div>}
                  <div className="font-display text-lg font-medium">{plan.name}</div>
                  <div className="mb-1 mt-1 font-display text-4xl font-semibold tracking-tight">
                    {plan.price}
                    <span className="text-base font-normal text-white/50">/mo</span>
                  </div>
                  <div className="mb-6 text-xs text-white/50">{plan.note}</div>
                  <ul className="mb-7 space-y-2 text-sm text-white/70">
                    {plan.points.map((p) => (
                      <li key={p} className="flex items-start gap-2">
                        <span className="mt-1 text-accent">·</span>
                        {p}
                      </li>
                    ))}
                  </ul>
                  <Link
                    href="/signup"
                    className={`block rounded-full py-3 text-center text-sm font-medium transition ${plan.featured ? "bg-accent text-accentInk hover:brightness-105" : "border border-white/20 bg-white/5 hover:bg-white/10"}`}
                  >
                    Get started
                  </Link>
                </motion.div>
              ))}
            </div>
          </section>

          {/* Closing */}
          <section className="py-32 text-center sm:py-44">
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "0px 0px -20% 0px" }}
              transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
            >
              <Drift strength={16}>
                <h2 className="mx-auto max-w-3xl font-display font-semibold leading-[1.02] tracking-tight" style={{ fontSize: "clamp(2.5rem, 6vw, 4.5rem)" }}>
                  Your next role is
                  <br />
                  already <span className="italic text-accent">out there.</span>
                </h2>
              </Drift>
              <div className="mt-10">
                <Link href="/signup" className="rounded-full bg-accent px-8 py-4 text-sm font-medium text-accentInk transition hover:brightness-105">
                  Start free →
                </Link>
              </div>
              <p className="mt-6 font-mono text-[11px] uppercase tracking-[0.24em] text-white/35">
                Free forever tier · No card · Bring your own AI key
              </p>
            </motion.div>
          </section>

          <footer className="flex flex-col items-center justify-between gap-3 border-t border-white/8 py-8 text-sm text-white/50 sm:flex-row">
            <div className="flex items-center gap-2.5">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent font-display text-sm font-semibold text-accentInk">C</span>
              <span className="font-display font-semibold text-white/80">CareerOS</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/terms" className="transition hover:text-white">Terms</Link>
              <Link href="/privacy" className="transition hover:text-white">Privacy</Link>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}
