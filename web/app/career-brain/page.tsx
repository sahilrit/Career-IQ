import { requireAccount } from "@/lib/session";
import { api, type CareerBrain } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { FadeIn } from "@/components/Motion";

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
      {!brain ? (
        <div className="card p-6 text-muted">No Career Brain yet.</div>
      ) : (
        <FadeIn>
          <div className="card p-6">
            <div className="text-lg font-medium">{brain.identity.full_name}</div>
            <div className="text-muted">{brain.identity.headline}</div>
            {brain.identity.summary && (
              <p className="mt-4 text-white/85">{brain.identity.summary}</p>
            )}
          </div>

          <section className="mt-6">
            <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Skills</h2>
            <div className="flex flex-wrap gap-2">
              {brain.skills.map((skill) => (
                <span
                  key={skill.name}
                  className="rounded-full border border-line bg-panel px-3 py-1 text-sm"
                >
                  {skill.name}
                </span>
              ))}
            </div>
          </section>

          <section className="mt-6">
            <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Experience</h2>
            <div className="space-y-2">
              {brain.experiences.map((experience, index) => (
                <div key={index} className="card p-4">
                  <div className="font-medium">{experience.title}</div>
                  <div className="text-sm text-muted">{experience.company_name}</div>
                </div>
              ))}
            </div>
          </section>
        </FadeIn>
      )}
    </Shell>
  );
}
