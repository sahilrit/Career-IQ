import { requireAccount } from "@/lib/session";
import { api, type RankedOffer } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { AddOfferForm } from "@/components/offers/AddOfferForm";

export const dynamic = "force-dynamic";

export default async function OffersPage() {
  const { token, account } = await requireAccount();
  let offers: RankedOffer[] = [];
  try {
    offers = await api.offers(token);
  } catch {
    /* empty */
  }

  return (
    <Shell account={account}>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Offers</h1>
      <AddOfferForm />
      {offers.length === 0 ? (
        <div className="card p-6 text-muted">
          No offers yet — add one above to compare them by Opportunity Value.
        </div>
      ) : (
        <div className="space-y-3">
          {offers.map((offer, index) => (
            <div key={index} className="card flex items-center justify-between gap-4 p-4">
              <div>
                <div className="font-medium">
                  <span className="mr-2 text-muted">#{index + 1}</span>
                  {offer.company_name} — {offer.job_title}
                </div>
                <div className="text-sm text-muted">Base ${offer.base_salary.toLocaleString()}</div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold">
                  ${Math.round(offer.opportunity_value).toLocaleString()}
                </div>
                <div className="text-xs text-muted">Opportunity Value</div>
              </div>
            </div>
          ))}
        </div>
      )}
      <p className="mt-4 text-sm text-muted">
        Opportunity Value is an after-tax, quality-adjusted estimate — a way to compare offers,
        not a guarantee.
      </p>
    </Shell>
  );
}
