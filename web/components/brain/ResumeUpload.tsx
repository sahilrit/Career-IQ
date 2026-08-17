"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FadeIn } from "@/components/Motion";

type Imported = { fields: string[]; skills_added: number };

export function ResumeUpload() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Imported | null>(null);

  async function upload(file: File) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch("/api/brain/import-resume", { method: "POST", body });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(payload.error ?? "Couldn't import that résumé.");
        return;
      }
      setResult(payload.imported as Imported);
      // Pull the freshly-filled fields into the page below.
      router.refresh();
    } catch {
      setError("Upload failed — check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  function summarize(imported: Imported): string {
    const bits: string[] = [];
    if (imported.fields.length) bits.push(imported.fields.join(", "));
    if (imported.skills_added) bits.push(`${imported.skills_added} skill${imported.skills_added === 1 ? "" : "s"}`);
    return bits.length
      ? `Imported ${bits.join(" and ")}. Review below and edit anything.`
      : "Nothing new to import — your details already look complete.";
  }

  return (
    <FadeIn>
      <section className="card mb-4 p-6">
        <h2 className="mb-1 text-sm uppercase tracking-wide text-muted">Import from résumé</h2>
        <p className="mb-4 text-sm text-muted">
          Upload your résumé (PDF) and we&apos;ll auto-fill your summary, skills, and contact
          details. You can edit everything afterwards.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                setFileName(file.name);
                void upload(file);
              }
            }}
          />
          <button
            type="button"
            className="btn"
            disabled={busy}
            onClick={() => inputRef.current?.click()}
          >
            {busy ? "Reading résumé…" : "Upload résumé (PDF)"}
          </button>
          {fileName && !busy && <span className="text-sm text-muted">{fileName}</span>}
        </div>
        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        {result && <p className="mt-3 text-sm text-emerald-400">{summarize(result)}</p>}
      </section>
    </FadeIn>
  );
}
