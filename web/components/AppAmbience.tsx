"use client";

import { Field3D } from "@/components/looks/Field3D";
import { CursorGlow, useCursorVars } from "@/components/looks/Interactive";

// The landing's cursor treatment, dialled down for the app: a faint particle
// field + a gold glow that trails the cursor, fixed behind every screen. A
// heavy scrim keeps content fully legible — this is atmosphere, not decoration
// competing with the UI. Reduced-motion disables the loop and the field's drift.
export function AppAmbience() {
  useCursorVars();
  return (
    <div className="pointer-events-none fixed inset-0 z-0" aria-hidden>
      <div className="absolute inset-0 bg-ink" />
      <Field3D accent="#f0b544" density={70} speed={1.1} />
      {/* legibility scrim */}
      <div className="absolute inset-0 bg-ink/80" />
      <div
        className="absolute inset-0"
        style={{ background: "radial-gradient(ellipse 70% 60% at 50% 30%, transparent 30%, rgba(0,0,0,0.7) 100%)" }}
      />
      <CursorGlow />
    </div>
  );
}
