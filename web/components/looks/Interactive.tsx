"use client";

import { useEffect } from "react";

// Cursor-reactive primitives. useCursorVars() runs one smoothed loop that
// writes CSS vars onto <html> (--mx/--my in -0.5..0.5, --gx/--gy in px); the
// rest are pure consumers, so "everything moves with the cursor" is just many
// layers reading the same vars at different strengths — the parallax depth
// trick. Vars live on documentElement so any subtree (landing or app) inherits.
export function useCursorVars() {
  useEffect(() => {
    const el = document.documentElement;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let mx = 0;
    let my = 0;
    let tmx = 0;
    let tmy = 0;
    let gx = window.innerWidth / 2;
    let gy = window.innerHeight * 0.4;
    let tgx = gx;
    let tgy = gy;
    let raf = 0;
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
      el.style.setProperty("--mx", mx.toFixed(4));
      el.style.setProperty("--my", my.toFixed(4));
      el.style.setProperty("--gx", `${gx.toFixed(1)}px`);
      el.style.setProperty("--gy", `${gy.toFixed(1)}px`);
      raf = requestAnimationFrame(tick);
    };
    window.addEventListener("mousemove", onMove);
    tick();
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
      el.style.removeProperty("--mx");
      el.style.removeProperty("--my");
    };
  }, []);
}

export function CursorGlow() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-[2] hidden md:block"
      style={{
        background:
          "radial-gradient(480px circle at var(--gx, 50%) var(--gy, 40%), rgba(240,181,68,0.10), transparent 62%)",
      }}
    />
  );
}

export function Drift({
  strength = 20,
  className,
  children,
}: {
  strength?: number;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={className}
      style={{
        transform: `translate3d(calc(var(--mx,0) * ${strength}px), calc(var(--my,0) * ${strength}px), 0)`,
        willChange: "transform",
      }}
    >
      {children}
    </div>
  );
}
