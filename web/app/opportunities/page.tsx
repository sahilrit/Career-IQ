import { requireAccount } from "@/lib/session";
import { api, type Application } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { Stagger, StaggerItem } from "@/components/Motion";
import { SearchForm } from "@/components/opportunities/SearchForm";
import { GenerateButton } from "@/components/opportunities/GenerateButton";
import { StatusControl } from "@/components/opportunities/StatusControl";

export const dynamic = "force-dynamic";

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
                    </div>
                  </div>
                  <StatusControl application={application} />
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
