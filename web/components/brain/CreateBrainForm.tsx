"use client";

import { useFormState } from "react-dom";
import { createBrain } from "@/app/career-brain/actions";
import { FadeIn } from "@/components/Motion";
import { SubmitButton } from "@/components/brain/SubmitButton";

export function CreateBrainForm({ defaultEmail }: { defaultEmail: string }) {
  const [state, action] = useFormState(createBrain, null);
  return (
    <FadeIn>
      <form action={action} className="card max-w-md space-y-4 p-6">
        <h2 className="text-lg font-medium">Create your Career Brain</h2>
        <div>
          <label className="label">Full name</label>
          <input name="full_name" className="input" required />
        </div>
        <div>
          <label className="label">Email</label>
          <input name="email" type="email" className="input" defaultValue={defaultEmail} required />
        </div>
        {state && !state.ok && <p className="text-sm text-red-400">{state.error}</p>}
        <SubmitButton full>Create</SubmitButton>
      </form>
    </FadeIn>
  );
}
