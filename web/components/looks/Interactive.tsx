"use client";

// Cursor-reactive primitives. A single loop in <Landing> writes smoothed CSS
// vars (--mx/--my in -0.5..0.5, --gx/--gy in px); these are pure consumers, so
// "everything moves with the cursor" is just many layers reading the same vars
// at different strengths — the Apple-style parallax depth trick.

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
