"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, SpeedRoundQuestion } from "@/lib/api";

type Phase = "intro" | "loading" | "playing" | "summary" | "error";

const SECONDS_PER_QUESTION = 8;
const QUESTIONS_PER_ROUND = 10;

export default function SpeedRoundPage() {
  const { user, token, loading } = useRequireAuth();
  const [phase, setPhase] = useState<Phase>("intro");
  const [streak, setStreak] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [questions, setQuestions] = useState<SpeedRoundQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [timeLeft, setTimeLeft] = useState(SECONDS_PER_QUESTION);
  const [finalResult, setFinalResult] = useState<{ score: number; streak: number } | null>(null);
  const advancingRef = useRef(false);

  useEffect(() => {
    if (!user || !token) return;
    api.getStreak(token).then((s) => setStreak(s.current_streak)).catch(() => setStreak(0));
  }, [user, token]);

  async function handleStart() {
    if (!token) return;
    setPhase("loading");
    setErrorMsg(null);
    try {
      const qs = await api.startSpeedRound(token, undefined, QUESTIONS_PER_ROUND);
      setQuestions(qs);
      setCurrentIndex(0);
      setCorrectCount(0);
      setSelectedOptionId(null);
      setShowResult(false);
      setTimeLeft(SECONDS_PER_QUESTION);
      advancingRef.current = false;
      setPhase("playing");
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : "Couldn't start a speed round right now.");
      setPhase("error");
    }
  }

  const goToNext = useCallback(() => {
    if (advancingRef.current) return;
    advancingRef.current = true;
    setTimeout(() => {
      setCurrentIndex((i) => i + 1);
      setSelectedOptionId(null);
      setShowResult(false);
      setTimeLeft(SECONDS_PER_QUESTION);
      advancingRef.current = false;
    }, 900);
  }, []);

  function handleSelect(optionId: string, isCorrect: boolean) {
    if (showResult) return;
    setSelectedOptionId(optionId);
    setShowResult(true);
    if (isCorrect) setCorrectCount((c) => c + 1);
    goToNext();
  }

  // Per-question countdown
  useEffect(() => {
    if (phase !== "playing" || showResult) return;
    if (timeLeft <= 0) {
      setShowResult(true);
      goToNext();
      return;
    }
    const t = setTimeout(() => setTimeLeft((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [phase, timeLeft, showResult, goToNext]);

  // Round completion
  useEffect(() => {
    if (phase !== "playing") return;
    if (currentIndex >= questions.length && questions.length > 0) {
      (async () => {
        if (!token) return;
        try {
          const result = await api.submitSpeedRound(questions.length, correctCount, token);
          setFinalResult({ score: result.score_percentage, streak: result.current_streak });
          setStreak(result.current_streak);
          setPhase("summary");
        } catch {
          setErrorMsg("Couldn't save your result, but here's how you did.");
          setFinalResult({ score: Math.round((correctCount / questions.length) * 100), streak: streak ?? 0 });
          setPhase("summary");
        }
      })();
    }
  }, [currentIndex, questions.length, phase, token, correctCount, streak]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  if (phase === "intro" || phase === "loading") {
    return (
      <main className="mx-auto max-w-xl px-6 py-16 text-center">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Speed round</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
          {SECONDS_PER_QUESTION} seconds a question. How many can you get right?
        </h1>

        {streak !== null && streak > 0 && (
          <p className="mt-4 font-mono text-lg text-pulse-coral">🔥 {streak}-day streak</p>
        )}

        <button
          onClick={handleStart}
          disabled={phase === "loading"}
          className="mt-8 rounded-md bg-vital-teal px-8 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {phase === "loading" ? "Loading…" : "Start speed round"}
        </button>

        <div className="mt-8">
          <Link href="/dashboard" className="text-sm text-vital-teal hover:underline">
            ← Back to dashboard
          </Link>
        </div>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="mx-auto max-w-xl px-6 py-16 text-center">
        <p className="text-pulse-coral">{errorMsg}</p>
        <Link href="/dashboard" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to dashboard
        </Link>
      </main>
    );
  }

  if (phase === "summary" && finalResult) {
    return (
      <main className="mx-auto max-w-xl px-6 py-16 text-center">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Round complete</p>
        <p className="mt-4 font-display text-6xl font-semibold text-ink-navy">{finalResult.score}%</p>
        <p className="mt-2 text-graphite">
          {correctCount} of {questions.length} correct
        </p>
        <p className="mt-4 font-mono text-lg text-pulse-coral">🔥 {finalResult.streak}-day streak</p>

        <div className="mt-8 flex justify-center gap-3">
          <button
            onClick={handleStart}
            className="rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
          >
            Play again
          </button>
          <Link
            href="/dashboard"
            className="rounded-md border border-mist px-6 py-3 font-medium text-ink-navy transition hover:border-vital-teal"
          >
            Back to dashboard
          </Link>
        </div>
      </main>
    );
  }

  const question = questions[currentIndex];
  if (!question) return null;

  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <div className="flex items-center justify-between">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
          {currentIndex + 1} / {questions.length}
        </p>
        <p className={`font-mono text-2xl ${timeLeft <= 3 ? "text-pulse-coral" : "text-ink-navy"}`}>
          {timeLeft}
        </p>
      </div>

      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-mist">
        <div
          className="h-full rounded-full bg-vital-teal transition-all duration-1000 ease-linear"
          style={{ width: `${(timeLeft / SECONDS_PER_QUESTION) * 100}%` }}
        />
      </div>

      <h1 className="mt-6 font-display text-2xl font-semibold text-ink-navy">{question.stem}</h1>

      <div className="mt-6 flex flex-col gap-3">
        {question.options.map((option) => {
          let stateClasses = "border-mist hover:border-vital-teal";
          if (showResult) {
            if (option.is_correct) stateClasses = "border-vital-teal bg-vital-teal/10";
            else if (option.id === selectedOptionId) stateClasses = "border-pulse-coral bg-pulse-coral/10";
            else stateClasses = "border-mist opacity-50";
          }
          return (
            <button
              key={option.id}
              onClick={() => handleSelect(option.id, option.is_correct)}
              disabled={showResult}
              className={`rounded-md border px-5 py-3 text-left font-body text-ink-navy transition ${stateClasses}`}
            >
              {option.text}
            </button>
          );
        })}
      </div>
    </main>
  );
}
