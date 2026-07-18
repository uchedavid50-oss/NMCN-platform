"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ThemeToggle } from "@/components/ThemeToggle";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const { logout } = useAuth();
  const { user, token, loading } = useRequireAuth();
  const [streak, setStreak] = useState<number | null>(null);

  useEffect(() => {
    if (!token) return;
    api.getStreak(token).then((s) => setStreak(s.current_streak)).catch(() => setStreak(0));
  }, [token]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Dashboard</p>
          <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
            Welcome back, {user.email}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button
            onClick={logout}
            className="rounded-md border border-mist px-4 py-2 text-sm font-medium text-ink-navy hover:border-pulse-coral hover:text-pulse-coral"
          >
            Log out
          </button>
        </div>
      </div>

      <div className="mt-10 grid grid-cols-2 gap-4 font-mono text-sm sm:grid-cols-3">
        <div className="rounded-md border border-mist p-4">
          <p className="text-graphite">Role</p>
          <p className="mt-1 text-lg text-ink-navy">{user.role}</p>
        </div>
        <div className="rounded-md border border-mist p-4">
          <p className="text-graphite">Subscription</p>
          <p className="mt-1 text-lg text-ink-navy">{user.subscription_status}</p>
        </div>
        <div className="rounded-md border border-mist p-4">
          <p className="text-graphite">Streak</p>
          <p className="mt-1 text-lg text-pulse-coral">
            {streak === null ? "…" : `🔥 ${streak} day${streak === 1 ? "" : "s"}`}
          </p>
        </div>
      </div>

      <div className="mt-10 flex flex-wrap gap-3">
        <Link
          href="/subjects"
          className="inline-block rounded-md bg-vital-teal px-6 py-3 font-body font-medium text-chart-cream transition hover:bg-ink-navy"
        >
          Start practicing
        </Link>
        <Link
          href="/games/speed-round"
          className="inline-block rounded-md bg-pulse-coral px-6 py-3 font-body font-medium text-chart-cream transition hover:bg-ink-navy"
        >
          ⚡ Speed round
        </Link>
        <Link
          href="/analytics"
          className="inline-block rounded-md border border-mist px-6 py-3 font-body font-medium text-ink-navy transition hover:border-vital-teal"
        >
          View my progress
        </Link>
        <Link
          href="/notes"
          className="inline-block rounded-md border border-mist px-6 py-3 font-body font-medium text-ink-navy transition hover:border-vital-teal"
        >
          My notes
        </Link>
        <Link
          href="/leaderboard"
          className="inline-block rounded-md border border-mist px-6 py-3 font-body font-medium text-ink-navy transition hover:border-vital-teal"
        >
          🏆 Leaderboard
        </Link>
      </div>
    </main>
  );
}
