import { AuthForm } from "@/components/AuthForm";
import { Wordmark } from "@/components/Wordmark";

export default function SignupPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-7 px-4">
      <Wordmark />
      <AuthForm mode="signup" />
    </div>
  );
}
