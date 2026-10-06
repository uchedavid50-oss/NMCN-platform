"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { useAuth } from "@/lib/auth-context";
import { getSubscriptionStatus, verifyPayment } from "@/lib/api-extras-4";
import { Confetti } from "@/components/Confetti";
import { Mascot } from "@/components/Mascot";

function PaymentCallbackContent() {
  const { user, token, loading } = useRequireAuth();
  const { refreshUser } = useAuth();
  const searchParams = useSearchParams();
  // Paystack appends ?reference=...&trxref=... when it redirects back.
  const reference = searchParams.get("reference") || searchParams.get("trxref");
  const [isActive, setIsActive] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [celebrated, setCelebrated] = useState(false);
  const MAX_ATTEMPTS = 6;

  useEffect(() => {
    if (!token) return;
    if (isActive) return;
    if (attempts >= MAX_ATTEMPTS) return;

    const t = setTimeout(async () => {
      try {
        // The backend verifies the transaction with Paystack and activates
        // the account itself (idempotent), so this doesn't depend on the
        // webhook having arrived. Without a reference (page opened by hand)
        // we can only read the current status.
        const active = reference
          ? (await verifyPayment(reference, token)).subscription_status === "active"
          : (await getSubscriptionStatus(token)).status === "active";
        if (active) {
          await refreshUser();
          setIsActive(true);
        }
      } catch {
        // ignore, will retry
      } finally {
        setAttempts((a) => a + 1);
      }
    }, attempts === 0 ? 0 : 2000);

    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, reference, isActive, attempts]);

  useEffect(() => {
    if (isActive) setCelebrated(true);
  }, [isActive]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  const stillWaiting = !isActive && attempts < MAX_ATTEMPTS;

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 text-center">
      {celebrated && <Confetti />}
      {isActive ? (
        <>
          <Mascot className="h-24 w-24" />
          <h1 className="mt-4 font-display text-2xl font-semibold text-ink-navy">
            You're all set!
          </h1>
          <p className="mt-2 text-graphite">Your Premium access is now active.</p>
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
            Your payment may still be confirming on Paystack's side. Refresh this page in a
            minute — no need to pay twice. If it still doesn't unlock, contact support and
            we'll activate your account.
          </p>
        </>
      )}
      <Link
        href={isActive ? "/dashboard" : "/subscribe"}
        className="mt-8 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg"
      >
        {isActive ? "Go to dashboard" : "Back to subscription"}
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
