"use client";

import { useState } from "react";
import type { BrandContent, BrandProject } from "@/lib/api";
import { FadeIn } from "@/components/Motion";

function Block({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <div className="mb-1 text-xs uppercase tracking-wide text-muted">{title}</div>
      <textarea readOnly className="input min-h-40 text-xs" value={body} />
    </div>
  );
}

export function BrandStudio({ projects }: { projects: BrandProject[] }) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [content, setContent] = useState<BrandContent | null>(null);

  if (!projects.length) {
    return (
      <div className="card p-6 text-sm text-muted">
        Add a project on your Career Brain first — then come back to spin it into content.
      </div>
    );
  }

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/personal-brand/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId }),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Couldn't generate content.");
      else setContent(data);
    } catch {
      setError("Something went wrong — try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <FadeIn>
      <div className="card mb-6 flex flex-wrap items-center gap-3 p-6">
        <select
          className="input max-w-xs"
          value={projectId}
          onChange={(event) => setProjectId(event.target.value)}
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        <button className="btn" disabled={busy} onClick={generate}>
          {busy ? "Writing…" : "Generate content"}
        </button>
        {error && <p className="w-full text-sm text-red-400">{error}</p>}
      </div>

      {content && (
        <div className="space-y-4">
          <section className="card p-6">
            <h2 className="mb-3 text-lg font-medium">{content.case_study.title}</h2>
            <div className="grid gap-3 md:grid-cols-3">
              <Block title="Problem" body={content.case_study.problem} />
              <Block title="Approach" body={content.case_study.approach} />
              <Block title="Result" body={content.case_study.result} />
            </div>
          </section>
          <section className="card grid gap-3 p-6 md:grid-cols-2">
            <Block title="LinkedIn post" body={content.linkedin} />
            <Block title="X / Twitter thread" body={content.x_thread.join("\n\n")} />
            <Block title="Portfolio page" body={content.portfolio} />
            <Block title="Blog post" body={content.blog} />
          </section>
        </div>
      )}
    </FadeIn>
  );
}
