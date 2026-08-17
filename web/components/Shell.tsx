import type { Account } from "@/lib/api";
import { LogoutButton } from "@/components/LogoutButton";
import { NavLinks } from "@/components/NavLinks";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/career-brain", label: "Career Brain" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/interview", label: "Interview Prep" },
  { href: "/autopilot", label: "Autopilot" },
  { href: "/offers", label: "Offers" },
  { href: "/freelance", label: "Freelance" },
  { href: "/pitch-kit", label: "Pitch Kit" },
  { href: "/clients", label: "Clients" },
  { href: "/network", label: "Network" },
  { href: "/personal-brand", label: "Personal Brand" },
  { href: "/learning", label: "Learning Lab" },
  { href: "/finance", label: "Finance" },
  { href: "/career-intel", label: "Career Intel" },
  { href: "/ceo", label: "CEO Agent" },
  { href: "/analytics", label: "Analytics" },
  { href: "/billing", label: "Billing" },
  { href: "/settings", label: "Settings" },
];

function BrandMark() {
  return (
    <span className="flex items-center gap-2">
      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent font-mono text-xs font-bold text-white shadow-glow">
        C
      </span>
      <span className="font-display text-lg font-semibold tracking-tight">CareerOS</span>
    </span>
  );
}

export function Shell({
  account,
  children,
}: {
  account: Account;
  children: React.ReactNode;
}) {
  const items = account.is_admin ? [...NAV, { href: "/admin", label: "Admin" }] : NAV;
  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-4 py-6 md:flex-row md:px-6">
      {/* Mobile top nav (the sidebar is hidden below md). */}
      <div className="md:hidden">
        <div className="mb-3 flex items-center justify-between">
          <BrandMark />
          <LogoutButton />
        </div>
        <nav className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
          <NavLinks items={items} variant="top" />
        </nav>
      </div>

      <aside className="hidden w-56 shrink-0 flex-col md:flex">
        <div className="mb-8 px-2">
          <BrandMark />
        </div>
        <nav className="flex flex-col gap-0.5">
          <NavLinks items={items} variant="side" />
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
