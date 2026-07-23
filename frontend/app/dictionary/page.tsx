"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ApiError } from "@/lib/api";
import { searchDictionary, listDictionary, verifyDictionaryEntry, DictionaryEntry } from "@/lib/api-extras-2";

export default function DictionaryPage() {
  const { user, token, loading } = useRequireAuth();
  const [query, setQuery] = useState("");
  const [entries, setEntries] = useState<DictionaryEntry[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function refreshList(q: string) {
    if (!token) return;
    listDictionary(q, token).then(setEntries).catch(() => {});
  }

  useEffect(() => {
    if (!user || !token) return;
    refreshList("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, token]);

  async function handleSearch() {
    if (!token || !query.trim()) return;
    setSearching(true);
    setError(null);
    try {
      await searchDictionary(query, token);
      refreshList(query);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't look this term up right now.");
    } finally {
      setSearching(false);
    }
  }

  async function handleVerify(id: string) {
    if (!token) return;
    try {
      await verifyDictionaryEntry(id, null, token);
      refreshList(query);
    } catch {
      setError("Couldn't verify this entry.");
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
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Nursing Dictionary</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Quick term lookups
      </h1>
      <p className="mt-3 text-graphite">
        Shared across every student — the first lookup generates it, every lookup after that is
        instant. Entries not yet reviewed by an admin are marked unverified.
      </p>

      <div className="mt-6 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="e.g. tachycardia, homeostasis…"
          disabled={searching}
          className="flex-1 rounded-md border border-mist px-4 py-2.5 focus:border-vital-teal focus:outline-none"
        />
        <button
          onClick={handleSearch}
          disabled={searching || !query.trim()}
          className="rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {searching ? "Looking up…" : "Search"}
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-pulse-coral">{error}</p>}

      <div className="mt-8 flex flex-col gap-3">
        {entries.map((e) => (
          <div key={e.id} className="rounded-md border border-mist bg-card-bg p-5">
            <div className="flex items-center justify-between">
              <p className="font-mono text-sm font-semibold text-vital-teal">{e.term}</p>
              {e.is_verified ? (
                <span className="text-xs text-vital-teal">✓ Verified</span>
              ) : (
                <span className="text-xs text-graphite">Unverified</span>
              )}
            </div>
            <p className="mt-2 text-ink-navy">{e.definition}</p>
            {user.role === "admin" && !e.is_verified && (
              <button
                onClick={() => handleVerify(e.id)}
                className="mt-3 rounded-md border border-vital-teal px-3 py-1 text-xs font-medium text-vital-teal hover:bg-vital-teal/10"
              >
                Mark as verified
              </button>
            )}
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-graphite">No entries yet — search for a term above.</p>
        )}
      </div>

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
