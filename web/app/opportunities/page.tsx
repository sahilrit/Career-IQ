import { requireAccount } from "@/lib/session";
import { api, type Application } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { Stagger, StaggerItem } from "@/components/Motion";
import { SearchForm } from "@/components/opportunities/SearchForm";
import { GenerateButton } from "@/components/opportunities/GenerateButton";

export const dynamic = "force-dynamic";

const TONE: Record<string, string> = {
  qualified: "text-emerald-400 border-emerald-500/40",
  applied: "text-sky-400 border-sky-500/40",
  in_review: "text-sky-400 border-sky-500/40",
  interviewing: "text-amber-400 border-amber-500/40",
  offer: "text-emerald-400 border-emerald-500/40",
  accepted: "text-emerald-400 border-emerald-500/40",
  rejected: "text-red-400 border-red-500/40",
};

export default async function OpportunitiesPage() {
  const { token, account } = await requireAccount();
  let applications: Application[] = [];
  try {
    applications = await api.applications(token);
  } catch {
    /* empty */
  }
  const ranked = [...applications].sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0));

  return (
    <Shell account={account}>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Opportunities</h1>
      <SearchForm />
      {ranked.length === 0 ? (
        <div className="card p-6 text-muted">
          No applications yet — run a search above to discover jobs.
        </div>
      ) : (
        <Stagger>
          <div className="space-y-3">
            {ranked.map((application) => (
              <StaggerItem key={application.id}>
                <div className="card p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="truncate font-medium">{application.job_title}</div>
                      <div className="truncate text-sm text-muted">
                        {application.company_name}
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      {application.match_score != null && (
                        <span className="text-sm text-muted">
                          {Math.round(application.match_score * 100)}%
                        </span>
                      )}
                      <span
                        className={`rounded-full border px-2.5 py-0.5 text-xs ${
                          TONE[application.status] ?? "text-muted border-line"
                        }`}
                      >
                        {application.status.replace(/_/g, " ")}
                      </span>
                    </div>
                  </div>
                  <GenerateButton jobUrl={application.job_url} />
                </div>
              </StaggerItem>
            ))}
          </div>
        </Stagger>
      )}
    </Shell>
  );
}
