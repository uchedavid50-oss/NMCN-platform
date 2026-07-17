"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import {
  api,
  ApiError,
  AttemptHistory,
  OverviewStats,
  StudyPlan,
  TopicPerformance,
} from "@/lib/api";

function formatDate(iso: string) {
  return new Date(iso.endsWith("Z") ? iso : `${iso}Z`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function AnalyticsPage() {
  const { user, token, loading } = useRequireAuth();
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [byTopic, setByTopic] = useState<TopicPerformance[] | null>(null);
  const [weakTopics, setWeakTopics] = useState<TopicPerformance[] | null>(null);
  const [history, setHistory] = useState<AttemptHistory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [studyPlan, setStudyPlan] = useState<StudyPlan | null>(null);
  const [studyPlanLoading, setStudyPlanLoading] = useState(false);
  const [studyPlanError, setStudyPlanError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !token) return;
    Promise.all([
      api.getOverview(token),
      api.getByTopic(token),
      api.getWeakTopics(token),
      api.getHistory(token, 10),
    ])
      .then(([o, bt, wt, h]) => {
        setOverview(o);
        setByTopic(bt);
        setWeakTopics(wt);
        setHistory(h);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load your progress."));
  }, [user, token]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  async function handleGetStudyPlan() {
    if (!token) return;
    setStudyPlanLoading(true);
    setStudyPlanError(null);
    try {
      const result = await api.getStudyPlan(token);
      setStudyPlan(result);
    } catch (err) {
      setStudyPlanError(err instanceof ApiError ? err.message : "Couldn't generate a study plan right now.");
    } finally {
      setStudyPlanLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Your progress</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        How exam-ready are you?
      </h1>

      {error && <p className="mt-6 text-pulse-coral">{error}</p>}

      {overview && (
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Overall accuracy" value={`${overview.overall_accuracy_percentage}%`} />
          <StatCard label="Questions answered" value={String(overview.total_questions_answered)} />
          <StatCard label="Practice sessions" value={String(overview.practice_attempts)} />
          <StatCard label="Mock exams" value={String(overview.mock_attempts)} />
        </div>
      )}

      <section className="mt-10">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl font-semibold text-ink-navy">Your study plan</h2>
          {!studyPlan && (
            <button
              onClick={handleGetStudyPlan}
              disabled={studyPlanLoading}
              className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
            >
              {studyPlanLoading ? "Generating…" : "Get my study plan"}
            </button>
          )}
        </div>

        {studyPlanError && <p className="mt-3 text-sm text-pulse-coral">{studyPlanError}</p>}

        {studyPlan && (
          <div className="mt-4 rounded-md border border-mist bg-white p-5">
            {studyPlan.has_weak_topics && (
              <p className="mb-3 font-mono text-xs uppercase tracking-widest text-vital-teal">
                Based on: {studyPlan.weak_topic_names.join(", ")}
              </p>
            )}
            <p className="whitespace-pre-line text-graphite">{studyPlan.plan}</p>
            <button
              onClick={handleGetStudyPlan}
              disabled={studyPlanLoading}
              className="mt-4 text-sm text-vital-teal hover:underline disabled:opacity-50"
            >
              {studyPlanLoading ? "Regenerating…" : "Regenerate"}
            </button>
          </div>
        )}
      </section>

      {weakTopics && weakTopics.length > 0 && (
        <section className="mt-10">
          <h2 className="font-display text-xl font-semibold text-ink-navy">Needs work</h2>
          <p className="mt-1 text-sm text-graphite">
            Topics where you've answered enough questions to see a real pattern, and it&apos;s below 60%.
          </p>
          <div className="mt-4 flex flex-col gap-3">
            {weakTopics.map((topic) => (
              <div
                key={topic.topic_id}
                className="rounded-md border border-pulse-coral/40 bg-pulse-coral/5 px-5 py-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-mono text-xs uppercase tracking-widest text-graphite">
                      {topic.subject_name}
                    </p>
                    <p className="font-body font-medium text-ink-navy">{topic.topic_name}</p>
                  </div>
                  <p className="font-mono text-2xl text-pulse-coral">
                    {topic.accuracy_percentage}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {byTopic && byTopic.length > 0 && (
        <section className="mt-10">
          <h2 className="font-display text-xl font-semibold text-ink-navy">By topic</h2>
          <div className="mt-4 flex flex-col gap-4">
            {byTopic.map((topic) => (
              <div key={topic.topic_id}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-body text-ink-navy">{topic.topic_name}</span>
                  <span className="font-mono text-graphite">
                    {topic.correct_answered}/{topic.total_answered} · {topic.accuracy_percentage}%
                  </span>
                </div>
                <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-mist">
                  <div
                    className={`h-full rounded-full ${
                      topic.accuracy_percentage < 60 ? "bg-pulse-coral" : "bg-vital-teal"
                    }`}
                    style={{ width: `${Math.max(4, topic.accuracy_percentage)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {byTopic && byTopic.length === 0 && (
        <p className="mt-10 text-graphite">
          No practice or mock exam data yet —{" "}
          <Link href="/subjects" className="text-vital-teal hover:underline">
            start practicing
          </Link>{" "}
          to see your progress here.
        </p>
      )}

      {history && history.items.length > 0 && (
        <section className="mt-10">
          <h2 className="font-display text-xl font-semibold text-ink-navy">Recent activity</h2>
          <div className="mt-4 flex flex-col gap-2">
            {history.items.map((item) => (
              <div
                key={item.attempt_id}
                className="flex items-center justify-between rounded-md border border-mist px-4 py-3 text-sm"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded px-2 py-0.5 font-mono text-xs uppercase ${
                      item.mode === "mock"
                        ? "bg-ink-navy text-chart-cream"
                        : "bg-mist text-graphite"
                    }`}
                  >
                    {item.mode}
                  </span>
                  <span className="text-ink-navy">{item.topic_name}</span>
                </div>
                <div className="flex items-center gap-3 font-mono text-graphite">
                  <span>
                    {item.score_percentage !== null ? `${item.score_percentage}%` : "incomplete"}
                  </span>
                  <span>{formatDate(item.started_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <Link href="/subjects" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to subjects
      </Link>
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-mist p-4">
      <p className="text-xs text-graphite">{label}</p>
      <p className="mt-1 font-mono text-2xl text-ink-navy">{value}</p>
    </div>
  );
}
