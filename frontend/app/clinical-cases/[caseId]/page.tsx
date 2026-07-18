"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, ClinicalCase } from "@/lib/api";

export default function ClinicalCaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { user, token, loading } = useRequireAuth();
  const [clinicalCase, setClinicalCase] = useState<ClinicalCase | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [finalResult, setFinalResult] = useState<{ score: number; streak: number } | null>(null);

  useEffect(() => {
    if (!user || !token) return;
    api
      .getClinicalCase(caseId, token)
      .then(setClinicalCase)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load this case."));
  }, [user, token, caseId]);

  async function handleFinish(finalCorrectCount: number) {
    if (!token || !clinicalCase) return;
    try {
      const result = await api.completeClinicalCase(
        caseId,
        clinicalCase.decision_points.length,
        finalCorrectCount,
        token
      );
      setFinalResult({ score: result.score_percentage, streak: result.current_streak });
    } catch {
      setFinalResult({
        score: Math.round((finalCorrectCount / clinicalCase.decision_points.length) * 100),
        streak: 0,
      });
    }
    setCompleted(true);
  }

  function handleSelect(optionId: string, isCorrect: boolean) {
    if (selectedOptionId) return; // already answered this decision point
    setSelectedOptionId(optionId);
    const newCorrectCount = isCorrect ? correctCount + 1 : correctCount;
    if (isCorrect) setCorrectCount(newCorrectCount);

    const isLast = clinicalCase && currentIndex === clinicalCase.decision_points.length - 1;
    if (isLast) {
      // Small delay so the student sees the feedback before the summary appears.
      setTimeout(() => handleFinish(newCorrectCount), 1200);
    }
  }

  function handleNext() {
    setCurrentIndex((i) => i + 1);
    setSelectedOptionId(null);
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto max-w-xl px-6 py-16 text-center">
        <p className="text-pulse-coral">{error}</p>
        <Link href="/clinical-cases" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to Clinical Cases
        </Link>
      </main>
    );
  }

  if (!clinicalCase) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading case…</p>
      </main>
    );
  }

  if (completed && finalResult) {
    return (
      <main className="mx-auto max-w-xl px-6 py-16 text-center">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Case complete</p>
        <p className="mt-4 font-display text-6xl font-semibold text-ink-navy">
          {finalResult.score}%
        </p>
        <p className="mt-2 text-graphite">
          {correctCount} of {clinicalCase.decision_points.length} clinical decisions correct
        </p>
        {finalResult.streak > 0 && (
          <p className="mt-4 font-mono text-lg text-pulse-coral">🔥 {finalResult.streak}-day streak</p>
        )}
        <div className="mt-8 flex justify-center gap-3">
          <Link
            href="/clinical-cases"
            className="rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
          >
            New case
          </Link>
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

  const decisionPoint = clinicalCase.decision_points[currentIndex];
  const isLast = currentIndex === clinicalCase.decision_points.length - 1;

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
        Decision {currentIndex + 1} of {clinicalCase.decision_points.length}
      </p>

      {currentIndex === 0 && (
        <div className="mt-3 rounded-md border border-mist bg-card-bg p-4">
          <p className="font-mono text-xs uppercase tracking-widest text-graphite">Scenario</p>
          <p className="mt-1 text-ink-navy">{clinicalCase.scenario}</p>
        </div>
      )}

      <h1 className="mt-6 font-display text-2xl font-semibold text-ink-navy">
        {decisionPoint.question}
      </h1>

      <div className="mt-6 flex flex-col gap-3">
        {decisionPoint.options.map((option) => {
          let stateClasses = "border-mist hover:border-vital-teal";
          if (selectedOptionId) {
            if (option.is_correct) stateClasses = "border-vital-teal bg-vital-teal/10";
            else if (option.id === selectedOptionId) stateClasses = "border-pulse-coral bg-pulse-coral/10";
            else stateClasses = "border-mist opacity-50";
          }
          return (
            <div key={option.id}>
              <button
                onClick={() => handleSelect(option.id, option.is_correct)}
                disabled={!!selectedOptionId}
                className={`w-full rounded-md border px-5 py-3 text-left font-body text-ink-navy transition ${stateClasses}`}
              >
                {option.text}
              </button>
              {selectedOptionId && (option.id === selectedOptionId || option.is_correct) && (
                <p className="mt-1 px-2 text-sm text-graphite">{option.rationale}</p>
              )}
            </div>
          );
        })}
      </div>

      {selectedOptionId && !isLast && (
        <button
          onClick={handleNext}
          className="mt-6 rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy"
        >
          Next decision
        </button>
      )}
      {selectedOptionId && isLast && (
        <p className="mt-6 font-mono text-sm text-graphite">Wrapping up your results…</p>
      )}
    </main>
  );
}
