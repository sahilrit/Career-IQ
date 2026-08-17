"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Field3D } from "@/components/looks/Field3D";
import { CinematicBackdrop } from "@/components/looks/CinematicBackdrop";
import { FullBleedStack } from "@/components/looks/FullBleedStack";

type Brand = "gold" | "silver";
type Motion = "field" | "cinematic" | "stack";

const THEME: Record<Brand, { accent: string; accentInk: string; pill: string; pillText: string; label: string }> = {
  gold: { accent: "#f0b544", accentInk: "#221704", pill: "#f0b544", pillText: "#221704", label: "Gold · editorial" },
  silver: { accent: "#e9e9f0", accentInk: "#0a0a0a", pill: "#ffffff", pillText: "#050505", label: "Silver · minimal" },
};

const MOTIONS: { key: Motion; label: string }[] = [
  { key: "field", label: "3D particle field" },
  { key: "cinematic", label: "Cinematic backdrop" },
  { key: "stack", label: "Glass stack" },
];

export default function Looks() {
  const [brand, setBrand] = useState<Brand>("gold");
  const [motionKey, setMotionKey] = useState<Motion>("field");
  const t = THEME[brand];
  const warm = brand === "gold";
  const isStack = motionKey === "stack";

  return (
    <div
      className="relative h-screen w-full overflow-hidden text-white"
      style={{ background: warm ? "#0b0b0e" : "#050505" }}
    >
      {/* Background engine */}
      {motionKey === "field" && (
        <>
          <div className="absolute inset-0" style={{ background: warm ? "#0b0b0e" : "#050505" }} />
          <Field3D accent={t.accent} />
          <div
            className="absolute inset-0"
            style={{ background: "radial-gradient(ellipse 60% 50% at 50% 50%, transparent 40%, rgba(0,0,0,0.55) 100%)" }}
          />
        </>
      )}
      {motionKey === "cinematic" && <CinematicBackdrop warm={warm} accent={t.accent} />}

      {/* Foreground composition */}
      <div className="relative z-10 mx-auto flex h-full max-w-6xl flex-col px-6 sm:px-10">
        {/* Nav */}
        <header className="flex items-center justify-between py-6">
          <div className="flex items-center gap-2.5">
            <span
              className="flex h-7 w-7 items-center justify-center rounded-lg font-display text-base font-semibold"
              style={{ background: t.accent, color: t.accentInk }}
            >
              C
            </span>
            <span className="font-display text-lg font-semibold tracking-tight">CareerOS</span>
          </div>
          <nav className="hidden items-center gap-8 text-sm text-white/70 md:flex">
            <span>Workspace</span>
            <span>Suite</span>
            <span>Pricing</span>
          </nav>
          <Link
            href="/signup"
            className="rounded-full px-5 py-2 text-sm font-medium"
            style={{ background: t.pill, color: t.pillText }}
          >
            Get started
          </Link>
        </header>

        {/* Hero */}
        <div className={`flex flex-1 ${isStack ? "grid items-center gap-8 lg:grid-cols-2" : "items-center"}`}>
          <motion.div
            key={`${brand}-${motionKey}`}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className={isStack ? "" : "max-w-2xl"}
          >
            <div
              className="mb-6 font-mono text-xs uppercase tracking-[0.28em]"
              style={{ color: warm ? t.accent : "#c9c9d2" }}
            >
              The operating system for your career
            </div>
            <h1
              className="font-display font-semibold tracking-tight"
              style={{ fontSize: "clamp(2.75rem, 6vw, 5rem)", lineHeight: 1.0 }}
            >
              Run your career
              <br />
              like a{" "}
              <span className="italic" style={{ color: warm ? t.accent : "#fff" }}>
                company.
              </span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/70">
              One workspace that learns your track record, finds the work worth your time, and writes
              every application and pitch to win it. You review. It runs.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href="/signup"
                className="rounded-full px-6 py-3 text-sm font-medium"
                style={{ background: t.pill, color: t.pillText }}
              >
                Start free →
              </Link>
              <Link
                href="/login"
                className="rounded-full border border-white/25 bg-white/5 px-6 py-3 text-sm backdrop-blur-sm transition hover:bg-white/10"
              >
                See how it works
              </Link>
            </div>
          </motion.div>

          {isStack && (
            <div className="hidden lg:block">
              <FullBleedStack accent={t.accent} accentInk={t.accentInk} />
            </div>
          )}
        </div>
      </div>

      {/* Variant switcher */}
      <div className="absolute inset-x-0 bottom-5 z-20 flex justify-center px-4">
        <div className="flex flex-col items-center gap-2 rounded-2xl border border-white/12 bg-black/60 px-3 py-2.5 backdrop-blur-xl sm:flex-row sm:gap-3">
          <span className="px-1 font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">Preview</span>
          <div className="flex gap-1">
            {(Object.keys(THEME) as Brand[]).map((b) => (
              <button
                key={b}
                onClick={() => setBrand(b)}
                className={`rounded-lg px-3 py-1.5 text-xs transition ${brand === b ? "bg-white/15 text-white" : "text-white/55 hover:text-white"}`}
              >
                {THEME[b].label}
              </button>
            ))}
          </div>
          <span className="hidden h-4 w-px bg-white/15 sm:block" />
          <div className="flex gap-1">
            {MOTIONS.map((m) => (
              <button
                key={m.key}
                onClick={() => setMotionKey(m.key)}
                className={`rounded-lg px-3 py-1.5 text-xs transition ${motionKey === m.key ? "bg-white/15 text-white" : "text-white/55 hover:text-white"}`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
