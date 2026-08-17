import { ResetPasswordForm } from "@/components/ResetPasswordForm";

export const dynamic = "force-dynamic";

export default function ResetPage({
  searchParams,
}: {
  searchParams: { token?: string };
}) {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <ResetPasswordForm token={searchParams.token ?? ""} />
    </div>
  );
}
