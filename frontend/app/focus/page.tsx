"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { completeFocusSession } from "@/lib/api-extras";
import { PulseTrace } from "@/components/PulseTrace";

const DURATION_OPTIONS = [15, 25, 45, 60];

export default function FocusPage() {
  const { user, token, loading } = useRequireAuth();
  const [durationMinutes, setDurationMinutes] = useState(25);
  const [secondsLeft, setSecondsLeft] = useState(25 * 60);
  const [running, setRunning] = useState(false);
  const [completedResult, setCompletedResult] = useState<{
    total_sessions: number;
    total_minutes: number;
    current_streak: number;
  } | null>(null);
  const completedRef = useRef(false);

  useEffect(() => {
    if (!running) return;
    if (secondsLeft <= 0) {
      if (!completedRef.current) {
        completedRef.current = true;
        setRunning(false);
        if (token) {
          completeFocusSession(durationMinutes, token).then(setCompletedResult);
        }
      }
      return;
    }
    const t = setTimeout(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [running, secondsLeft, token, durationMinutes]);

  function handleStart() {
    completedRef.current = false;
    setCompletedResult(null);
    setSecondsLeft(durationMinutes * 60);
    setRunning(true);
  }

  function handleStop() {
    setRunning(false);
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;

  return (
    <main className="mx-auto max-w-xl px-6 py-16 text-center">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Focus Session</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Steady focus, steady progress
      </h1>

      <PulseTrace className={`mx-auto my-8 h-16 w-full max-w-sm ${running ? "" : "opacity-40"}`} />

      <p className="font-mono text-6xl text-ink-navy">
        {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
      </p>

      {!running && !completedResult && (
        <>
          <div className="mt-6 flex justify-center gap-2">
            {DURATION_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => {
                  setDurationMinutes(d);
                  setSecondsLeft(d * 60);
                }}
                className={`rounded-md border px-4 py-2 text-sm font-medium transition ${
                  d === durationMinutes
                    ? "border-vital-teal bg-vital-teal/10 text-vital-teal"
                    : "border-mist text-ink-navy hover:border-vital-teal"
                }`}
              >
                {d} min
              </button>
            ))}
          </div>
          <button
            onClick={handleStart}
            className="mt-6 rounded-md bg-vital-teal px-8 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
          >
            Start focus session
          </button>
        </>
      )}

      {running && (
        <button
          onClick={handleStop}
          className="mt-6 rounded-md border border-pulse-coral px-8 py-3 font-medium text-pulse-coral transition hover:bg-pulse-coral/10"
        >
          Stop early
        </button>
      )}

      {completedResult && (
        <div className="mt-6 rounded-md border border-vital-teal bg-vital-teal/10 p-5">
          <p className="text-vital-teal">Nice work — session complete.</p>
          <p className="mt-2 font-mono text-sm text-graphite">
            {completedResult.total_sessions} sessions · {completedResult.total_minutes} total minutes
          </p>
          {completedResult.current_streak > 0 && (
            <p className="mt-1 font-mono text-lg text-pulse-coral">
              🔥 {completedResult.current_streak}-day streak
            </p>
          )}
          <button
            onClick={handleStart}
            className="mt-4 rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy"
          >
            Start another
          </button>
        </div>
      )}

      <div className="mt-10">
        <Link href="/dashboard" className="text-sm text-vital-teal hover:underline">
          ← Back to dashboard
        </Link>
      </div>
    </main>
  );
}
