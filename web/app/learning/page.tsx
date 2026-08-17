import { requireAccount } from "@/lib/session";
import { api, type ExperimentRow } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { LearningBoard } from "@/components/learning/LearningBoard";

export const dynamic = "force-dynamic";

export default async function LearningPage() {
  const { token, account } = await requireAccount();
  let experiments: ExperimentRow[] = [];
  try {
    experiments = await api.experiments(token);
  } catch {
    experiments = [];
  }
  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Learning Lab</h1>
      <p className="mb-6 text-sm text-muted">
        A/B test your résumés, emails, and outreach. Log sends and replies; the winner surfaces
        after enough data.
      </p>
      <LearningBoard experiments={experiments} />
    </Shell>
  );
}
