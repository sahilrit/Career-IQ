import { requireAccount } from "@/lib/session";
import { api, type Application } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { Stagger, StaggerItem } from "@/components/Motion";

export const dynamic = "force-dynamic";

function rate(numerator: number, denominator: number): string {
  if (denominator === 0) return "—";
  return `${Math.round((numerator / denominator) * 100)}%`;
}

export default async function AnalyticsPage() {
  const { token, account } = await requireAccount();
  let applications: Application[] = [];
  try {
    applications = await api.applications(token);
  } catch {
    /* empty */
  }

  const count = (statuses: string[]) =>
    applications.filter((a) => statuses.includes(a.status)).length;

  const applied = count(["applied", "in_review", "interviewing", "offer", "accepted", "rejected"]);
  const interviews = count(["interviewing", "offer", "accepted"]);
  const offers = count(["offer", "accepted"]);

  const funnel = [
    { label: "Discovered", value: applications.length },
    { label: "Applied", value: applied },
    { label: "Interviews", value: interviews },
    { label: "Offers", value: offers },
  ];
  const rates = [
    { label: "Interview rate", value: rate(interviews, applied) },
    { label: "Offer rate", value: rate(offers, applied) },
  ];

  return (
    <Shell account={account}>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Analytics</h1>
      <Stagger>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {funnel.map((item) => (
            <StaggerItem key={item.label}>
              <div className="card p-5">
                <div className="text-3xl font-semibold">{item.value}</div>
                <div className="mt-1 text-sm text-muted">{item.label}</div>
              </div>
            </StaggerItem>
          ))}
        </div>
      </Stagger>
      <div className="mt-4 grid grid-cols-2 gap-4 md:max-w-md">
        {rates.map((item) => (
          <div key={item.label} className="card p-5">
            <div className="text-2xl font-semibold">{item.value}</div>
            <div className="mt-1 text-sm text-muted">{item.label}</div>
          </div>
        ))}
      </div>
      <p className="mt-6 text-sm text-muted">
        Full funnel and Career ROI (with freelance income) live on the Analytics
        page in the app; this reads live from the API.
      </p>
    </Shell>
  );
}
