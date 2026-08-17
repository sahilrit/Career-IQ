import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#09090c",
        panel: "#15151c",
        line: "#26262f",
        muted: "#9a9aa6",
        accent: "#6d5efc",
        accentSoft: "#8b7bff",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 12px 40px -12px rgba(0,0,0,0.5)",
        glow: "0 8px 30px -8px rgba(109,94,252,0.45)",
      },
    },
  },
  plugins: [],
};

export default config;
