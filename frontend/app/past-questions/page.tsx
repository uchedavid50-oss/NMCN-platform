"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ApiError } from "@/lib/api";
import {
  getPastQuestionsCount,
  startPastQuestionsPractice,
  completePastQuestionsPractice,
  PastQuestion,
} from "@/lib/api-extras-6";

type Phase = "intro" | "loading" | "playing" | "summary" | "error";

export default function PastQuestionsPage() {
  const { user, token, loading } = useRequireAuth();
  const [phase, setPhase] = useState<Phase>("intro");
  const [availableCount, setAvailableCount] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [questions, setQuestions] = useState<PastQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [finalResult, setFinalResult] = useState<{ score: number; streak: number } | null>(null);

  useEffect(() => {
    getPastQuestionsCount().then((r) => setAvailableCount(r.count)).catch(() => setAvailableCount(0));
  }, []);

  async function handleStart() {
    if (!token) return;
    setPhase("loading");
    setErrorMsg(null);
    try {
      const result = await startPastQuestionsPractice(availableCount || 20, token);
      setQuestions(result);
      setCurrentIndex(0);
      setCorrectCount(0);
      setSelectedOptionId(null);
      setPhase("playing");
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : "Couldn't load past questions.");
      setPhase("error");
    }
  }

  function handleSelect(optionId: string, isCorrect: boolean) {
    if (selectedOptionId) return;
    setSelectedOptionId(optionId);
    const newCorrect = isCorrect ? correctCount + 1 : correctCount;
    if (isCorrect) setCorrectCount(newCorrect);

    const isLast = currentIndex === questions.length - 1;
    setTimeout(async () => {
      if (isLast) {
        if (!token) return;
        try {
          const result = await completePastQuestionsPractice(questions.length, newCorrect, token);
          setFinalResult({ score: result.score_percentage, streak: result.current_streak });
        } catch {
          setFinalResult({ score: Math.round((newCorrect / questions.length) * 100), streak: 0 });
        }
        setPhase("summary");
      } else {
        setCurrentIndex((i) => i + 1);
        setSelectedOptionId(null);
      }
    }, 5000);
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  if (phase === "intro" || phase === "loading") {
    return (
      <main className="relative mx-auto flex min-h-screen max-w-xl flex-col justify-center overflow-hidden px-6 text-center">
        <div className="ambient-glow" />
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
          Past Questions
        </p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
          NMCN Past Questions
        </h1>
        <p className="mt-3 text-left text-graphite">
          Nursing is a noble profession that requires extensive knowledge, critical thinking
          skills, empathy, and the ability to provide safe and effective care to patients. In
          order to become a licensed nurse, individuals must pass a rigorous examination that
          tests their understanding of various nursing concepts. Past questions and answers play
          a vital role in preparing aspiring nurses for these examinations. They serve as a
          valuable study resource, allowing candidates to familiarize themselves with the format
          and types of questions that may be asked. General nursing past questions and answers
          cover a wide range of topics, including anatomy and physiology, pharmacology, nursing
          ethics and laws, patient care and assessment, medical surgical nursing, research
          methodology, health economics, maternal and child health, principles of management
          reproduction system, foundation of nursing, and community health nursing. These
          questions often require candidates to apply their knowledge to real-life scenarios,
          demonstrating their understanding of key nursing principles and their ability to make
          sound decisions in different clinical situations.
        </p>
        <div className="mt-6 rounded-md border border-mist bg-card-bg p-5 text-left">
          <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
            Before you begin
          </p>
          <ul className="mt-3 flex flex-col gap-2 text-sm text-graphite">
            <li>• Each question has one correct answer out of the options shown.</li>
            <li>• Once you select an answer, you cannot change it — just like the real exam.</li>
            <li>• You'll see the correct answer and a brief rationale after each question.</li>
            <li>• Your score and streak are recorded when you finish the session.</li>
          </ul>
        </div>

        {availableCount !== null && (
          <p className="mt-4 font-mono text-sm text-graphite">
            {availableCount} question{availableCount === 1 ? "" : "s"} available right now
          </p>
        )}

        <button
          onClick={handleStart}
          disabled={phase === "loading" || availableCount === 0}
          className="mt-8 rounded-md bg-vital-teal px-8 py-3 font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg disabled:opacity-50"
        >
          {phase === "loading" ? "Loading…" : "Begin exam"}
        </button>

        <button
          onClick={handleStart}
          disabled={phase === "loading" || availableCount === 0}
          className="mt-8 rounded-md bg-vital-teal px-8 py-3 font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg disabled:opacity-50"
        >
          {phase === "loading" ? "Loading…" : "Start practicing"}
        </button>
        {availableCount === 0 && (
          <p className="mt-3 text-sm text-graphite">
            Nothing available yet — check back once your admin has approved some.
          </p>
        )}

        <Link href="/dashboard" className="mt-8 text-sm text-vital-teal hover:underline">
          ← Back to dashboard
        </Link>
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
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Session complete</p>
        <p className="mt-4 font-display text-6xl font-semibold text-ink-navy">{finalResult.score}%</p>
        <p className="mt-2 text-graphite">
          {correctCount} of {questions.length} correct
        </p>
        {finalResult.streak > 0 && (
          <p className="mt-4 font-mono text-lg text-pulse-coral">🔥 {finalResult.streak}-day streak</p>
        )}
        <div className="mt-8 flex justify-center gap-3">
          <button
            onClick={handleStart}
            className="rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
          >
            Practice again
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
    <main className="mx-auto max-w-2xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
        Question {currentIndex + 1} of {questions.length}
      </p>
      <h1 className="mt-4 font-display text-2xl font-semibold text-ink-navy">{question.stem}</h1>
      <div className="mt-6 flex flex-col gap-3">
        {question.options.map((option) => {
          let stateClasses = "border-mist hover:border-vital-teal";
          if (selectedOptionId) {
            if (option.is_correct) stateClasses = "border-vital-teal bg-vital-teal/10";
            else if (option.id === selectedOptionId) stateClasses = "border-pulse-coral bg-pulse-coral/10";
            else stateClasses = "border-mist opacity-50";
          }
          return (
            <button
              key={option.id}
              onClick={() => handleSelect(option.id, option.is_correct)}
              disabled={!!selectedOptionId}
              className={`rounded-md border px-5 py-3 text-left font-body text-ink-navy transition ${stateClasses}`}
            >
              {option.text}
            </button>
          );
        })}
      </div>

      {selectedOptionId && (
        <div className="animate-fade-in-up mt-6 rounded-md border border-mist bg-card-bg p-5">
          <p
            className={`font-display text-lg font-semibold ${
              question.options.find((o) => o.id === selectedOptionId)?.is_correct
                ? "text-vital-teal"
                : "text-pulse-coral"
            }`}
          >
            {question.options.find((o) => o.id === selectedOptionId)?.is_correct
              ? "Correct!"
              : "wrong"}
          </p>
          <p className="mt-2 text-sm text-graphite">{question.explanation}</p>
        </div>
      )}
    </main>
  );
}