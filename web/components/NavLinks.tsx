"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Item = { href: string; label: string };

export function NavLinks({ items, variant }: { items: Item[]; variant: "side" | "top" }) {
  const pathname = usePathname();
  return (
    <>
      {items.map((item) => {
        const active = pathname === item.href;
        if (variant === "top") {
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`shrink-0 rounded-lg border px-3 py-1.5 text-sm transition ${
                active
                  ? "border-accentSoft bg-accent/10 text-white"
                  : "border-line text-white/75 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          );
        }
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`relative rounded-lg px-3 py-2 text-sm transition ${
              active
                ? "bg-accent/10 font-medium text-white"
                : "text-white/70 hover:bg-white/[0.03] hover:text-white"
            }`}
          >
            {active && (
              <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-accentSoft" />
            )}
            {item.label}
          </Link>
        );
      })}
    </>
  );
}
