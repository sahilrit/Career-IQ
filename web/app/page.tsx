import { redirect } from "next/navigation";
import { getToken } from "@/lib/session";

export default function Home() {
  redirect(getToken() ? "/dashboard" : "/login");
}
