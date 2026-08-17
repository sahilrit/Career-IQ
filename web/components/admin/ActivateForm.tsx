"use client";

import { useFormState } from "react-dom";
import type { Customer } from "@/lib/api";
import { activatePlan } from "@/app/admin/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

export function ActivateForm({ customers }: { customers: Customer[] }) {
  const [state, action] = useFormState(activatePlan, null);
  return (
    <form action={action} className="card grid gap-3 p-5 sm:grid-cols-3">
      <select name="workspace_id" className="input">
        {customers.map((customer) => (
          <option key={customer.workspace_id} value={customer.workspace_id}>
            {customer.email} — {customer.plan}
          </option>
        ))}
      </select>
      <select name="tier" className="input" defaultValue="pro">
        <option value="free">free</option>
        <option value="pro">pro</option>
        <option value="agency">agency</option>
      </select>
      <div className="flex items-center gap-3">
        <SubmitButton>Set plan</SubmitButton>
        {state && !state.ok && <span className="text-sm text-red-400">{state.error}</span>}
      </div>
    </form>
  );
}
