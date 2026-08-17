import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Warm ink base with layered surfaces for real depth (not flat).
        ink: "#0b0b0e",
        panel: "#141319",
        raised: "#1c1b23",
        line: "#2a2932",
        lineSoft: "#211f28",
        muted: "#9d9aa8",
        // Signal-gold accent: opportunity, value, the "career gold".
        accent: "#f0b544",
        accentSoft: "#f7cd77",
        accentInk: "#221704", // dark text on gold
        // A cool secondary for quiet links/secondary marks.
        iris: "#8b8cff",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "ui-serif", "Georgia", "serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 20px 50px -24px rgba(0,0,0,0.7)",
        raised: "0 1px 0 0 rgba(255,255,255,0.05) inset, 0 8px 24px -12px rgba(0,0,0,0.6)",
        glow: "0 10px 34px -10px rgba(240,181,68,0.5)",
      },
      letterSpacing: {
        tightest: "-0.03em",
      },
    },
  },
  plugins: [],
};

export default config;
