import { AuthForm } from "@/components/AuthForm";
import { Wordmark } from "@/components/Wordmark";
import { AppAmbience } from "@/components/AppAmbience";

export default function SignupPage() {
  return (
    <>
      <AppAmbience />
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center gap-7 px-4">
        <Wordmark />
        <AuthForm mode="signup" />
      </div>
    </>
  );
}
