import { requireAccount } from "@/lib/session";
import { api, type WatchedCompany } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { WatchlistManager } from "@/components/watchlist/WatchlistManager";

export const dynamic = "force-dynamic";

export default async function WatchlistPage() {
  const { token, account } = await requireAccount();
  let watched: WatchedCompany[] = [];
  try {
    watched = await api.watchlist(token);
  } catch {
    watched = [];
  }

  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Watchlist</h1>
      <p className="mb-6 max-w-2xl text-sm text-muted">
        Monitor a company&apos;s hiring board and CareerOS surfaces new roles the day they post.
        Works with Greenhouse, Lever and Ashby — paste the company&apos;s board token (the name in
        its careers URL, e.g. <span className="text-white">stripe</span> for
        boards.greenhouse.io/stripe).
      </p>
      <WatchlistManager initial={watched} />
    </Shell>
  );
}
