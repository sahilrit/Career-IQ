import Link from "next/link";
import { requireAccount } from "@/lib/session";
import {
  api,
  type Application,
  type CareerBrain,
  type FollowUp,
  type Onboarding,
} from "@/lib/api";
import { Shell } from "@/components/Shell";
import { Stagger, StaggerItem } from "@/components/Motion";
import { OnboardingChecklist } from "@/components/OnboardingChecklist";

export const dynamic = "force-dynamic";

function statusOf(applications: Application[], statuses: string[]) {
  return applications.filter((a) => statuses.includes(a.status)).length;
}

const COLUMNS: [string, string][] = [
  ["qualified", "Qualified"],
  ["applied", "Applied"],
  ["in_review", "In review"],
  ["interviewing", "Interviewing"],
  ["offer", "Offer"],
];

export default async function DashboardPage() {
  const { token, account } = await requireAccount();

  let applications: Application[] = [];
  let followUps: FollowUp[] = [];
  let brain: CareerBrain | null = null;
  let onboarding: Onboarding | null = null;
  try {
    [applications, followUps] = await Promise.all([api.applications(token), api.followUps(token)]);
  } catch {
    /* empty */
  }
  try {
    brain = await api.brain(token);
  } catch {
    brain = null;
  }
  try {
    onboarding = await api.onboarding(token);
  } catch {
    onboarding = null;
  }

  const dueSoon = followUps.filter((f) => f.days_until <= 3);
  const tiles = [
    { label: "Applications", value: applications.length },
    { label: "Qualified", value: statusOf(applications, ["qualified"]) },
    { label: "Applied", value: statusOf(applications, ["applied", "in_review"]) },
    { label: "Interviewing", value: statusOf(applications, ["interviewing"]) },
    { label: "Offers", value: statusOf(applications, ["offer", "accepted"]) },
  ];

  return (
    <Shell account={account}>
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">
          {brain ? `Hi, ${brain.identity.full_name.split(" ")[0]}` : "Welcome to CareerOS"}
        </h1>
        <p className="text-muted">
          {brain?.identity.headline || "Build your Career Brain to get started."}
        </p>
      </header>

      {onboarding && <OnboardingChecklist data={onboarding} />}

      {dueSoon.length > 0 && (
        <Link
          href="/opportunities"
          className="mb-6 block rounded-2xl border border-amber-500/30 bg-amber-500/[0.06] p-4 transition hover:border-amber-500/50"
        >
          <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.2em] text-amber-400">
            {dueSoon.length} follow-up{dueSoon.length > 1 ? "s" : ""} due soon
          </div>
          <div className="truncate text-sm text-white/85">
            {dueSoon.map((f) => `${f.job_title} · ${f.company_name}`).join("  ·  ")}
          </div>
        </Link>
      )}

      <Stagger>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          {tiles.map((tile) => (
            <StaggerItem key={tile.label}>
              <Link href="/opportunities" className="card block p-5 transition hover:border-accent/40">
                <div className="text-3xl font-semibold">{tile.value}</div>
                <div className="mt-1 text-sm text-muted">{tile.label}</div>
              </Link>
            </StaggerItem>
          ))}
        </div>
      </Stagger>

      {applications.length > 0 && (
        <section className="mt-8">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-lg font-medium">Pipeline</h2>
            <Link href="/opportunities" className="text-sm text-muted transition hover:text-white">
              Manage →
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-5">
            {COLUMNS.map(([status, label]) => {
              const items = applications.filter((a) => a.status === status);
              return (
                <div key={status} className="rounded-xl border border-lineSoft bg-panel/50 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-medium text-white/80">{label}</span>
                    <span className="font-mono text-xs text-muted">{items.length}</span>
                  </div>
                  <div className="space-y-2">
                    {items.length === 0 ? (
                      <div className="text-xs text-muted/60">—</div>
                    ) : (
                      items.slice(0, 6).map((a) => (
                        <div key={a.id} className="rounded-lg border border-line bg-ink/50 p-2">
                          <div className="truncate text-xs font-medium text-white/90">
                            {a.job_title}
                          </div>
                          <div className="truncate text-[11px] text-muted">{a.company_name}</div>
                        </div>
                      ))
                    )}
                    {items.length > 6 && (
                      <div className="text-[11px] text-muted">+{items.length - 6} more</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </Shell>
  );
}
