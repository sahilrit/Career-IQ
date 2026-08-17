import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center px-6 text-center">
      <div className="eyebrow mb-4">Error 404</div>
      <h1 className="font-display text-4xl font-medium tracking-tightest sm:text-5xl">
        This page took a different job.
      </h1>
      <p className="mt-4 text-muted">
        The page you&apos;re looking for doesn&apos;t exist or has moved.
      </p>
      <Link href="/dashboard" className="btn mt-8">
        Back to dashboard
      </Link>
    </div>
  );
}
