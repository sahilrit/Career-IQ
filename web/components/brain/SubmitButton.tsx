"use client";

import { useFormStatus } from "react-dom";

export function SubmitButton({
  children,
  full = false,
}: {
  children: React.ReactNode;
  full?: boolean;
}) {
  const { pending } = useFormStatus();
  return (
    <button className={`btn ${full ? "w-full" : ""}`} disabled={pending}>
      {pending ? "…" : children}
    </button>
  );
}
