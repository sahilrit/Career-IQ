import { requireAccount } from "@/lib/session";
import { api, type Prospect } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { AddProspectForm } from "@/components/freelance/AddProspectForm";

export const dynamic = "force-dynamic";

export default async function FreelancePage() {
  const { token, account } = await requireAccount();
  let prospects: Prospect[] = [];
  try {
    prospects = await api.prospects(token);
  } catch {
    /* empty */
  }

  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Freelance</h1>
      <p className="mb-6 text-muted">
        Track prospect businesses to pitch. Run the website audit + pitch kit in the app; this is
        your prospect pipeline.
      </p>
      <AddProspectForm />
      {prospects.length === 0 ? (
        <div className="card p-6 text-muted">No prospects yet — add a business above.</div>
      ) : (
        <div className="space-y-2">
          {prospects.map((prospect) => (
            <div key={prospect.id} className="card flex items-center justify-between gap-4 p-4">
              <div className="min-w-0">
                <div className="truncate font-medium">{prospect.name}</div>
                <a
                  href={prospect.website}
                  target="_blank"
                  rel="noreferrer"
                  className="truncate text-sm text-accentSoft hover:underline"
                >
                  {prospect.website}
                </a>
              </div>
              {prospect.stage && (
                <span className="rounded-full border border-line px-2.5 py-0.5 text-xs text-muted">
                  {prospect.stage.replace(/_/g, " ")}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </Shell>
  );
}
