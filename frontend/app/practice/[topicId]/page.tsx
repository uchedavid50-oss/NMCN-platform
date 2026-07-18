"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, AnswerResponse, ApiError, AttemptSummary, PracticeQuestion } from "@/lib/api";

type Phase = "loading" | "quiz" | "summary" | "error";

export default function PracticePage() {
  const { topicId } = useParams<{ topicId: string }>();
  const { user, token, loading } = useRequireAuth();

  const [phase, setPhase] = useState<Phase>("loading");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<PracticeQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [feedback, setFeedback] = useState<AnswerResponse | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [summary, setSummary] = useState<AttemptSummary | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [tutorMessage, setTutorMessage] = useState("");
  const [tutorReplies, setTutorReplies] = useState<{ question: string; reply: string }[]>([]);
  const [tutorAsking, setTutorAsking] = useState(false);
  const [tutorError, setTutorError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !token) return;
    api
      .startPractice(topicId, token)
      .then((res) => {
        if (res.questions.length === 0) {
          setErrorMsg("This topic doesn't have any questions yet.");
          setPhase("error");
          return;
        }
        setAttemptId(res.attempt_id);
        setQuestions(res.questions);
        setPhase("quiz");
      })
      .catch((err) => {
        setErrorMsg(err.message || "Couldn't start this practice session.");
        setPhase("error");
      });
  }, [user, token, topicId]);

  if (loading || !user || phase === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-pulse-coral">{errorMsg}</p>
        <Link href="/subjects" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to subjects
        </Link>
      </main>
    );
  }

  if (phase === "summary" && summary) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16 text-center">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
          Practice complete
        </p>
        <p className="mt-4 font-display text-6xl font-semibold text-ink-navy">
          {summary.score_percentage}%
        </p>
        <p className="mt-2 text-graphite">
          {summary.correct_answers} of {summary.total_questions} correct
        </p>
        <Link
          href="/subjects"
          className="mt-8 inline-block rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
        >
          Back to subjects
        </Link>
      </main>
    );
  }

  const question = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;

  async function handleSelectOption(optionId: string) {
    if (feedback || submitting || !attemptId || !token) return;
    setSelectedOptionId(optionId);
    setSubmitting(true);
    try {
      const result = await api.submitPracticeAnswer(attemptId, question.id, optionId, token);
      setFeedback(result);
      if (result.is_correct) setCorrectCount((c) => c + 1);
    } catch (err: any) {
      setErrorMsg(err.message || "Couldn't submit that answer.");
      setPhase("error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleNext() {
    if (!attemptId || !token) return;
    if (isLastQuestion) {
      setSubmitting(true);
      try {
        const result = await api.finishPractice(attemptId, token);
        setSummary(result);
        setPhase("summary");
      } catch (err: any) {
        setErrorMsg(err.message || "Couldn't finish this practice session.");
        setPhase("error");
      } finally {
        setSubmitting(false);
      }
      return;
    }
    setCurrentIndex((i) => i + 1);
    setFeedback(null);
    setSelectedOptionId(null);
    setTutorReplies([]);
    setTutorMessage("");
    setTutorError(null);
  }

  async function handleAskTutor() {
    if (!token || !tutorMessage.trim()) return;
    setTutorAsking(true);
    setTutorError(null);
    try {
      const result = await api.askTutor(question.id, tutorMessage, token);
      setTutorReplies((prev) => [...prev, { question: tutorMessage, reply: result.reply }]);
      setTutorMessage("");
    } catch (err) {
      setTutorError(err instanceof ApiError ? err.message : "The tutor couldn't respond just now.");
    } finally {
      setTutorAsking(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <div className="flex items-center justify-between">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
          Question {currentIndex + 1} of {questions.length}
        </p>
        <p className="font-mono text-sm text-graphite">
          {correctCount} correct so far
        </p>
      </div>

      <h1 className="mt-4 font-display text-2xl font-semibold text-ink-navy">{question.stem}</h1>

      <div className="mt-6 flex flex-col gap-3">
        {question.options.map((option) => {
          const isSelected = option.id === selectedOptionId;
          const isCorrectOption = feedback && option.id === feedback.correct_option_id;
          const isWrongSelected = feedback && isSelected && !feedback.is_correct;

          let stateClasses = "border-mist hover:border-vital-teal hover:bg-card-bg";
          if (feedback) {
            if (isCorrectOption) {
              stateClasses = "border-vital-teal bg-vital-teal/10";
            } else if (isWrongSelected) {
              stateClasses = "border-pulse-coral bg-pulse-coral/10";
            } else {
              stateClasses = "border-mist opacity-60";
            }
          }

          return (
            <button
              key={option.id}
              onClick={() => handleSelectOption(option.id)}
              disabled={!!feedback || submitting}
              className={`rounded-md border px-5 py-4 text-left font-body text-lg text-ink-navy transition ${stateClasses}`}
            >
              {option.text}
            </button>
          );
        })}
      </div>

      {feedback && (
        <div className="mt-6 rounded-md border border-mist bg-card-bg p-5">
          <p
            className={`font-mono text-sm font-medium uppercase tracking-widest ${
              feedback.is_correct ? "text-vital-teal" : "text-pulse-coral"
            }`}
          >
            {feedback.is_correct ? "Correct" : "Not quite"}
          </p>
          <p className="mt-2 text-graphite">{feedback.explanation}</p>

          <div className="mt-5 border-t border-mist pt-4">
            <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
              Still unsure? Ask the tutor
            </p>

            {tutorReplies.map((exchange, i) => (
              <div key={i} className="mt-3">
                <p className="text-sm font-medium text-ink-navy">{exchange.question}</p>
                <p className="mt-1 text-sm text-graphite">{exchange.reply}</p>
              </div>
            ))}

            {tutorError && <p className="mt-3 text-sm text-pulse-coral">{tutorError}</p>}

            <div className="mt-3 flex gap-2">
              <input
                type="text"
                value={tutorMessage}
                onChange={(e) => setTutorMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAskTutor()}
                placeholder="Ask a follow-up question…"
                disabled={tutorAsking}
                className="flex-1 rounded-md border border-mist px-3 py-2 text-sm focus:border-vital-teal focus:outline-none"
              />
              <button
                onClick={handleAskTutor}
                disabled={tutorAsking || !tutorMessage.trim()}
                className="rounded-md border border-mist px-4 py-2 text-sm font-medium text-ink-navy transition hover:border-vital-teal disabled:opacity-50"
              >
                {tutorAsking ? "Asking…" : "Ask"}
              </button>
            </div>
          </div>

          <button
            onClick={handleNext}
            disabled={submitting}
            className="mt-4 rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
          >
            {submitting ? "Please wait…" : isLastQuestion ? "Finish" : "Next question"}
          </button>
        </div>
      )}
    </main>
  );
}
