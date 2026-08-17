import Link from "next/link";

export function Wordmark({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2.5">
      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent font-display text-base font-semibold text-accentInk shadow-glow">
        C
      </span>
      <span className="font-display text-xl font-semibold tracking-tightest text-white">
        CareerOS
      </span>
    </Link>
  );
}
