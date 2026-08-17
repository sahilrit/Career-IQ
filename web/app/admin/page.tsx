import { redirect } from "next/navigation";
import { requireAccount } from "@/lib/session";
import { api, type AdminOverview } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { ActivateForm } from "@/components/admin/ActivateForm";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const { token, account } = await requireAccount();
  if (!account.is_admin) redirect("/dashboard");

  let overview: AdminOverview | null = null;
  try {
    overview = await api.adminOverview(token);
  } catch {
    overview = null;
  }

  return (
    <Shell account={account}>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Admin</h1>
      {!overview ? (
        <div className="card p-6 text-muted">Admin data is unavailable.</div>
      ) : (
        <>
          <div className="mb-6 grid grid-cols-3 gap-4">
            <div className="card p-5">
              <div className="text-3xl font-semibold">{overview.accounts}</div>
              <div className="mt-1 text-sm text-muted">Accounts</div>
            </div>
            <div className="card p-5">
              <div className="text-3xl font-semibold">{overview.paying_workspaces}</div>
              <div className="mt-1 text-sm text-muted">Paying workspaces</div>
            </div>
            <div className="card p-5">
              <div className="text-3xl font-semibold">${overview.mrr.toLocaleString()}</div>
              <div className="mt-1 text-sm text-muted">MRR</div>
            </div>
          </div>

          <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Customers</h2>
          <div className="mb-6 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-muted">
                <tr>
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Plan</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2">Joined</th>
                </tr>
              </thead>
              <tbody>
                {overview.customers.map((customer) => (
                  <tr key={customer.workspace_id} className="border-t border-line">
                    <td className="py-2 pr-4">{customer.name}</td>
                    <td className="py-2 pr-4">{customer.email}</td>
                    <td className="py-2 pr-4">{customer.plan}</td>
                    <td className="py-2 pr-4">{customer.status}</td>
                    <td className="py-2">{customer.joined}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Activate a plan</h2>
          <ActivateForm customers={overview.customers} />
        </>
      )}
    </Shell>
  );
}
