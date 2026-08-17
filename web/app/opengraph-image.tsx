import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "CareerOS — the operating system for your career";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Branded social-share card, rendered at the edge (system serif/sans — no
// external font fetch needed).
export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px",
          background:
            "radial-gradient(1100px 620px at 85% -10%, rgba(240,181,68,0.22), transparent 60%), #0b0b0e",
          color: "#ffffff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 14,
              background: "#f0b544",
              color: "#221704",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 34,
              fontWeight: 700,
              fontFamily: "Georgia, serif",
            }}
          >
            C
          </div>
          <div style={{ fontSize: 34, fontWeight: 600, fontFamily: "Georgia, serif" }}>CareerOS</div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div
            style={{
              fontSize: 76,
              lineHeight: 1.05,
              fontWeight: 600,
              fontFamily: "Georgia, serif",
              letterSpacing: -1,
              maxWidth: 900,
            }}
          >
            Run your career like a <span style={{ color: "#f0b544", fontStyle: "italic" }}>company.</span>
          </div>
          <div style={{ fontSize: 30, color: "#9d9aa8", maxWidth: 860 }}>
            A Career Brain, opportunity discovery, and AI applications & pitch kits — in one workspace.
          </div>
        </div>

        <div
          style={{
            fontSize: 22,
            color: "#9d9aa8",
            fontFamily: "monospace",
            letterSpacing: 3,
            textTransform: "uppercase",
          }}
        >
          The operating system for your career
        </div>
      </div>
    ),
    { ...size },
  );
}
