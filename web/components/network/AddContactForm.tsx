"use client";

import { useFormState } from "react-dom";
import { addContact } from "@/app/network/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

const ROLES = ["recruiter", "founder", "cmo", "hiring_manager", "agency_owner", "client", "prospect"];

export function AddContactForm() {
  const [state, action] = useFormState(addContact, null);
  return (
    <form action={action} className="card mb-6 grid gap-3 p-5 sm:grid-cols-4">
      <input name="name" className="input" placeholder="Name" />
      <select name="role" className="input" defaultValue="recruiter">
        {ROLES.map((role) => (
          <option key={role} value={role}>
            {role.replace(/_/g, " ")}
          </option>
        ))}
      </select>
      <input name="organization_name" className="input" placeholder="Organization" />
      <input name="email" type="email" className="input" placeholder="Email (optional)" />
      <div className="sm:col-span-4 flex items-center gap-3">
        <SubmitButton>Add contact</SubmitButton>
        {state && !state.ok && <span className="text-sm text-red-400">{state.error}</span>}
      </div>
    </form>
  );
}
