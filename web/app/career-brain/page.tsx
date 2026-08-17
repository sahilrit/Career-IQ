import { requireAccount } from "@/lib/session";
import { api, type CareerBrain } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { CreateBrainForm } from "@/components/brain/CreateBrainForm";
import { BrainEditor } from "@/components/brain/BrainEditor";
import { ResumeUpload } from "@/components/brain/ResumeUpload";

export const dynamic = "force-dynamic";

export default async function CareerBrainPage() {
  const { token, account } = await requireAccount();
  let brain: CareerBrain | null = null;
  try {
    brain = await api.brain(token);
  } catch {
    brain = null;
  }

  return (
    <Shell account={account}>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Career Brain</h1>
      <ResumeUpload />
      {brain ? (
        <BrainEditor brain={brain} />
      ) : (
        <CreateBrainForm defaultEmail={account.email} />
      )}
    </Shell>
  );
}
