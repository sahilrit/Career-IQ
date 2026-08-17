"use client";

import { useFormState } from "react-dom";
import type { ClientRow } from "@/lib/api";
import { addClient, addContract, addInvoice } from "@/app/clients/actions";
import { SubmitButton } from "@/components/brain/SubmitButton";

function AddClient() {
  const [state, action] = useFormState(addClient, null);
  return (
    <form action={action} className="flex gap-2">
      <input name="name" className="input" placeholder="Client / business name" />
      <SubmitButton>Add client</SubmitButton>
      {state && !state.ok && <p className="text-sm text-red-400">{state.error}</p>}
    </form>
  );
}

function AddContract({ clientId }: { clientId: string }) {
  const [state, action] = useFormState(addContract, null);
  return (
    <form action={action} className="mt-3 grid gap-2 sm:grid-cols-4">
      <input type="hidden" name="client_id" value={clientId} />
      <input name="title" className="input sm:col-span-2" placeholder="Contract title" />
      <input name="rate" type="number" step="0.01" className="input" placeholder="Rate" />
      <input name="start_date" type="date" className="input" />
      <div className="sm:col-span-4">
        <SubmitButton>Add contract</SubmitButton>
      </div>
      {state && !state.ok && <p className="text-sm text-red-400 sm:col-span-4">{state.error}</p>}
    </form>
  );
}

function AddInvoice({ contractId }: { contractId: string }) {
  const [state, action] = useFormState(addInvoice, null);
  return (
    <form action={action} className="mt-2 flex flex-wrap items-center gap-2">
      <input type="hidden" name="contract_id" value={contractId} />
      <input name="amount" type="number" step="0.01" className="input max-w-32" placeholder="Invoice $" />
      <input name="due_date" type="date" className="input max-w-44" />
      <SubmitButton>Invoice</SubmitButton>
      {state && !state.ok && <p className="w-full text-sm text-red-400">{state.error}</p>}
    </form>
  );
}

export function ClientsBoard({ clients }: { clients: ClientRow[] }) {
  return (
    <div>
      <section className="card mb-4 p-6">
        <h2 className="mb-3 text-sm uppercase tracking-wide text-muted">Add a client</h2>
        <AddClient />
      </section>

      {clients.length === 0 ? (
        <div className="card p-6 text-sm text-muted">
          No clients yet. Add one above to track contracts, invoices, and outstanding balances.
        </div>
      ) : (
        <div className="space-y-4">
          {clients.map((client) => (
            <section key={client.id} className="card p-6">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-medium">{client.name}</h2>
                {client.lifecycle_stage && (
                  <span className="rounded-full border border-line px-2 py-0.5 text-xs text-muted capitalize">
                    {client.lifecycle_stage.replace(/_/g, " ")}
                  </span>
                )}
              </div>
              <div className="space-y-3">
                {client.contracts.map((contract) => (
                  <div key={contract.id} className="rounded-lg border border-line bg-ink/40 p-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{contract.title}</span>
                      <span className="text-muted capitalize">{contract.status}</span>
                    </div>
                    <div className="mt-1 text-xs text-muted">
                      Rate ${contract.rate.toLocaleString()} · Outstanding $
                      {contract.outstanding.toLocaleString()}
                    </div>
                    <AddInvoice contractId={contract.id} />
                  </div>
                ))}
                {client.contracts.length === 0 && (
                  <p className="text-sm text-muted">No contracts yet.</p>
                )}
              </div>
              <AddContract clientId={client.id} />
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
