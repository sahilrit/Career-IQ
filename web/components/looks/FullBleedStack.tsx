"use client";

import { useRef } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";

// Full-bleed, cursor-reactive 3D glass stack — themeable accent so it works in
// both the gold and silver directions. Three panels on a shared perspective.

const SPRING = { stiffness: 140, damping: 20, mass: 0.7 };

type Props = { accent: string; accentInk: string };

export function FullBleedStack({ accent, accentInk }: Props) {
  const px = useMotionValue(0);
  const py = useMotionValue(0);
  const rotateY = useSpring(useTransform(px, [-0.5, 0.5], [18, -18]), SPRING);
  const rotateX = useSpring(useTransform(py, [-0.5, 0.5], [-14, 14]), SPRING);
  const wrap = useRef<HTMLDivElement>(null);

  const onMove = (e: React.MouseEvent) => {
    const r = e.currentTarget.getBoundingClientRect();
    px.set((e.clientX - r.left) / r.width - 0.5);
    py.set((e.clientY - r.top) / r.height - 0.5);
  };
  const onLeave = () => {
    px.set(0);
    py.set(0);
  };

  const panel =
    "absolute rounded-2xl border border-white/12 bg-white/[0.04] shadow-2xl backdrop-blur-xl";

  return (
    <div
      ref={wrap}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className="relative mx-auto h-[32rem] w-full max-w-2xl"
      style={{ perspective: 1400 }}
    >
      <motion.div
        className="absolute inset-0"
        style={{ transformStyle: "preserve-3d", rotateX, rotateY }}
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* back */}
        <div className={`${panel} right-4 top-4 w-72 p-5`} style={{ transform: "translateZ(-70px)" }}>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em]" style={{ color: accent }}>
            Revenue found
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {["$1.5M", "$150K", "$1.8M"].map((v, i) => (
              <div key={v} className="rounded-lg border border-white/10 bg-black/40 p-2.5">
                <div className="text-[9px] text-white/50">{["now", "+/mo", "+/yr"][i]}</div>
                <div className="mt-0.5 font-display text-base font-semibold" style={{ color: i === 2 ? accent : "#fff" }}>
                  {v}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* mid */}
        <div className={`${panel} left-2 top-40 w-64 p-5`} style={{ transform: "translateZ(20px)" }}>
          <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.22em] text-white/55">
            Matches for you
          </div>
          {[["Growth Lead · Ramp", 96], ["Sr. PPC · Linear", 91], ["Retainer · Acme", 88]].map(([r, s]) => (
            <div key={r as string} className="mb-2.5">
              <div className="text-[11px] text-white/85">{r}</div>
              <div className="mt-1 h-1.5 w-full rounded-full bg-white/10">
                <div className="h-1.5 rounded-full" style={{ width: `${s}%`, background: accent }} />
              </div>
            </div>
          ))}
        </div>

        {/* front */}
        <div className={`${panel} bottom-2 right-10 w-64 p-5`} style={{ transform: "translateZ(110px)" }}>
          <div className="flex items-center gap-2.5">
            <span
              className="flex h-8 w-8 items-center justify-center rounded-lg font-display text-sm font-bold"
              style={{ background: accent, color: accentInk }}
            >
              C
            </span>
            <div>
              <div className="text-[12px] font-medium text-white">Career Brain</div>
              <div className="font-mono text-[9px] uppercase tracking-[0.18em]" style={{ color: accent }}>
                verified source
              </div>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {["Meta Ads", "Growth", "SQL", "Lifecycle", "CRO"].map((t) => (
              <span key={t} className="rounded-full border border-white/10 bg-white/[0.05] px-2 py-0.5 text-[10px] text-white/75">
                {t}
              </span>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
