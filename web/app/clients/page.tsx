import { requireAccount } from "@/lib/session";
import { api, type ClientRow } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { ClientsBoard } from "@/components/clients/ClientsBoard";

export const dynamic = "force-dynamic";

export default async function ClientsPage() {
  const { token, account } = await requireAccount();
  let clients: ClientRow[] = [];
  try {
    clients = await api.clients(token);
  } catch {
    clients = [];
  }
  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Clients</h1>
      <p className="mb-6 text-sm text-muted">
        Track your freelance clients — contracts, invoices, outstanding balances, and lifecycle.
      </p>
      <ClientsBoard clients={clients} />
    </Shell>
  );
}
