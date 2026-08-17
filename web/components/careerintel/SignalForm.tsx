"use client";

import { useFormState } from "react-dom";
import { addSignal } from "@/app/career-intel/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

const CATEGORIES = [
  "role", "company", "industry", "client", "country",
  "salary_range", "skill", "platform", "outreach_strategy", "resume_variant",
];

export function SignalForm() {
  const [state, action] = useFormState(addSignal, null);
  return (
    <form action={action} className="grid gap-2 sm:grid-cols-4">
      <select name="category" className="input sm:col-span-1">
        {CATEGORIES.map((category) => (
          <option key={category} value={category}>
            {category.replace(/_/g, " ")}
          </option>
        ))}
      </select>
      <input name="subject" className="input sm:col-span-2" placeholder="Subject (e.g. Growth Lead)" />
      <input name="score" type="number" step="0.1" defaultValue="1" className="input" placeholder="Score" />
      <div className="sm:col-span-4">
        <SubmitButton>Add signal</SubmitButton>
      </div>
      {state && !state.ok && <p className="text-sm text-red-400 sm:col-span-4">{state.error}</p>}
    </form>
  );
}
