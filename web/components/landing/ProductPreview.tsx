// A stylised mock of the app UI — communicates the product at a glance.
// Presentational only (no data); wrapped in <Float> by the page for the
// gentle 3D drift.
export function ProductPreview() {
  return (
    <div className="rounded-2xl border border-line bg-panel/80 shadow-card backdrop-blur">
      {/* window chrome */}
      <div className="flex items-center gap-1.5 border-b border-lineSoft px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
        <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
        <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
        <span className="ml-3 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
          careeros / pitch kit
        </span>
      </div>

      <div className="grid grid-cols-[86px_1fr] gap-0">
        {/* mini sidebar */}
        <div className="hidden flex-col gap-2 border-r border-lineSoft p-4 sm:flex">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent font-display text-xs font-bold text-accentInk">
            C
          </span>
          <div className="mt-2 h-2 w-12 rounded bg-accent/50" />
          <div className="h-2 w-14 rounded bg-white/10" />
          <div className="h-2 w-10 rounded bg-white/10" />
          <div className="h-2 w-14 rounded bg-white/10" />
          <div className="h-2 w-11 rounded bg-white/10" />
        </div>

        {/* content */}
        <div className="p-5">
          <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.2em] text-accent/80">
            Revenue opportunity
          </div>
          <div className="grid grid-cols-3 gap-2">
            {[
              ["Current", "$1.5M"],
              ["Extra / mo", "$150K"],
              ["Extra / yr", "$1.8M"],
            ].map(([label, value], i) => (
              <div key={label} className="rounded-lg border border-line bg-ink/50 p-3">
                <div className="text-[10px] text-muted">{label}</div>
                <div
                  className={`mt-0.5 font-display text-lg font-semibold ${
                    i === 2 ? "text-accent" : "text-white"
                  }`}
                >
                  {value}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center gap-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
              Written proposal
            </div>
            <span className="rounded-full bg-accent/20 px-2 py-0.5 text-[9px] text-accentSoft">
              ✨ AI-written
            </span>
          </div>
          <div className="mt-2 space-y-1.5 rounded-lg border border-line bg-ink/40 p-3">
            <div className="h-2 w-11/12 rounded bg-white/10" />
            <div className="h-2 w-10/12 rounded bg-white/10" />
            <div className="h-2 w-9/12 rounded bg-white/10" />
            <div className="h-2 w-11/12 rounded bg-white/[0.07]" />
            <div className="h-2 w-7/12 rounded bg-white/[0.07]" />
          </div>

          <div className="mt-4 flex gap-2">
            <div className="h-7 w-28 rounded-full bg-accent" />
            <div className="h-7 w-24 rounded-full border border-line" />
          </div>
        </div>
      </div>
    </div>
  );
}
