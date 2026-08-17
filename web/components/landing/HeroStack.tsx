"use client";

import { useRef } from "react";
import {
  motion,
  useMotionValue,
  useScroll,
  useSpring,
  useTransform,
  type MotionValue,
} from "framer-motion";

// The hero signature: three real product panels floating on one shared
// perspective. The whole rig tilts toward the cursor and the panels drift
// apart in depth as you scroll — the "operating system" made literal as
// layered glass, not a flat screenshot.

const SPRING = { stiffness: 140, damping: 22, mass: 0.6 };

function Panel({
  className,
  style,
  children,
}: {
  className?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`absolute rounded-2xl border border-white/10 bg-panel/80 shadow-card backdrop-blur-xl ${className ?? ""}`}
      style={{ transformStyle: "preserve-3d", ...style }}
    >
      <div
        className="pointer-events-none absolute inset-0 rounded-2xl"
        style={{
          background:
            "linear-gradient(140deg, rgba(255,255,255,0.10), transparent 40%)",
        }}
        aria-hidden
      />
      {children}
    </div>
  );
}

function Bar({ w, tone = "dim" }: { w: string; tone?: "gold" | "bright" | "dim" }) {
  const bg = tone === "gold" ? "bg-accent/70" : tone === "bright" ? "bg-white/25" : "bg-white/10";
  return <div className={`h-2 rounded ${bg}`} style={{ width: w }} />;
}

export function HeroStack() {
  const wrapRef = useRef<HTMLDivElement>(null);

  // Cursor tilt.
  const px = useMotionValue(0);
  const py = useMotionValue(0);
  const rotateY = useSpring(useTransform(px, [-0.5, 0.5], [16, -16]), SPRING);
  const rotateX = useSpring(useTransform(py, [-0.5, 0.5], [-12, 12]), SPRING);

  // Scroll spread — panels separate in depth as the hero scrolls away.
  const { scrollYProgress } = useScroll({
    target: wrapRef,
    offset: ["start start", "end start"],
  });
  const spread = useSpring(scrollYProgress, { stiffness: 80, damping: 30, mass: 0.5 });

  function onMove(e: React.MouseEvent) {
    const r = e.currentTarget.getBoundingClientRect();
    px.set((e.clientX - r.left) / r.width - 0.5);
    py.set((e.clientY - r.top) / r.height - 0.5);
  }
  function onLeave() {
    px.set(0);
    py.set(0);
  }

  // Each panel drifts by a different amount → parallax within the rig.
  const back = useTransform(spread, [0, 1], [0, -70]) as MotionValue<number>;
  const mid = useTransform(spread, [0, 1], [0, 40]) as MotionValue<number>;
  const front = useTransform(spread, [0, 1], [0, 110]) as MotionValue<number>;

  return (
    <div
      ref={wrapRef}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className="relative mx-auto h-[26rem] w-full max-w-lg sm:h-[30rem]"
      style={{ perspective: 1300 }}
    >
      <motion.div
        className="absolute inset-0"
        style={{ transformStyle: "preserve-3d", rotateX, rotateY }}
        initial={{ opacity: 0, y: 60, rotateX: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
      >
        {/* BACK — Pitch Kit revenue */}
        <motion.div style={{ y: back, translateZ: -90, transformStyle: "preserve-3d" }}>
          <Panel className="right-0 top-2 w-64 p-4 sm:w-72">
            <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-accent/80">
              Pitch Kit · revenue found
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                ["Now", "$1.5M", false],
                ["+ / mo", "$150K", false],
                ["+ / yr", "$1.8M", true],
              ].map(([label, value, gold]) => (
                <div key={label as string} className="rounded-lg border border-white/10 bg-ink/60 p-2.5">
                  <div className="text-[9px] text-muted">{label}</div>
                  <div
                    className={`mt-0.5 font-display text-base font-semibold ${gold ? "text-accent" : "text-white"}`}
                  >
                    {value}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 space-y-1.5">
              <Bar w="92%" />
              <Bar w="78%" />
              <Bar w="60%" />
            </div>
          </Panel>
        </motion.div>

        {/* MID — Opportunity discovery */}
        <motion.div style={{ y: mid, translateZ: 10, transformStyle: "preserve-3d" }}>
          <Panel className="left-0 top-28 w-60 p-4 sm:top-32 sm:w-64">
            <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
              Matches for you
            </div>
            {[
              ["Growth Lead · Ramp", "96", true],
              ["Sr. PPC · Linear", "91", false],
              ["Retainer · Acme Shop", "88", false],
            ].map(([role, score, top]) => (
              <div key={role as string} className="mb-2.5 flex items-center gap-2">
                <div className="flex-1">
                  <div className="text-[11px] text-white/85">{role}</div>
                  <div className="mt-1 h-1.5 w-full rounded-full bg-white/10">
                    <div
                      className={`h-1.5 rounded-full ${top ? "bg-accent" : "bg-accent/50"}`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
                <div className="font-mono text-[11px] text-accent">{score as string}</div>
              </div>
            ))}
          </Panel>
        </motion.div>

        {/* FRONT — Career Brain */}
        <motion.div style={{ y: front, translateZ: 120, transformStyle: "preserve-3d" }}>
          <Panel className="bottom-0 right-6 w-60 p-4 sm:w-64">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent font-display text-sm font-bold text-accentInk">
                C
              </span>
              <div>
                <div className="text-[12px] font-medium text-white">Career Brain</div>
                <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-accent/80">
                  verified source
                </div>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {["Meta Ads", "Growth", "SQL", "Lifecycle", "CRO"].map((s) => (
                <span
                  key={s}
                  className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[10px] text-white/75"
                >
                  {s}
                </span>
              ))}
            </div>
            <div className="mt-3 space-y-1.5">
              <Bar w="100%" tone="bright" />
              <Bar w="80%" />
              <Bar w="88%" />
            </div>
          </Panel>
        </motion.div>
      </motion.div>
    </div>
  );
}
