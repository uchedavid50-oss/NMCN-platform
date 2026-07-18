"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError } from "@/lib/api";

export default function CBTExamIntroPage() {
  const { user, token, loading } = useRequireAuth();
  const router = useRouter();
  const [questionCount, setQuestionCount] = useState(250);
  const [durationMinutes, setDurationMinutes] = useState(240);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleStart() {
    if (!token) return;
    setStarting(true);
    setError(null);
    try {
      const session = await api.startCBTExam(questionCount, durationMinutes, token);
      sessionStorage.setItem(`cbt-exam-${session.session_id}`, JSON.stringify(session));
      router.push(`/cbt-exam/${session.session_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't start the exam right now.");
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

  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">CBT Center</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Full exam simulation
      </h1>
      <p className="mt-3 text-graphite">
        A single, timed sitting drawing questions across every subject — the closest thing on this
        platform to the real NMCN exam-day experience. No instant feedback while you work through
        it, same as the real thing; your full results appear only after you submit.
      </p>

      <div className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-ink-navy">Number of questions</span>
          <input
            type="number"
            min={10}
            max={300}
            value={questionCount}
            onChange={(e) => setQuestionCount(Number(e.target.value))}
            className="rounded-md border border-mist px-4 py-2 focus:border-vital-teal focus:outline-none"
          />
          <span className="text-xs text-graphite">
            If fewer questions exist in the bank than you request, you&apos;ll get however many are
            available.
          </span>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-ink-navy">Time limit (minutes)</span>
          <input
            type="number"
            min={30}
            max={300}
            value={durationMinutes}
            onChange={(e) => setDurationMinutes(Number(e.target.value))}
            className="rounded-md border border-mist px-4 py-2 focus:border-vital-teal focus:outline-none"
          />
          <span className="text-xs text-graphite">240 minutes (4 hours) matches a full exam sitting.</span>
        </label>
      </div>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      <button
        onClick={handleStart}
        disabled={starting}
        className="mt-8 rounded-md bg-vital-teal px-8 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
      >
        {starting ? "Starting…" : "Start full exam simulation"}
      </button>

      <div className="mt-8">
        <Link href="/dashboard" className="text-sm text-vital-teal hover:underline">
          ← Back to dashboard
        </Link>
      </div>
    </main>
  );
}
