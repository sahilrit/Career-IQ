"use client";

import { useState } from "react";

type Package = {
  resume_text: string;
  cover_letter: string;
  ai_used?: boolean;
  ai_error?: string | null;
  resume_document_id?: string | null;
  cover_letter_document_id?: string | null;
  version?: number | null;
};

function DocEditor({
  label,
  documentId,
  initial,
  badge,
}: {
  label: string;
  documentId: string | null | undefined;
  initial: string;
  badge?: React.ReactNode;
}) {
  const [content, setContent] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save() {
    if (!documentId) return;
    setSaving(true);
    setSaved(false);
    try {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (response.ok) setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-muted">
        {label}
        {badge}
      </div>
      <textarea
        className="input min-h-40 text-xs"
        value={content}
        onChange={(e) => {
          setContent(e.target.value);
          setSaved(false);
        }}
      />
      {documentId && (
        <div className="mt-2 flex items-center gap-3">
          <button onClick={save} disabled={saving} className="btn-ghost text-xs">
            {saving ? "Saving…" : "Save edits"}
          </button>
          <a
            href={`/api/documents/${documentId}/pdf`}
            className="text-xs text-accentSoft transition hover:underline"
          >
            Export PDF ↓
          </a>
          {saved && <span className="text-xs text-emerald-400">Saved</span>}
        </div>
      )}
    </div>
  );
}

export function GenerateButton({ jobUrl }: { jobUrl: string | null }) {
  const [busy, setBusy] = useState(false);
  const [pkg, setPkg] = useState<Package | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!jobUrl) return null;

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/opportunities/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_url: jobUrl }),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Generation failed.");
      else setPkg(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3">
      <button onClick={generate} disabled={busy} className="btn-ghost text-sm">
        {busy ? "Generating…" : pkg ? "Regenerate (new version)" : "Generate resume & cover letter"}
      </button>
      {pkg?.version != null && (
        <span className="ml-2 text-xs text-muted">Saved · v{pkg.version}</span>
      )}
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      {pkg && (
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <DocEditor label="Resume" documentId={pkg.resume_document_id} initial={pkg.resume_text} />
          <DocEditor
            label="Cover letter"
            documentId={pkg.cover_letter_document_id}
            initial={pkg.cover_letter}
            badge={
              <span
                className={
                  pkg.ai_used
                    ? "rounded-full bg-accent/20 px-2 py-0.5 text-[10px] font-medium normal-case text-accentSoft"
                    : "rounded-full border border-line px-2 py-0.5 text-[10px] font-medium normal-case text-muted"
                }
              >
                {pkg.ai_used ? "✨ AI-written" : "Template"}
              </span>
            }
          />
          {pkg.ai_error && (
            <p className="text-xs text-amber-400 md:col-span-2">
              AI unavailable, using template — {pkg.ai_error}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
