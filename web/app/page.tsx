import Link from "next/link";
import { redirect } from "next/navigation";
import { getToken } from "@/lib/session";
import { FadeIn, Stagger, StaggerItem } from "@/components/Motion";

const FEATURES = [
  ["🧠 Career Brain", "One authoritative profile powering every resume and pitch."],
  ["🎯 Opportunity discovery", "Jobs and freelance clients found and scored for you."],
  ["📄 One-click applications", "Tailored resume + cover letter per posting."],
  ["🤖 Autopilot", "Applies for you across open ATS boards — safely, with handoffs."],
  ["💼 Freelance CRM", "Prospects, website audits, pitch kits, clients, and income."],
  ["🔒 Private by design", "Your workspace is isolated; export or delete anytime."],
];

const PLANS = [
  { name: "Free", price: "$0", points: ["Career Brain", "Job discovery", "Basic applications"] },
  {
    name: "Pro",
    price: "$29",
    points: ["Everything in Free", "Autopilot", "Freelance acquisition", "Analytics"],
    featured: true,
  },
  {
    name: "Agency",
    price: "$99",
    points: ["Everything in Pro", "Multiple workspaces", "Team members", "API access"],
  },
];

export default function Home() {
  if (getToken()) redirect("/dashboard");

  return (
    <div className="mx-auto max-w-5xl px-5 py-6">
      <header className="flex items-center justify-between">
        <span className="text-lg font-semibold tracking-tight">CareerOS</span>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm text-white/80 hover:text-white">
            Log in
          </Link>
          <Link href="/signup" className="btn text-sm">
            Get started
          </Link>
        </div>
      </header>

      <FadeIn>
        <section className="py-20 text-center sm:py-28">
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">
            Your career, run like a company.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted">
            CareerOS builds a Career Brain from your real experience, finds matching jobs and
            freelance clients, writes tailored applications, and — on autopilot — applies for you.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link href="/signup" className="btn">
              Start free
            </Link>
            <Link href="/login" className="btn-ghost">
              Log in
            </Link>
          </div>
        </section>
      </FadeIn>

      <Stagger>
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(([title, body]) => (
            <StaggerItem key={title}>
              <div className="card h-full p-6">
                <div className="font-medium">{title}</div>
                <p className="mt-2 text-sm text-muted">{body}</p>
              </div>
            </StaggerItem>
          ))}
        </section>
      </Stagger>

      <section className="py-20">
        <h2 className="mb-8 text-center text-2xl font-semibold tracking-tight">Pricing</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`card p-6 ${plan.featured ? "ring-1 ring-accent" : ""}`}
            >
              <div className="text-lg font-medium">{plan.name}</div>
              <div className="mb-4 text-3xl font-semibold">
                {plan.price}
                <span className="text-sm font-normal text-muted">/mo</span>
              </div>
              <ul className="mb-6 space-y-1 text-sm text-muted">
                {plan.points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
              <Link href="/signup" className={plan.featured ? "btn w-full" : "btn-ghost w-full"}>
                Get started
              </Link>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-line py-8 text-center text-sm text-muted">
        <div>CareerOS — built to help you land the work.</div>
        <div className="mt-2">
          <Link href="/terms" className="transition hover:text-white">
            Terms
          </Link>
          <span className="mx-2">·</span>
          <Link href="/privacy" className="transition hover:text-white">
            Privacy
          </Link>
        </div>
      </footer>
    </div>
  );
}
