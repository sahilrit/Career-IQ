import { redirect } from "next/navigation";
import { getToken } from "@/lib/session";
import { Landing } from "@/components/landing/Landing";

export default function Home() {
  if (getToken()) redirect("/dashboard");
  return <Landing />;
}
