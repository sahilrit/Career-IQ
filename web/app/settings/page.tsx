import { requireAccount } from "@/lib/session";
import { api, type AiStatus } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { AiKeyForm } from "@/components/settings/AiKeyForm";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const { token, account } = await requireAccount();
  let status: AiStatus = { has_key: false, model: "" };
  try {
    status = await api.aiStatus(token);
  } catch {
    // Leave the default (AI off) if the call fails.
  }

  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Settings</h1>
      <p className="mb-6 text-sm text-muted">
        Connect your own AI so CareerOS writes your cover letters. Without a key everything still
        works on free templates.
      </p>
      <AiKeyForm initial={status} />
    </Shell>
  );
}
