import { requireAccount } from "@/lib/session";
import { api, type FinanceOverview } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { IncomeForm } from "@/components/finance/IncomeForm";

export const dynamic = "force-dynamic";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export default async function FinancePage() {
  const { token, account } = await requireAccount();
  let data: FinanceOverview = { records: [], total: 0, monthly: [], trend: null };
  try {
    data = await api.finance(token);
  } catch {
    // leave empty
  }

  return (
    <Shell account={account}>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Finance</h1>

      <div className="mb-4 grid gap-4 sm:grid-cols-3">
        <div className="card p-6">
          <div className="text-xs uppercase tracking-wide text-muted">Total income</div>
          <div className="mt-1 text-2xl font-semibold">${data.total.toLocaleString()}</div>
        </div>
        <div className="card p-6">
          <div className="text-xs uppercase tracking-wide text-muted">Records</div>
          <div className="mt-1 text-2xl font-semibold">{data.records.length}</div>
        </div>
        <div className="card p-6">
          <div className="text-xs uppercase tracking-wide text-muted">Trend</div>
          <div className="mt-1 text-2xl font-semibold capitalize">{data.trend ?? "—"}</div>
        </div>
      </div>

      <section className="card mb-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Add income</h2>
        <IncomeForm />
      </section>

      <section className="card p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Recent income</h2>
        {data.records.length === 0 ? (
          <p className="text-sm text-muted">No income logged yet.</p>
        ) : (
          <div className="space-y-2">
            {data.records.map((record) => (
              <div
                key={record.id}
                className="flex items-center justify-between rounded-lg border border-line bg-ink/40 px-3 py-2 text-sm"
              >
                <div>
                  <span className="font-medium">{record.source_name}</span>
                  <span className="ml-2 text-muted capitalize">{record.source.replace("_", " ")}</span>
                </div>
                <div className="text-right">
                  <div className="font-medium">${record.amount.toLocaleString()}</div>
                  <div className="text-xs text-muted">{record.received_date}</div>
                </div>
              </div>
            ))}
          </div>
        )}
        {data.monthly.length > 0 && (
          <div className="mt-4 border-t border-line pt-4">
            <div className="mb-2 text-xs uppercase tracking-wide text-muted">Monthly</div>
            <div className="flex flex-wrap gap-2">
              {data.monthly.map((month) => (
                <span
                  key={`${month.year}-${month.month}`}
                  className="rounded-full border border-line px-3 py-1 text-sm"
                >
                  {MONTHS[month.month - 1]} {month.year}: ${month.total.toLocaleString()}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>
    </Shell>
  );
}
