import { requireAccount } from "@/lib/session";
import { api, type CareerIntel } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { SignalForm } from "@/components/careerintel/SignalForm";

export const dynamic = "force-dynamic";

export default async function CareerIntelPage() {
  const { token, account } = await requireAccount();
  let data: CareerIntel = { direction_summary: "", recommendations: {} };
  try {
    data = await api.careerIntel(token);
  } catch {
    // leave empty
  }
  const categories = Object.entries(data.recommendations);

  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Career Intel</h1>
      <p className="mb-6 text-sm text-muted">
        Ranked recommendations synthesized from signals across your activity.
      </p>

      <section className="card mb-4 p-6">
        <h2 className="mb-2 text-sm uppercase tracking-wide text-muted">Direction</h2>
        <p className="text-sm">
          {data.direction_summary || "Add a few signals below to build your direction summary."}
        </p>
      </section>

      <section className="card mb-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Add a signal</h2>
        <SignalForm />
      </section>

      {categories.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {categories.map(([category, ranked]) => (
            <section key={category} className="card p-6">
              <h2 className="mb-3 text-sm uppercase tracking-wide text-muted capitalize">
                {category.replace(/_/g, " ")}
              </h2>
              <div className="space-y-2">
                {ranked.map((item) => (
                  <div
                    key={item.subject}
                    className="flex items-center justify-between rounded-lg border border-line bg-ink/40 px-3 py-2 text-sm"
                  >
                    <span className="font-medium">{item.subject}</span>
                    <span className="text-muted">{Math.round(item.combined_score)}</span>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </Shell>
  );
}
