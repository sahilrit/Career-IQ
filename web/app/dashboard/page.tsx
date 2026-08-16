import { requireAccount } from "@/lib/session";
import { api, type Application, type CareerBrain } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { Stagger, StaggerItem } from "@/components/Motion";

export const dynamic = "force-dynamic";

function statusOf(applications: Application[], statuses: string[]) {
  return applications.filter((a) => statuses.includes(a.status)).length;
}

export default async function DashboardPage() {
  const { token, account } = await requireAccount();

  let applications: Application[] = [];
  let brain: CareerBrain | null = null;
  try {
    applications = await api.applications(token);
  } catch {
    /* empty */
  }
  try {
    brain = await api.brain(token);
  } catch {
    brain = null;
  }

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

      <Stagger>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          {tiles.map((tile) => (
            <StaggerItem key={tile.label}>
              <div className="card p-5">
                <div className="text-3xl font-semibold">{tile.value}</div>
                <div className="mt-1 text-sm text-muted">{tile.label}</div>
              </div>
            </StaggerItem>
          ))}
        </div>
      </Stagger>

      {!brain && (
        <div className="card mt-6 p-6 text-muted">
          No Career Brain yet — head to the Career Brain page (in the Streamlit
          app) or import your resume to get started.
        </div>
      )}
    </Shell>
  );
}
