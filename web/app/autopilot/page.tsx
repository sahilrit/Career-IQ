import { requireAccount } from "@/lib/session";
import { api, type AutopilotRun } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { Stagger, StaggerItem } from "@/components/Motion";

export const dynamic = "force-dynamic";

export default async function AutopilotPage() {
  const { token, account } = await requireAccount();
  let runs: AutopilotRun[] = [];
  try {
    runs = await api.autopilotRuns(token);
  } catch {
    /* empty */
  }

  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Autopilot</h1>
      <p className="mb-6 text-muted">
        Autonomous applying runs from the daemon and record every submission and hold here.
        Start it with{" "}
        <code className="rounded bg-panel px-1.5 py-0.5 text-white/80">
          uv run python scripts/autopilot_daemon.py --workspace-id {account.workspace_id}
        </code>
        . It never bypasses logins or captchas — those are held for you.
      </p>
      {runs.length === 0 ? (
        <div className="card p-6 text-muted">No autopilot runs yet.</div>
      ) : (
        <Stagger>
          <div className="space-y-4">
            {runs.map((run) => (
              <StaggerItem key={run.id}>
                <div className="card p-5">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="text-sm text-muted">{run.ran_at.slice(0, 16).replace("T", " ")}</div>
                    <div className="text-sm">
                      <span className="text-emerald-400">{run.submitted} submitted</span>
                      <span className="text-muted"> / {run.qualified_total} qualified</span>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    {run.outcomes.map((outcome, index) => (
                      <div key={index} className="flex items-start gap-2 text-sm">
                        <span
                          className={`mt-0.5 shrink-0 rounded-full border px-2 py-0.5 text-xs ${
                            outcome.submitted
                              ? "border-emerald-500/40 text-emerald-400"
                              : "border-amber-500/40 text-amber-400"
                          }`}
                        >
                          {outcome.submitted ? "submitted" : "held"}
                        </span>
                        <span className="text-white/85">
                          {outcome.job_title} @ {outcome.company_name}
                          {!outcome.submitted && (
                            <span className="text-muted"> — {outcome.reason}</span>
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </StaggerItem>
            ))}
          </div>
        </Stagger>
      )}
    </Shell>
  );
}
