"use client";

import { useState } from "react";
import type { PitchKit } from "@/lib/api";
import { FadeIn } from "@/components/Motion";

type Ad = { headline: string; body_text: string; cta: string; landing_page_url: string };

function Deliverable({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <div className="mb-1 text-xs uppercase tracking-wide text-muted">{title}</div>
      <textarea readOnly className="input min-h-40 text-xs" value={body} />
    </div>
  );
}

export function PitchKitStudio() {
  const [company, setCompany] = useState({ company_name: "", website: "", industry: "" });
  const [roi, setRoi] = useState({ monthly_visitors: "", conversion_rate: "", average_order_value: "" });
  const [ads, setAds] = useState<Ad[]>([{ headline: "", body_text: "", cta: "", landing_page_url: "" }]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [kit, setKit] = useState<PitchKit | null>(null);

  function num(value: string): number | null {
    const parsed = Number(value);
    return value.trim() === "" || Number.isNaN(parsed) ? null : parsed;
  }

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/audit/pitch-kit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...company,
          monthly_visitors: num(roi.monthly_visitors),
          conversion_rate: num(roi.conversion_rate),
          average_order_value: num(roi.average_order_value),
          ads: ads.filter((ad) => ad.headline || ad.body_text),
        }),
      });
      const data = await response.json();
      if (!response.ok) setError(data.error ?? "Couldn't build the pitch kit.");
      else setKit(data);
    } catch {
      setError("Something went wrong — try again.");
    } finally {
      setBusy(false);
    }
  }

  function pdfHref(base64: string) {
    return `data:application/pdf;base64,${base64}`;
  }

  return (
    <FadeIn>
      <div className="card mb-6 space-y-4 p-6">
        <div className="grid gap-2 sm:grid-cols-3">
          <input
            className="input"
            placeholder="Business name"
            value={company.company_name}
            onChange={(e) => setCompany({ ...company, company_name: e.target.value })}
          />
          <input
            className="input"
            placeholder="Website (e.g. brand.com)"
            value={company.website}
            onChange={(e) => setCompany({ ...company, website: e.target.value })}
          />
          <input
            className="input"
            placeholder="Industry"
            value={company.industry}
            onChange={(e) => setCompany({ ...company, industry: e.target.value })}
          />
        </div>

        <div>
          <div className="mb-1 text-xs uppercase tracking-wide text-muted">
            ROI inputs (optional — powers the revenue projection)
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            <input
              className="input"
              type="number"
              placeholder="Monthly visitors"
              value={roi.monthly_visitors}
              onChange={(e) => setRoi({ ...roi, monthly_visitors: e.target.value })}
            />
            <input
              className="input"
              type="number"
              step="0.001"
              placeholder="Conversion rate (e.g. 0.02)"
              value={roi.conversion_rate}
              onChange={(e) => setRoi({ ...roi, conversion_rate: e.target.value })}
            />
            <input
              className="input"
              type="number"
              step="0.01"
              placeholder="Avg order value ($)"
              value={roi.average_order_value}
              onChange={(e) => setRoi({ ...roi, average_order_value: e.target.value })}
            />
          </div>
        </div>

        <div>
          <div className="mb-1 text-xs uppercase tracking-wide text-muted">
            Their Meta ads (optional — paste a few to audit them)
          </div>
          {ads.map((ad, index) => (
            <div key={index} className="mb-2 grid gap-2 sm:grid-cols-2">
              <input
                className="input"
                placeholder="Ad headline"
                value={ad.headline}
                onChange={(e) => {
                  const next = [...ads];
                  next[index] = { ...ad, headline: e.target.value };
                  setAds(next);
                }}
              />
              <input
                className="input"
                placeholder="Ad body text"
                value={ad.body_text}
                onChange={(e) => {
                  const next = [...ads];
                  next[index] = { ...ad, body_text: e.target.value };
                  setAds(next);
                }}
              />
            </div>
          ))}
          <button
            type="button"
            className="btn-ghost text-xs"
            onClick={() => setAds([...ads, { headline: "", body_text: "", cta: "", landing_page_url: "" }])}
          >
            + Add another ad
          </button>
        </div>

        <div>
          <button className="btn" disabled={busy || !company.company_name} onClick={generate}>
            {busy ? "Building your pitch kit…" : "Generate pitch kit"}
          </button>
          {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
        </div>
      </div>

      {kit && (
        <div className="space-y-4">
          {kit.roi && (
            <section className="card p-6">
              <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Revenue opportunity</h2>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl border border-line bg-ink/40 p-4">
                  <div className="text-xs text-muted">Current monthly</div>
                  <div className="mt-1 text-xl font-semibold">
                    ${Math.round(kit.roi.current_monthly_revenue).toLocaleString()}
                  </div>
                </div>
                <div className="rounded-xl border border-line bg-ink/40 p-4">
                  <div className="text-xs text-muted">Extra / month</div>
                  <div className="mt-1 text-xl font-semibold">
                    ${Math.round(kit.roi.projected_additional_monthly_revenue).toLocaleString()}
                  </div>
                </div>
                <div className="rounded-xl border border-line bg-ink/40 p-4">
                  <div className="text-xs text-muted">Extra / year</div>
                  <div className="mt-1 text-xl font-semibold text-accentSoft">
                    ${Math.round(kit.roi.projected_additional_annual_revenue).toLocaleString()}
                  </div>
                </div>
              </div>
              <p className="mt-3 text-xs text-muted">{kit.roi.disclaimer}</p>
            </section>
          )}

          <section className="card p-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm uppercase tracking-wide text-muted">Findings</h2>
              <a href={pdfHref(kit.pdf_base64)} download="proposal.pdf" className="btn-ghost text-xs">
                Download PDF proposal
              </a>
            </div>
            <ul className="space-y-2">
              {kit.findings.map((finding, index) => (
                <li key={index} className="rounded-lg border border-line bg-ink/40 px-3 py-2 text-sm">
                  <div className="font-medium capitalize">{finding.category}</div>
                  <div className="text-muted">{finding.detail}</div>
                  <div className="mt-1">→ {finding.recommendation}</div>
                </li>
              ))}
              {kit.findings.length === 0 && (
                <p className="text-sm text-muted">
                  No findings yet — add a couple of their ads above to generate an audit.
                </p>
              )}
            </ul>
          </section>

          <section className="card grid gap-3 p-6 md:grid-cols-2">
            <div className="md:col-span-2">
              <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-muted">
                Written proposal
                <span
                  className={
                    kit.ai_used
                      ? "rounded-full bg-accent/20 px-2 py-0.5 text-[10px] normal-case text-accentSoft"
                      : "rounded-full border border-line px-2 py-0.5 text-[10px] normal-case text-muted"
                  }
                >
                  {kit.ai_used ? "✨ AI-written" : "Template"}
                </span>
              </div>
              <textarea readOnly className="input min-h-48 text-xs" value={kit.proposal} />
            </div>
            <Deliverable title="Cold email" body={kit.email} />
            <Deliverable title="LinkedIn message" body={kit.linkedin_message} />
            <Deliverable title="Loom walkthrough script" body={kit.loom_script} />
          </section>
        </div>
      )}
    </FadeIn>
  );
}
