import { AuthForm } from "@/components/AuthForm";
import { Wordmark } from "@/components/Wordmark";
import { AppAmbience } from "@/components/AppAmbience";

export default function LoginPage() {
  return (
    <>
      <AppAmbience scrim={0.5} vignette={0.5} density={110} />
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center gap-7 px-4">
        <Wordmark />
        <AuthForm mode="login" />
      </div>
    </>
  );
}
