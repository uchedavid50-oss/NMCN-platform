"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { PREMIUM_LIFETIME_PRICE_LABEL } from "@/lib/pricing";
import { initializePayment, getSubscriptionStatus, SubscriptionStatus } from "@/lib/api-extras-4";

const PLAN = "premium_lifetime";

const FEATURES = [
  "Unlimited practice, mock exams and full CBT exam simulations",
  "Past questions and the full question bank",
  "AI tutor, study notes and flashcards",
  "Clinical cases, OSCE videos and viva prep",
  "Textbooks, analytics and the leaderboard",
];

export default function SubscribePage() {
  const { user, token, loading } = useRequireAuth();
  const { logout } = useAuth();
  const router = useRouter();
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

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  const isPaid = user.role === "admin" || user.subscription_status === "active" || status?.status === "active";

  return (
    <main className="relative mx-auto flex min-h-screen max-w-xl flex-col justify-center overflow-hidden px-6">
      <div className="ambient-glow" />
      <div className="auth-card animate-fade-in-up p-8">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Subscription</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
          {isPaid ? "You're on Premium" : "Unlock Cura Guide"}
        </h1>

        {isPaid ? (
          <div className="mt-6">
            <p className="text-graphite">Your access is active — no further payment needed.</p>
            <Link href="/dashboard" className="mt-6 inline-block text-sm text-vital-teal hover:underline">
              Go to dashboard →
            </Link>
          </div>
        ) : (
          <div className="mt-6">
            <p className="text-graphite">
              A one-time payment gives you lifetime access to everything on Cura Guide. Subscribe
              to start practicing.
            </p>
            <div className="mt-6 rounded-md border border-mist bg-card-bg p-5">
              <p className="font-display text-3xl font-semibold text-ink-navy">
                {PREMIUM_LIFETIME_PRICE_LABEL}
                <span className="ml-2 text-base font-normal text-graphite">one-time · lifetime access</span>
              </p>
              <ul className="mt-4 space-y-2 text-sm text-graphite">
                {FEATURES.map((f) => (
                  <li key={f} className="flex gap-2">
                    <span className="text-vital-teal">✓</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
            {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}
            <button
              onClick={handleSubscribe}
              disabled={starting}
              className="mt-6 w-full rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg disabled:opacity-50"
            >
              {starting ? "Redirecting to Paystack…" : `Pay ${PREMIUM_LIFETIME_PRICE_LABEL} with Paystack`}
            </button>
            <p className="mt-3 text-center text-xs text-graphite">
              Paid but still locked out? Refresh after a minute, or contact support.
            </p>
          </div>
        )}

        <button onClick={handleLogout} className="mt-6 inline-block text-sm text-vital-teal hover:underline">
          Log out
        </button>
      </div>
    </main>
  );
}
