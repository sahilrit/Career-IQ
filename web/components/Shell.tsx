import type { Account } from "@/lib/api";
import { LogoutButton } from "@/components/LogoutButton";
import { NavLinks } from "@/components/NavLinks";

type Item = { href: string; label: string };

const HOME: Item = { href: "/dashboard", label: "Dashboard" };

const GROUPS: { label: string; items: Item[] }[] = [
  {
    label: "Career",
    items: [
      { href: "/career-brain", label: "Career Brain" },
      { href: "/opportunities", label: "Opportunities" },
      { href: "/interview", label: "Interview Prep" },
      { href: "/autopilot", label: "Autopilot" },
      { href: "/offers", label: "Offers" },
    ],
  },
  {
    label: "Freelance",
    items: [
      { href: "/freelance", label: "Freelance" },
      { href: "/pitch-kit", label: "Pitch Kit" },
      { href: "/clients", label: "Clients" },
    ],
  },
  {
    label: "Growth",
    items: [
      { href: "/network", label: "Network" },
      { href: "/personal-brand", label: "Personal Brand" },
      { href: "/learning", label: "Learning Lab" },
      { href: "/finance", label: "Finance" },
      { href: "/career-intel", label: "Career Intel" },
      { href: "/ceo", label: "CEO Agent" },
      { href: "/analytics", label: "Analytics" },
    ],
  },
];

const ACCOUNT: Item[] = [
  { href: "/billing", label: "Billing" },
  { href: "/settings", label: "Settings" },
];

// Flat list for the mobile top-nav (grouping doesn't fit a horizontal scroller).
const FLAT: Item[] = [HOME, ...GROUPS.flatMap((g) => g.items), ...ACCOUNT];

function BrandMark() {
  return (
    <span className="flex items-center gap-2.5">
      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent font-display text-base font-semibold text-accentInk shadow-glow">
        C
      </span>
      <span className="font-display text-xl font-semibold tracking-tightest text-white">
        CareerOS
      </span>
    </span>
  );
}

export function Shell({ account, children }: { account: Account; children: React.ReactNode }) {
  const accountItems = account.is_admin ? [...ACCOUNT, { href: "/admin", label: "Admin" }] : ACCOUNT;
  const flat = account.is_admin ? [...FLAT, { href: "/admin", label: "Admin" }] : FLAT;

  return (
    <div className="mx-auto flex min-h-screen max-w-[76rem] flex-col gap-6 px-4 py-6 md:flex-row md:px-6">
      {/* Mobile top nav */}
      <div className="md:hidden">
        <div className="mb-3 flex items-center justify-between">
          <BrandMark />
          <LogoutButton />
        </div>
        <nav className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
          <NavLinks items={flat} variant="top" />
        </nav>
      </div>

      <aside className="hidden w-60 shrink-0 flex-col md:flex">
        <div className="mb-8 px-2">
          <BrandMark />
        </div>
        <nav className="flex flex-col gap-6">
          <div className="flex flex-col gap-0.5">
            <NavLinks items={[HOME]} variant="side" />
          </div>
          {GROUPS.map((group) => (
            <div key={group.label} className="flex flex-col gap-0.5">
              <div className="eyebrow mb-1.5 px-3">{group.label}</div>
              <NavLinks items={group.items} variant="side" />
            </div>
          ))}
          <div className="flex flex-col gap-0.5">
            <div className="eyebrow mb-1.5 px-3">Account</div>
            <NavLinks items={accountItems} variant="side" />
          </div>
        </nav>
        <div className="mt-auto border-t border-lineSoft px-2 pt-5 text-sm text-muted">
          <div className="mb-2 truncate text-white/80">{account.full_name}</div>
          <LogoutButton />
        </div>
      </aside>

      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
