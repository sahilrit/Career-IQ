"use client";

import { useFormState } from "react-dom";
import { useTransition } from "react";
import type { CareerBrain } from "@/lib/api";
import {
  addExperience,
  addSkill,
  deleteExperience,
  deleteSkill,
  updateSummary,
} from "@/app/career-brain/actions";
import { FadeIn } from "@/components/Motion";
import { SubmitButton } from "@/components/brain/SubmitButton";

function RemoveButton({ onRemove, label }: { onRemove: () => Promise<unknown>; label: string }) {
  const [pending, startTransition] = useTransition();
  return (
    <button
      type="button"
      aria-label={label}
      disabled={pending}
      onClick={() => startTransition(() => void onRemove())}
      className="text-muted transition hover:text-red-400 disabled:opacity-40"
    >
      ×
    </button>
  );
}

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
              key={skill.id}
              className="flex items-center gap-1.5 rounded-full border border-line bg-ink/60 px-3 py-1 text-sm"
            >
              {skill.name}
              <RemoveButton
                label={`Remove ${skill.name}`}
                onRemove={() => deleteSkill(skill.id)}
              />
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
          {brain.experiences.map((experience) => (
            <div
              key={experience.id}
              className="flex items-start justify-between gap-3 rounded-xl border border-line bg-ink/40 p-3"
            >
              <div>
                <div className="font-medium">{experience.title}</div>
                <div className="text-sm text-muted">
                  {experience.company_name}
                  {experience.start_date && (
                    <span className="ml-2 text-xs">
                      {experience.start_date.slice(0, 7)} –{" "}
                      {experience.end_date ? experience.end_date.slice(0, 7) : "Present"}
                    </span>
                  )}
                </div>
              </div>
              <RemoveButton
                label={`Remove ${experience.title}`}
                onRemove={() => deleteExperience(experience.id)}
              />
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
