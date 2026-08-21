import { requireAccount } from "@/lib/session";
import { api, type Application, type FollowUp, type SavedSearch } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { Stagger, StaggerItem } from "@/components/Motion";
import { SearchForm } from "@/components/opportunities/SearchForm";
import { SavedSearches } from "@/components/opportunities/SavedSearches";
import { GenerateButton } from "@/components/opportunities/GenerateButton";
import { StatusControl } from "@/components/opportunities/StatusControl";
import { MatchGap } from "@/components/opportunities/MatchGap";
import { FollowUpControl } from "@/components/opportunities/FollowUpControl";

export const dynamic = "force-dynamic";

export default async function OpportunitiesPage() {
  const { token, account } = await requireAccount();
  let applications: Application[] = [];
  let followUps: FollowUp[] = [];
  let saved: SavedSearch[] = [];
  try {
    [applications, followUps, saved] = await Promise.all([
      api.applications(token),
      api.followUps(token),
      api.savedSearches(token),
    ]);
  } catch {
    /* empty */
  }
  const ranked = [...applications].sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0));
  const dueSoon = followUps.filter((f) => f.days_until <= 3);

  return (
    <Shell account={account}>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Opportunities</h1>
      {dueSoon.length > 0 && (
        <div className="mb-6 rounded-2xl border border-amber-500/30 bg-amber-500/[0.06] p-4">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-amber-400">
            Follow-ups due soon
          </div>
          <ul className="space-y-1 text-sm text-white/85">
            {dueSoon.map((f) => (
              <li key={f.id} className="flex items-center justify-between gap-3">
                <span className="truncate">
                  {f.job_title} · {f.company_name}
                </span>
                <span className="shrink-0 text-xs text-amber-400">
                  {f.due ? "due now" : `in ${f.days_until}d`}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <SearchForm />
      <SavedSearches initial={saved} />
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
                  <MatchGap applicationId={application.id} />
                  <StatusControl application={application} />
                  <FollowUpControl application={application} />
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
