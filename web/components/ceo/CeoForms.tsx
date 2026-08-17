"use client";

import { useFormState } from "react-dom";
import { computeAllocation, recordPerformance } from "@/app/ceo/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

const CATEGORIES = ["employment", "freelance", "networking", "personal_brand"];

export function PerformanceForm() {
  const [state, action] = useFormState(recordPerformance, null);
  return (
    <form action={action} className="grid gap-2 sm:grid-cols-3">
      <select name="category" className="input">
        {CATEGORIES.map((category) => (
          <option key={category} value={category}>
            {category.replace(/_/g, " ")}
          </option>
        ))}
      </select>
      <input name="metric_name" className="input" placeholder="Metric (e.g. offers)" />
      <input name="value" type="number" step="0.01" className="input" placeholder="Value" />
      <div className="sm:col-span-3">
        <SubmitButton>Log result</SubmitButton>
      </div>
      {state && !state.ok && <p className="text-sm text-red-400 sm:col-span-3">{state.error}</p>}
    </form>
  );
}

export function ComputeButton() {
  const [state, action] = useFormState(async () => computeAllocation(), null);
  return (
    <form action={action}>
      <SubmitButton>Recompute allocation</SubmitButton>
      {state && !state.ok && <p className="mt-2 text-sm text-red-400">{state.error}</p>}
    </form>
  );
}
