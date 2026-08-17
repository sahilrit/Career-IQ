"use client";

import { useFormState } from "react-dom";
import type { ExperimentRow } from "@/lib/api";
import { addVariant, createExperiment, recordOutcome } from "@/app/learning/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

const TYPES = ["resume", "email", "linkedin", "portfolio", "proposal", "subject_line"];

function CreateExperiment() {
  const [state, action] = useFormState(createExperiment, null);
  return (
    <form action={action} className="grid gap-2 sm:grid-cols-3">
      <select name="experiment_type" className="input">
        {TYPES.map((type) => (
          <option key={type} value={type}>
            {type.replace(/_/g, " ")}
          </option>
        ))}
      </select>
      <input name="name" className="input" placeholder="Experiment name" />
      <SubmitButton>New experiment</SubmitButton>
      {state && !state.ok && <p className="text-sm text-red-400 sm:col-span-3">{state.error}</p>}
    </form>
  );
}

function AddVariant({ experimentId }: { experimentId: string }) {
  const [state, action] = useFormState(addVariant, null);
  return (
    <form action={action} className="mt-3 flex gap-2">
      <input type="hidden" name="experiment_id" value={experimentId} />
      <input name="label" className="input" placeholder="New variant label" />
      <SubmitButton>Add</SubmitButton>
      {state && !state.ok && <p className="text-sm text-red-400">{state.error}</p>}
    </form>
  );
}

function OutcomeButton({
  variantId,
  outcome,
  label,
}: {
  variantId: string;
  outcome: string;
  label: string;
}) {
  return (
    <form action={recordOutcome}>
      <input type="hidden" name="variant_id" value={variantId} />
      <input type="hidden" name="outcome_type" value={outcome} />
      <button className="btn-ghost text-xs">{label}</button>
    </form>
  );
}

export function LearningBoard({ experiments }: { experiments: ExperimentRow[] }) {
  return (
    <div>
      <section className="card mb-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">New experiment</h2>
        <CreateExperiment />
      </section>

      {experiments.length === 0 ? (
        <div className="card p-6 text-sm text-muted">
          No experiments yet — create one above to start A/B testing your outreach.
        </div>
      ) : (
        <div className="space-y-4">
          {experiments.map((experiment) => (
            <section key={experiment.id} className="card p-6">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-medium">{experiment.name}</h2>
                <span className="text-xs uppercase tracking-wide text-muted">
                  {experiment.type.replace(/_/g, " ")}
                </span>
              </div>
              <div className="space-y-2">
                {experiment.variants.map((variant) => (
                  <div
                    key={variant.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-ink/40 px-3 py-2 text-sm"
                  >
                    <div>
                      <span className="font-medium">{variant.label}</span>
                      {experiment.winner === variant.id && (
                        <span className="ml-2 rounded-full bg-accent/20 px-2 py-0.5 text-[10px] text-accentSoft">
                          winner
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-muted">
                      <span>{variant.sent} sent</span>
                      <span>{variant.responses} replies</span>
                      <span>
                        {variant.response_rate === null
                          ? "—"
                          : `${Math.round(variant.response_rate * 100)}%`}
                      </span>
                      <OutcomeButton variantId={variant.id} outcome="sent" label="+ Sent" />
                      <OutcomeButton variantId={variant.id} outcome="response" label="+ Reply" />
                    </div>
                  </div>
                ))}
                {experiment.variants.length === 0 && (
                  <p className="text-sm text-muted">No variants yet.</p>
                )}
              </div>
              <AddVariant experimentId={experiment.id} />
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
