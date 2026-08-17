import { requireAccount } from "@/lib/session";
import { Shell } from "@/components/Shell";
import { InterviewPrepForm } from "@/components/interview/InterviewPrepForm";
import { BookInterviewButton } from "@/components/BookInterviewButton";

export const dynamic = "force-dynamic";

export default async function InterviewPage() {
  const { account } = await requireAccount();
  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Interview Prep</h1>
      <p className="mb-6 text-sm text-muted">
        Tailored questions and a one-page briefing, built from your Career Brain.
      </p>
      <section className="card mb-6 p-6">
        <h2 className="eyebrow mb-1">Scheduling</h2>
        <p className="mb-3 text-sm text-muted">
          Put an interview on your Google Calendar and email the invite to the interviewer.
        </p>
        <BookInterviewButton defaultSummary="Interview" />
      </section>
      <InterviewPrepForm />
    </Shell>
  );
}
