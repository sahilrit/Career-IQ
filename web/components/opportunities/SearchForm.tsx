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
        <div className="mt-3">
          <p className="text-sm text-emerald-400">
            Discovered {state.discovered} posting(s), {state.qualified} qualified.
          </p>
          {/* A search that quietly returned less because a source broke looks
              identical to a quiet week. Say which ones didn't answer. */}
          {state.source_errors.length > 0 && (
            <div className="mt-2 rounded-lg border border-amber-500/30 bg-amber-500/[0.06] px-3 py-2">
              <p className="text-sm text-amber-300">
                {state.source_errors.length} source(s) didn&apos;t respond, so these results are
                incomplete.
              </p>
              <ul className="mt-1 space-y-0.5 text-xs text-amber-200/70">
                {state.source_errors.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      {state && !state.ok && <p className="mt-3 text-sm text-red-400">{state.error}</p>}
    </div>
  );
}
