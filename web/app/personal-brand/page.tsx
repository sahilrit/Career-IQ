import { requireAccount } from "@/lib/session";
import { api, type BrandProject } from "@/lib/api";
import { Shell } from "@/components/Shell";
import { BrandStudio } from "@/components/personalbrand/BrandStudio";

export const dynamic = "force-dynamic";

export default async function PersonalBrandPage() {
  const { token, account } = await requireAccount();
  let projects: BrandProject[] = [];
  try {
    projects = await api.brandProjects(token);
  } catch {
    projects = [];
  }
  return (
    <Shell account={account}>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Personal Brand</h1>
      <p className="mb-6 text-sm text-muted">
        Turn a project into a case study, LinkedIn post, X thread, portfolio page, and blog post.
      </p>
      <BrandStudio projects={projects} />
    </Shell>
  );
}
