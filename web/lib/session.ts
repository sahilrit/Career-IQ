// Server-side session helpers. The careeros-api bearer token lives only
// in an httpOnly cookie — never readable by client JS — which also means
// a full page refresh stays logged in (fixing the Streamlit limitation).

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { api, type Account } from "@/lib/api";

export const SESSION_COOKIE = "careeros_token";

export function getToken(): string | undefined {
  return cookies().get(SESSION_COOKIE)?.value;
}

export async function requireAccount(): Promise<{ token: string; account: Account }> {
  const token = getToken();
  if (!token) redirect("/login");
  try {
    const account = await api.me(token);
    return { token, account };
  } catch {
    redirect("/login");
  }
}
