import { requireAccount } from "@/lib/session";
import { api, type PreparedApplication } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { ReviewQueue } from "@/components/review/ReviewQueue";

export const dynamic = "force-dynamic";

export default async function ReviewPage() {
  const { token, account } = await requireAccount();
  let prepared: PreparedApplication[] = [];
  try {
    prepared = await api.reviewPrepared(token);
  } catch {
    /* empty — show the empty state */
  }

  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Review queue</h1>
      <p className="mb-6 max-w-2xl text-muted">
        Applications CareerOS tailored and filled for you, but couldn&apos;t submit — these forms
        need a captcha or a step only you can do. Open each one, check the details and the AI cover
        letter, apply, then mark it done.
      </p>
      <ReviewQueue initial={prepared} />
    </Shell>
  );
}
