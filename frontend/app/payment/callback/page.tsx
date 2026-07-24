"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { getSubscriptionStatus, SubscriptionStatus } from "@/lib/api-extras-4";

function PaymentCallbackContent() {
  const { user, token, loading } = useRequireAuth();
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [attempts, setAttempts] = useState(0);
  const MAX_ATTEMPTS = 6;

  useEffect(() => {
    if (!token) return;
    if (status?.status === "active") return;
    if (attempts >= MAX_ATTEMPTS) return;

    const t = setTimeout(async () => {
      try {
        const result = await getSubscriptionStatus(token);
        setStatus(result);
      } catch {
        // ignore, will retry
      } finally {
        setAttempts((a) => a + 1);
      }
    }, 2000);

    return () => clearTimeout(t);
  }, [token, status, attempts]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  const isActive = status?.status === "active";
  const stillWaiting = !isActive && attempts < MAX_ATTEMPTS;

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 text-center">
      {isActive ? (
        <>
          <p className="text-4xl">✅</p>
          <h1 className="mt-4 font-display text-2xl font-semibold text-ink-navy">
            You're all set!
          </h1>
          <p className="mt-2 text-graphite">Your premium subscription is now active.</p>
        </>
      ) : stillWaiting ? (
        <>
          <p className="text-4xl">⏳</p>
          <h1 className="mt-4 font-display text-2xl font-semibold text-ink-navy">
            Confirming your payment…
          </h1>
          <p className="mt-2 text-graphite">This usually takes just a few seconds.</p>
        </>
      ) : (
        <>
          <p className="text-4xl">⚠️</p>
          <h1 className="mt-4 font-display text-2xl font-semibold text-ink-navy">
            Still processing
          </h1>
          <p className="mt-2 text-graphite">
            Your payment may still be confirming on Paystack's side. If this doesn't update
            shortly, check your subscription status again in a few minutes — no need to pay
            twice.
          </p>
        </>
      )}
      <Link
        href="/dashboard"
        className="mt-8 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg"
      >
        Back to dashboard
      </Link>
    </main>
  );
}

export default function PaymentCallbackPage() {
  return (
    <Suspense fallback={<main className="flex min-h-screen items-center justify-center"><p>Loading…</p></main>}>
      <PaymentCallbackContent />
    </Suspense>
  );
}
