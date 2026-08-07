"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ApiError } from "@/lib/api";
import { verifyEmail } from "@/lib/api-extras-3";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("This verification link is missing its token — please use the link from your email.");
      return;
    }
    verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err) => {
        setStatus("error");
        setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
      });
  }, [token]);

  if (status === "verifying") {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Verifying…</p>
      </main>
    );
  }

  if (status === "success") {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 text-center">
        <h1 className="font-display text-3xl font-semibold text-ink-navy">Email verified</h1>
        <p className="mt-3 text-graphite">Your account is active — you can log in now.</p>
        <Link
          href="/login"
          className="mt-6 inline-block rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
        >
          Go to login
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 text-center">
      <h1 className="font-display text-3xl font-semibold text-ink-navy">Verification failed</h1>
      <p className="mt-3 text-pulse-coral">{error}</p>
      <p className="mt-3 text-graphite">
        Links expire after 48 hours. Try logging in — you&apos;ll be able to request a new one there.
      </p>
      <Link href="/login" className="mt-6 text-vital-teal hover:underline">
        ← Back to login
      </Link>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center">
          <p className="font-mono text-sm text-graphite">Loading…</p>
        </main>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
