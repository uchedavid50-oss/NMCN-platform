"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ApiError } from "@/lib/api";
import { initializePayment, getSubscriptionStatus, SubscriptionStatus } from "@/lib/api-extras-4";

const PLAN = "premium_monthly";
const PLAN_LABEL = "Premium — ₦5,000/month";

export default function SubscribePage() {
  const { user, token, loading } = useRequireAuth();
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    getSubscriptionStatus(token).then(setStatus).catch(() => {});
  }, [token]);

  async function handleSubscribe() {
    if (!token) return;
    setStarting(true);
    setError(null);
    try {
      const result = await initializePayment(PLAN, token);
      window.location.href = result.authorization_url;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't start checkout. Try again.");
      setStarting(false);
    }
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  const isActive = status?.status === "active";

  return (
    <main className="relative mx-auto flex min-h-screen max-w-xl flex-col justify-center overflow-hidden px-6">
      <div className="ambient-glow" />
      <div className="auth-card animate-fade-in-up p-8">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Subscription</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
          {isActive ? "You're on Premium" : "Unlock unlimited practice"}
        </h1>

        {isActive ? (
          <div className="mt-6">
            <p className="text-graphite">
              Your subscription is active
              {status?.expires_at &&
                ` until ${new Date(
                  status.expires_at.endsWith("Z") ? status.expires_at : `${status.expires_at}Z`
                ).toLocaleDateString()}`}
              .
            </p>
            <p className="mt-2 text-sm text-graphite">
              Unlimited mock exams, full CBT exam simulations, and everything else on the free
              tier — no limits.
            </p>
          </div>
        ) : (
          <div className="mt-6">
            <p className="text-graphite">
              Free accounts are limited to a small number of mock exams and one full CBT exam
              simulation. Upgrade for unlimited access to every practice mode.
            </p>
            <div className="mt-6 rounded-md border border-mist bg-card-bg p-5">
              <p className="font-display text-xl font-semibold text-ink-navy">{PLAN_LABEL}</p>
              <p className="mt-1 text-sm text-graphite">Unlimited mock exams &amp; CBT exams</p>
            </div>
            {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}
            <button
              onClick={handleSubscribe}
              disabled={starting}
              className="mt-6 w-full rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg disabled:opacity-50"
            >
              {starting ? "Redirecting to Paystack…" : "Subscribe with Paystack"}
            </button>
          </div>
        )}

        <Link href="/dashboard" className="mt-6 inline-block text-sm text-vital-teal hover:underline">
          ← Back to dashboard
        </Link>
      </div>
    </main>
  );
}
