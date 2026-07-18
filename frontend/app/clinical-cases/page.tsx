"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, ClinicalCaseSummary } from "@/lib/api";

export default function ClinicalCasesPage() {
  const { user, token, loading } = useRequireAuth();
  const router = useRouter();
  const [cases, setCases] = useState<ClinicalCaseSummary[] | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !token) return;
    api.listClinicalCases(token).then(setCases).catch(() => setCases([]));
  }, [user, token]);

  async function handleGenerate() {
    if (!token) return;
    setGenerating(true);
    setError(null);
    try {
      const newCase = await api.generateClinicalCase(token);
      router.push(`/clinical-cases/${newCase.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't generate a case right now.");
      setGenerating(false);
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
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
        Clinical Case Simulator
      </p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Build clinical judgment, not just recall
      </h1>
      <p className="mt-3 text-graphite">
        Work through a realistic patient scenario step by step — assessment, prioritization,
        intervention — with instant feedback and reasoning at every decision, not just a final
        score.
      </p>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      <button
        onClick={handleGenerate}
        disabled={generating}
        className="mt-6 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
      >
        {generating ? "Generating case…" : "Start a new case"}
      </button>

      <h2 className="mt-10 font-display text-xl font-semibold text-ink-navy">Past cases</h2>
      <div className="mt-4 flex flex-col gap-2">
        {cases?.map((c) => (
          <Link
            key={c.id}
            href={`/clinical-cases/${c.id}`}
            className="flex items-center justify-between rounded-md border border-mist px-4 py-3 transition hover:border-vital-teal"
          >
            <span className="text-ink-navy">{c.subject_context ?? "General nursing"}</span>
            <span className="font-mono text-xs text-graphite">
              {new Date(c.created_at.endsWith("Z") ? c.created_at : `${c.created_at}Z`).toLocaleDateString()}
            </span>
          </Link>
        ))}
        {cases && cases.length === 0 && (
          <p className="text-graphite">No cases yet — start one above.</p>
        )}
      </div>

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
