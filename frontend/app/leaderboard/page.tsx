"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, LeaderboardEntry } from "@/lib/api";

export default function LeaderboardPage() {
  const { user, token, loading } = useRequireAuth();
  const [entries, setEntries] = useState<LeaderboardEntry[] | null>(null);
  const [optedIn, setOptedIn] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user || !token) return;
    setOptedIn(user.leaderboard_opt_in);
    setDisplayName(user.display_name ?? "");
    api
      .getLeaderboard(token)
      .then(setEntries)
      .catch(() => setError("Couldn't load the leaderboard."));
  }, [user, token]);

  async function handleSave() {
    if (!token) return;
    setSaving(true);
    setError(null);
    try {
      await api.setLeaderboardOptIn(optedIn, displayName || undefined, token);
      const updated = await api.getLeaderboard(token);
      setEntries(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save your preference.");
    } finally {
      setSaving(false);
    }
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Leaderboard</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Top streaks and speed-round scores
      </h1>
      <p className="mt-3 text-graphite">
        Opt-in only — your streak and scores are never shown to other students unless you choose
        to join, and only under a display name you pick, never your email.
      </p>

      <div className="mt-6 rounded-md border border-mist bg-card-bg p-5">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={optedIn}
            onChange={(e) => setOptedIn(e.target.checked)}
            className="h-4 w-4"
          />
          <span className="text-ink-navy">Show me on the leaderboard</span>
        </label>

        {optedIn && (
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Display name (e.g. Ada N.)"
            maxLength={30}
            className="mt-3 w-full rounded-md border border-mist px-3 py-2 text-sm focus:border-vital-teal focus:outline-none"
          />
        )}

        <button
          onClick={handleSave}
          disabled={saving}
          className="mt-3 rounded-md bg-vital-teal px-5 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save preference"}
        </button>
      </div>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      <div className="mt-8 flex flex-col gap-2">
        {entries?.map((entry, i) => (
          <div
            key={i}
            className="flex items-center justify-between rounded-md border border-mist px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-graphite">#{i + 1}</span>
              <span className="text-ink-navy">{entry.display_name}</span>
            </div>
            <div className="flex items-center gap-4 font-mono text-sm">
              <span className="text-pulse-coral">🔥 {entry.current_streak}d</span>
              <span className="text-vital-teal">{entry.best_score_percentage}%</span>
            </div>
          </div>
        ))}
        {entries && entries.length === 0 && (
          <p className="text-graphite">No one's opted in yet — be the first!</p>
        )}
      </div>

      <Link href="/dashboard" className="mt-8 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
