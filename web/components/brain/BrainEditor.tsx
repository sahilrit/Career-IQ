"use client";

import { useFormState } from "react-dom";
import { useTransition } from "react";
import type { CareerBrain } from "@/lib/api";
import {
  addAward,
  addCertification,
  addEducation,
  addExperience,
  addLanguage,
  addProject,
  addSkill,
  deleteAward,
  deleteCertification,
  deleteEducation,
  deleteExperience,
  deleteLanguage,
  deleteProject,
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
  const [eduState, eduAction] = useFormState(addEducation, null);
  const [certState, certAction] = useFormState(addCertification, null);
  const [projState, projAction] = useFormState(addProject, null);
  const [langState, langAction] = useFormState(addLanguage, null);
  const [awardState, awardAction] = useFormState(addAward, null);

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

      <section className="card mt-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Education</h2>
        <div className="mb-4 space-y-2">
          {(brain.education ?? []).map((edu) => (
            <div
              key={edu.id}
              className="flex items-start justify-between gap-3 rounded-xl border border-line bg-ink/40 p-3"
            >
              <div>
                <div className="font-medium">{edu.credential}</div>
                <div className="text-sm text-muted">
                  {edu.institution}
                  {edu.field_of_study ? ` · ${edu.field_of_study}` : ""}
                  {edu.end_date ? ` · ${edu.end_date.slice(0, 4)}` : ""}
                </div>
              </div>
              <RemoveButton
                label={`Remove ${edu.credential}`}
                onRemove={() => deleteEducation(edu.id)}
              />
            </div>
          ))}
          {(brain.education ?? []).length === 0 && (
            <span className="text-sm text-muted">No education added yet.</span>
          )}
        </div>
        <form action={eduAction} className="grid gap-2 sm:grid-cols-2">
          <input name="credential" className="input" placeholder="Degree / credential" />
          <input name="institution" className="input" placeholder="Institution" />
          <input name="field_of_study" className="input" placeholder="Field of study (optional)" />
          <input name="end_date" type="date" className="input" />
          <div className="sm:col-span-2">
            <SubmitButton>Add education</SubmitButton>
          </div>
        </form>
        <FormError state={eduState} />
      </section>

      <section className="card mt-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Certifications</h2>
        <div className="mb-4 space-y-2">
          {(brain.certifications ?? []).map((cert) => (
            <div
              key={cert.id}
              className="flex items-center justify-between gap-3 rounded-xl border border-line bg-ink/40 p-3"
            >
              <div>
                <span className="font-medium">{cert.name}</span>
                {cert.issuer && <span className="ml-2 text-sm text-muted">{cert.issuer}</span>}
              </div>
              <RemoveButton
                label={`Remove ${cert.name}`}
                onRemove={() => deleteCertification(cert.id)}
              />
            </div>
          ))}
          {(brain.certifications ?? []).length === 0 && (
            <span className="text-sm text-muted">No certifications added yet.</span>
          )}
        </div>
        <form action={certAction} className="grid gap-2 sm:grid-cols-2">
          <input name="name" className="input" placeholder="Certification (e.g. Google Ads)" />
          <input name="issuer" className="input" placeholder="Issuer (optional)" />
          <div className="sm:col-span-2">
            <SubmitButton>Add certification</SubmitButton>
          </div>
        </form>
        <FormError state={certState} />
      </section>

      <section className="card mt-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Projects</h2>
        <div className="mb-4 space-y-2">
          {(brain.projects ?? []).map((proj) => (
            <div
              key={proj.id}
              className="flex items-start justify-between gap-3 rounded-xl border border-line bg-ink/40 p-3"
            >
              <div>
                <div className="font-medium">
                  {proj.url ? (
                    <a href={proj.url} target="_blank" rel="noreferrer" className="hover:underline">
                      {proj.name}
                    </a>
                  ) : (
                    proj.name
                  )}
                </div>
                {proj.description && <div className="text-sm text-muted">{proj.description}</div>}
              </div>
              <RemoveButton label={`Remove ${proj.name}`} onRemove={() => deleteProject(proj.id)} />
            </div>
          ))}
          {(brain.projects ?? []).length === 0 && (
            <span className="text-sm text-muted">No projects added yet.</span>
          )}
        </div>
        <form action={projAction} className="grid gap-2 sm:grid-cols-2">
          <input name="name" className="input" placeholder="Project name" />
          <input name="url" className="input" placeholder="Link (optional)" />
          <input name="description" className="input sm:col-span-2" placeholder="Short description (optional)" />
          <div className="sm:col-span-2">
            <SubmitButton>Add project</SubmitButton>
          </div>
        </form>
        <FormError state={projState} />
      </section>

      <section className="card mt-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Languages</h2>
        <div className="mb-4 flex flex-wrap gap-2">
          {(brain.languages ?? []).map((lang) => (
            <span
              key={lang.id}
              className="flex items-center gap-1.5 rounded-full border border-line bg-ink/60 px-3 py-1 text-sm"
            >
              {lang.name}
              <span className="text-xs text-muted">· {lang.proficiency}</span>
              <RemoveButton label={`Remove ${lang.name}`} onRemove={() => deleteLanguage(lang.id)} />
            </span>
          ))}
          {(brain.languages ?? []).length === 0 && (
            <span className="text-sm text-muted">No languages added yet.</span>
          )}
        </div>
        <form action={langAction} className="flex flex-wrap gap-2">
          <input name="name" className="input flex-1" placeholder="e.g. English" />
          <select name="proficiency" className="input w-auto" defaultValue="fluent">
            {["native", "fluent", "professional", "conversational", "basic"].map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <SubmitButton>Add</SubmitButton>
        </form>
        <FormError state={langState} />
      </section>

      <section className="card mt-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Awards</h2>
        <div className="mb-4 space-y-2">
          {(brain.awards ?? []).map((award) => (
            <div
              key={award.id}
              className="flex items-center justify-between gap-3 rounded-xl border border-line bg-ink/40 p-3"
            >
              <div>
                <span className="font-medium">{award.title}</span>
                {award.issuer && <span className="ml-2 text-sm text-muted">{award.issuer}</span>}
              </div>
              <RemoveButton label={`Remove ${award.title}`} onRemove={() => deleteAward(award.id)} />
            </div>
          ))}
          {(brain.awards ?? []).length === 0 && (
            <span className="text-sm text-muted">No awards added yet.</span>
          )}
        </div>
        <form action={awardAction} className="grid gap-2 sm:grid-cols-2">
          <input name="title" className="input" placeholder="Award / honor" />
          <input name="issuer" className="input" placeholder="Issuer (optional)" />
          <div className="sm:col-span-2">
            <SubmitButton>Add award</SubmitButton>
          </div>
        </form>
        <FormError state={awardState} />
      </section>
    </FadeIn>
  );
}
