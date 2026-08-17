import Link from "next/link";
import type { Account } from "@/lib/api";
import { LogoutButton } from "@/components/LogoutButton";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/career-brain", label: "Career Brain" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/offers", label: "Offers" },
  { href: "/freelance", label: "Freelance" },
  { href: "/network", label: "Network" },
  { href: "/analytics", label: "Analytics" },
];

export function Shell({
  account,
  children,
}: {
  account: Account;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto flex min-h-screen max-w-6xl gap-6 px-4 py-6 md:px-6">
      <aside className="hidden w-56 shrink-0 flex-col md:flex">
        <div className="mb-8 flex items-center gap-2 px-2">
          <span className="text-lg font-semibold tracking-tight">CareerOS</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-xl px-3 py-2 text-sm text-white/80 transition hover:bg-panel hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="mt-auto px-2 pt-8 text-sm text-muted">
          <div className="mb-2 truncate">{account.full_name}</div>
          <LogoutButton />
        </div>
      </aside>
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
