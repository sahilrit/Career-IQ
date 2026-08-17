import type { Metadata } from "next";
import { Fraunces, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Fraunces: a characterful high-contrast serif for display — the signature
// that makes this read as designed, not a templated grotesque SaaS.
const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});
const sans = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

const SITE_URL = process.env.CAREEROS_APP_BASE_URL ?? "https://careeros-web-1tor.onrender.com";
const DESCRIPTION =
  "Run your career and freelance business like a company. CareerOS builds a Career Brain from your real experience, finds the work worth pursuing, and writes the applications and pitches to win it.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "CareerOS — the operating system for your career",
  description: DESCRIPTION,
  applicationName: "CareerOS",
  keywords: ["career", "job search", "AI résumé", "cover letter", "freelance", "pitch kit", "autopilot"],
  openGraph: {
    type: "website",
    url: "/",
    siteName: "CareerOS",
    title: "CareerOS — the operating system for your career",
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: "CareerOS — the operating system for your career",
    description: DESCRIPTION,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
