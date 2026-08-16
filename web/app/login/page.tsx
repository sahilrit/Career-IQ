import { AuthForm } from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <AuthForm mode="login" />
    </div>
  );
}
