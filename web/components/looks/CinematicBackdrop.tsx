"use client";

import { useEffect, useRef } from "react";

// A cinematic "still" built entirely in code — a volumetric light column in
// drifting fog with film grain, parallaxed by the cursor. No external asset,
// fully themeable (warm gold vs cool silver).

type Props = { warm: boolean; accent: string };

export function CinematicBackdrop({ warm, accent }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let x = 0;
    let y = 0;
    let tx = 0;
    let ty = 0;
    let raf = 0;
    const onMove = (e: MouseEvent) => {
      tx = e.clientX / window.innerWidth - 0.5;
      ty = e.clientY / window.innerHeight - 0.5;
    };
    const tick = () => {
      x += (tx - x) * 0.06;
      y += (ty - y) * 0.06;
      el.style.setProperty("--px", String(x));
      el.style.setProperty("--py", String(y));
      raf = requestAnimationFrame(tick);
    };
    window.addEventListener("mousemove", onMove);
    tick();
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  const glow = warm ? accent : "#e9e9f0";
  const base = warm ? "#0b0b0e" : "#050505";

  return (
    <div ref={ref} className="absolute inset-0 overflow-hidden" style={{ background: base }} aria-hidden>
      {/* volumetric light column */}
      <div
        className="absolute left-1/2 top-[-10%] h-[130%] w-[42vw] blur-[60px]"
        style={{
          transform: "translateX(calc(-50% + var(--px,0) * 120px)) translateY(calc(var(--py,0) * 40px))",
          background: `radial-gradient(50% 40% at 50% 30%, ${glow}55, transparent 70%), linear-gradient(to bottom, ${glow}22, transparent 65%)`,
          opacity: warm ? 0.7 : 0.85,
        }}
      />
      {/* portal core */}
      <div
        className="absolute left-1/2 top-[16%] h-[62%] w-[3px] blur-[2px]"
        style={{
          transform: "translateX(calc(-50% + var(--px,0) * 140px))",
          background: `linear-gradient(to bottom, transparent, ${warm ? accent : "#ffffff"}, transparent)`,
          opacity: warm ? 0.55 : 0.9,
        }}
      />
      {/* drifting fog */}
      <div
        className="absolute bottom-[-30%] left-[10%] h-[60vh] w-[60vw] rounded-full blur-[120px]"
        style={{ background: `${glow}1f`, transform: "translate(calc(var(--px,0) * -80px), calc(var(--py,0) * -40px))" }}
      />
      <div
        className="absolute right-[5%] top-[10%] h-[45vh] w-[40vw] rounded-full blur-[130px]"
        style={{ background: `${glow}14`, transform: "translate(calc(var(--px,0) * 90px), calc(var(--py,0) * 50px))" }}
      />
      {/* floor reflection */}
      <div
        className="absolute inset-x-0 bottom-0 h-[35%]"
        style={{ background: `linear-gradient(to top, ${glow}12, transparent)` }}
      />
      {/* film grain */}
      <svg className="absolute inset-0 h-full w-full opacity-[0.06] mix-blend-overlay">
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
      {/* vignette */}
      <div
        className="absolute inset-0"
        style={{ background: "radial-gradient(ellipse 70% 60% at 50% 45%, transparent 40%, rgba(0,0,0,0.6) 100%)" }}
      />
    </div>
  );
}
