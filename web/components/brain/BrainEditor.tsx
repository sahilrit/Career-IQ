"use client";

import { useFormState } from "react-dom";
import type { CareerBrain } from "@/lib/api";
import { addExperience, addSkill, updateSummary } from "@/app/career-brain/actions";
import { FadeIn } from "@/components/Motion";
import { SubmitButton } from "@/components/brain/SubmitButton";

function FormError({ state }: { state: { ok: boolean; error?: string } | null }) {
  if (!state || state.ok) return null;
  return <p className="text-sm text-red-400">{state.error}</p>;
}

export function BrainEditor({ brain }: { brain: CareerBrain }) {
  const [summaryState, summaryAction] = useFormState(updateSummary, null);
  const [skillState, skillAction] = useFormState(addSkill, null);
  const [expState, expAction] = useFormState(addExperience, null);

  return (
    <FadeIn>
      <div className="card p-6">
        <div className="text-lg font-medium">{brain.identity.full_name}</div>
        <div className="text-muted">{brain.identity.headline || brain.identity.email}</div>
      </div>

      <section className="card mt-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Professional summary</h2>
        <form action={summaryAction} className="space-y-3">
          <textarea
            name="summary"
            className="input min-h-28"
            defaultValue={brain.identity.summary}
            placeholder="A few sentences on who you are and your impact…"
          />
          <FormError state={summaryState} />
          <SubmitButton>Save summary</SubmitButton>
        </form>
      </section>

      <section className="card mt-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Skills</h2>
        <div className="mb-4 flex flex-wrap gap-2">
          {brain.skills.map((skill) => (
            <span
              key={skill.name}
              className="rounded-full border border-line bg-ink/60 px-3 py-1 text-sm"
            >
              {skill.name}
            </span>
          ))}
          {brain.skills.length === 0 && <span className="text-sm text-muted">No skills yet.</span>}
        </div>
        <form action={skillAction} className="flex gap-2">
          <input name="name" className="input" placeholder="e.g. Meta Ads" />
          <SubmitButton>Add</SubmitButton>
        </form>
        <FormError state={skillState} />
      </section>

      <section className="card mt-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Experience</h2>
        <div className="mb-4 space-y-2">
          {brain.experiences.map((experience, index) => (
            <div key={index} className="rounded-xl border border-line bg-ink/40 p-3">
              <div className="font-medium">{experience.title}</div>
              <div className="text-sm text-muted">{experience.company_name}</div>
            </div>
          ))}
          {brain.experiences.length === 0 && (
            <span className="text-sm text-muted">No experience added yet.</span>
          )}
        </div>
        <form action={expAction} className="grid gap-2 sm:grid-cols-3">
          <input name="title" className="input" placeholder="Title" />
          <input name="company_name" className="input" placeholder="Company" />
          <input name="start_date" type="date" className="input" />
          <div className="sm:col-span-3">
            <SubmitButton>Add experience</SubmitButton>
          </div>
        </form>
        <FormError state={expState} />
      </section>
    </FadeIn>
  );
}
