"use client";

import { useFormState } from "react-dom";
import { addIncome } from "@/app/finance/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

export function IncomeForm() {
  const [state, action] = useFormState(addIncome, null);
  return (
    <form action={action} className="grid gap-2 sm:grid-cols-2">
      <select name="source" className="input">
        <option value="salary">Salary</option>
        <option value="freelance">Freelance</option>
        <option value="client_revenue">Client revenue</option>
        <option value="other">Other</option>
      </select>
      <input name="source_name" className="input" placeholder="Source (e.g. Acme Corp)" />
      <input name="amount" type="number" step="0.01" className="input" placeholder="Amount" />
      <input name="received_date" type="date" className="input" />
      <div className="sm:col-span-2">
        <SubmitButton>Add income</SubmitButton>
      </div>
      {state && !state.ok && <p className="text-sm text-red-400 sm:col-span-2">{state.error}</p>}
    </form>
  );
}
