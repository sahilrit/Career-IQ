"use client";

import { useFormState } from "react-dom";
import { runSearch } from "@/app/opportunities/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

export function SearchForm() {
  const [state, action] = useFormState(runSearch, null);
  return (
    <div className="card mb-6 p-5">
      <form action={action} className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label className="label">Search keywords (comma-separated)</label>
          <input
            name="keywords"
            className="input"
            placeholder="performance marketing, ppc, media buyer"
          />
        </div>
        <label className="flex items-center gap-2 pb-2.5 text-sm text-muted">
          <input type="checkbox" name="remote_only" defaultChecked className="accent-accent" />
          Remote only
        </label>
        <SubmitButton>Search</SubmitButton>
      </form>
      {state && state.ok && (
        <p className="mt-3 text-sm text-emerald-400">
          Discovered {state.discovered} posting(s), {state.qualified} qualified.
        </p>
      )}
      {state && !state.ok && <p className="mt-3 text-sm text-red-400">{state.error}</p>}
    </div>
  );
}
