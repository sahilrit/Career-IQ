"use client";

import { useFormState } from "react-dom";
import { addProspect } from "@/app/freelance/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

export function AddProspectForm() {
  const [state, action] = useFormState(addProspect, null);
  return (
    <form action={action} className="card mb-6 grid gap-3 p-5 sm:grid-cols-3">
      <input name="name" className="input" placeholder="Business name" />
      <input name="website" className="input" placeholder="Website (e.g. brand.com)" />
      <input name="industry" className="input" placeholder="Industry (optional)" />
      <div className="sm:col-span-3 flex items-center gap-3">
        <SubmitButton>Add prospect</SubmitButton>
        {state && !state.ok && <span className="text-sm text-red-400">{state.error}</span>}
      </div>
    </form>
  );
}
