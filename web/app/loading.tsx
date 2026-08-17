export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex animate-pulse items-center gap-2.5 opacity-80">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent font-display text-base font-semibold text-accentInk">
          C
        </span>
        <span className="font-display text-xl font-semibold tracking-tightest">CareerOS</span>
      </div>
    </div>
  );
}
