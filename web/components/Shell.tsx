import Link from "next/link";
import type { Account } from "@/lib/api";
import { LogoutButton } from "@/components/LogoutButton";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/career-brain", label: "Career Brain" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/autopilot", label: "Autopilot" },
  { href: "/offers", label: "Offers" },
  { href: "/freelance", label: "Freelance" },
  { href: "/network", label: "Network" },
  { href: "/analytics", label: "Analytics" },
  { href: "/billing", label: "Billing" },
  { href: "/settings", label: "Settings" },
];

export function Shell({
  account,
  children,
}: {
  account: Account;
  children: React.ReactNode;
}) {
  const nav = account.is_admin
    ? [...NAV, { href: "/admin", label: "Admin" }]
    : NAV;
  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-4 py-6 md:flex-row md:px-6">
      {/* Mobile top nav (the sidebar is hidden below md). */}
      <div className="md:hidden">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-lg font-semibold tracking-tight">CareerOS</span>
          <LogoutButton />
        </div>
        <nav className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="shrink-0 rounded-xl border border-line px-3 py-1.5 text-sm text-white/80"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>

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
          {account.is_admin && (
            <Link
              href="/admin"
              className="rounded-xl px-3 py-2 text-sm text-accentSoft transition hover:bg-panel"
            >
              Admin
            </Link>
          )}
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
