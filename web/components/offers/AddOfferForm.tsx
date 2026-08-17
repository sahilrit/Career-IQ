"use client";

import { useFormState } from "react-dom";
import { addOffer } from "@/app/offers/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

export function AddOfferForm() {
  const [state, action] = useFormState(addOffer, null);
  return (
    <form action={action} className="card mb-6 grid gap-3 p-5 sm:grid-cols-3">
      <input name="company_name" className="input" placeholder="Company" />
      <input name="job_title" className="input" placeholder="Job title" />
      <input name="base_salary" type="number" className="input" placeholder="Base salary" />
      <input name="bonus" type="number" className="input" placeholder="Bonus" />
      <input name="equity_value" type="number" className="input" placeholder="Equity / yr" />
      <input name="benefits_value" type="number" className="input" placeholder="Benefits" />
      <div className="sm:col-span-3 flex items-center gap-3">
        <SubmitButton>Add offer</SubmitButton>
        {state && !state.ok && <span className="text-sm text-red-400">{state.error}</span>}
      </div>
    </form>
  );
}
