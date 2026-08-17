import { requireAccount } from "@/lib/session";
import { api, type Billing } from "@/lib/api";
import { Shell } from "@/components/Shell";

export const dynamic = "force-dynamic";

export default async function BillingPage() {
  const { token, account } = await requireAccount();
  let billing: Billing | null = null;
  try {
    billing = await api.billing(token);
  } catch {
    billing = null;
  }

  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Billing</h1>
      {billing && (
        <p className="mb-6 text-muted">
          Current plan: <span className="text-white">{billing.current_tier}</span> ·{" "}
          {billing.status}
        </p>
      )}
      {!billing ? (
        <div className="card p-6 text-muted">Billing is unavailable right now.</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {billing.plans.map((plan) => (
            <div
              key={plan.tier}
              className={`card p-6 ${plan.is_current ? "ring-1 ring-accent" : ""}`}
            >
              <div className="text-lg font-medium">{plan.name}</div>
              <div className="mb-3 text-2xl font-semibold">
                ${plan.monthly_price_usd.toLocaleString()}
                <span className="text-sm font-normal text-muted">/mo</span>
              </div>
              <ul className="mb-4 space-y-1 text-sm text-muted">
                {plan.features.map((feature) => (
                  <li key={feature}>{feature.replace(/_/g, " ")}</li>
                ))}
              </ul>
              {plan.is_current ? (
                <span className="text-sm text-emerald-400">Your plan</span>
              ) : plan.checkout_url ? (
                <a href={plan.checkout_url} className="btn w-full" target="_blank" rel="noreferrer">
                  Upgrade to {plan.name}
                </a>
              ) : plan.monthly_price_usd > 0 ? (
                <span className="text-sm text-muted">Contact us to upgrade</span>
              ) : null}
            </div>
          ))}
        </div>
      )}
      <p className="mt-6 text-sm text-muted">
        Payments are handled by Stripe. After paying, your plan activates automatically.
      </p>
    </Shell>
  );
}
