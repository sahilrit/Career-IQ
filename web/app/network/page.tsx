import { requireAccount } from "@/lib/session";
import { api, type Contact } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { AddContactForm } from "@/components/network/AddContactForm";

export const dynamic = "force-dynamic";

export default async function NetworkPage() {
  const { token, account } = await requireAccount();
  let contacts: Contact[] = [];
  try {
    contacts = await api.contacts(token);
  } catch {
    /* empty */
  }

  return (
    <Shell account={account}>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Network</h1>
      <AddContactForm />
      {contacts.length === 0 ? (
        <div className="card p-6 text-muted">No contacts yet — add one above.</div>
      ) : (
        <div className="space-y-2">
          {contacts.map((contact) => (
            <div key={contact.id} className="card flex items-center justify-between gap-4 p-4">
              <div>
                <div className="font-medium">{contact.name}</div>
                <div className="text-sm text-muted">
                  {contact.organization_name || "—"}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full border border-line px-2.5 py-0.5 text-xs text-muted">
                  {contact.role.replace(/_/g, " ")}
                </span>
                {contact.stage && (
                  <span className="text-xs text-muted">{contact.stage.replace(/_/g, " ")}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Shell>
  );
}
