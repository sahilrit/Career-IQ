import { requireAccount } from "@/lib/session";
import { api, type CeoOverview } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { ComputeButton, PerformanceForm } from "@/components/ceo/CeoForms";

export const dynamic = "force-dynamic";

export default async function CeoPage() {
  const { token, account } = await requireAccount();
  let data: CeoOverview = { latest: null, history: [] };
  try {
    data = await api.ceo(token);
  } catch {
    // leave empty
  }
  const latest = data.latest;

  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">CEO Agent</h1>
      <p className="mb-6 text-sm text-muted">
        Log results across your work streams and get a suggested effort split. Guidance only.
      </p>

      <section className="card mb-4 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm uppercase tracking-wide text-muted">Suggested allocation</h2>
          <ComputeButton />
        </div>
        {latest ? (
          <>
            <div className="grid gap-3 sm:grid-cols-4">
              {Object.entries(latest.allocations).map(([category, pct]) => (
                <div key={category} className="rounded-xl border border-line bg-ink/40 p-4">
                  <div className="text-xs uppercase tracking-wide text-muted capitalize">
                    {category.replace(/_/g, " ")}
                  </div>
                  <div className="mt-1 text-xl font-semibold">{Math.round(pct)}%</div>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-muted">{latest.disclaimer}</p>
          </>
        ) : (
          <p className="text-sm text-muted">
            Log a few results, then recompute to get your first allocation.
          </p>
        )}
      </section>

      <section className="card p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Log a result</h2>
        <PerformanceForm />
      </section>
    </Shell>
  );
}
