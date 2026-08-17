import { requireAccount } from "@/lib/session";
import { Shell } from "@/components/Shell";
import { PitchKitStudio } from "@/components/audit/PitchKitStudio";

export const dynamic = "force-dynamic";

export default async function PitchKitPage() {
  const { account } = await requireAccount();
  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Pitch Kit</h1>
      <p className="mb-6 text-sm text-muted">
        Turn a target business into a complete freelance pitch — audit findings, a revenue
        projection, a cold email, a LinkedIn message, a Loom script, and a written proposal (PDF).
        Add your Anthropic key in Settings for an AI-written proposal.
      </p>
      <PitchKitStudio />
    </Shell>
  );
}
