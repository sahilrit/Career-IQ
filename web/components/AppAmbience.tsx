"use client";

import { Field3D } from "@/components/looks/Field3D";
import { CursorGlow, useCursorVars } from "@/components/looks/Interactive";

// The landing's cursor treatment, dialled down for behind-content use: a faint
// particle field + a gold glow that trails the cursor, fixed behind the screen.
// The scrim keeps content legible — heavier for the dense app, lighter for the
// sparse auth pages. Reduced-motion disables the loop and the field's drift.
type Props = {
  /** 0–1 flat scrim over the field. Higher = calmer/darker (app: ~0.8, auth: ~0.5). */
  scrim?: number;
  /** 0–1 edge vignette depth. */
  vignette?: number;
  density?: number;
  speed?: number;
};

export function AppAmbience({ scrim = 0.8, vignette = 0.7, density = 70, speed = 1.1 }: Props = {}) {
  useCursorVars();
  return (
    <div className="pointer-events-none fixed inset-0 z-0" aria-hidden>
      <div className="absolute inset-0 bg-ink" />
      <Field3D accent="#f0b544" density={density} speed={speed} />
      <div className="absolute inset-0" style={{ background: `rgba(11,11,14,${scrim})` }} />
      <div
        className="absolute inset-0"
        style={{ background: `radial-gradient(ellipse 70% 60% at 50% 35%, transparent 30%, rgba(0,0,0,${vignette}) 100%)` }}
      />
      <CursorGlow />
    </div>
  );
}
