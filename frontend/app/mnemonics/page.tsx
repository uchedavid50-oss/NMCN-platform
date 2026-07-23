"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ApiError } from "@/lib/api";
import { listMnemonics, generateMnemonic, Mnemonic } from "@/lib/api-extras";

export default function MnemonicsPage() {
  const { user, token, loading } = useRequireAuth();
  const [term, setTerm] = useState("");
  const [mnemonics, setMnemonics] = useState<Mnemonic[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !token) return;
    listMnemonics(token).then(setMnemonics).catch(() => {});
  }, [user, token]);

  async function handleGenerate() {
    if (!token || !term.trim()) return;
    setGenerating(true);
    setError(null);
    try {
      const result = await generateMnemonic(term, token);
      setMnemonics((prev) => [result, ...prev]);
      setTerm("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't generate a mnemonic right now.");
    } finally {
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
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Mnemonic Generator</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Short forms to remember key terms
      </h1>
      <p className="mt-3 text-graphite">
        Type a term, list, or sequence you need to memorize — get a quick mnemonic to help it stick.
      </p>

      <div className="mt-6 flex gap-2">
        <input
          type="text"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
          placeholder="e.g. cranial nerves, stages of mitosis…"
          disabled={generating}
          className="flex-1 rounded-md border border-mist px-4 py-2.5 focus:border-vital-teal focus:outline-none"
        />
        <button
          onClick={handleGenerate}
          disabled={generating || !term.trim()}
          className="rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {generating ? "Generating…" : "Generate"}
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-pulse-coral">{error}</p>}

      <div className="mt-8 flex flex-col gap-4">
        {mnemonics.map((m) => (
          <div key={m.id} className="rounded-md border border-mist bg-card-bg p-5">
            <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">{m.term}</p>
            <p className="mt-2 whitespace-pre-line text-ink-navy">{m.mnemonic_text}</p>
          </div>
        ))}
        {mnemonics.length === 0 && (
          <p className="text-graphite">No mnemonics yet — try generating one above.</p>
        )}
      </div>

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
