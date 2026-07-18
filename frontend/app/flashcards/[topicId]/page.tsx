"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, Flashcard } from "@/lib/api";

export default function FlashcardsPage() {
  const { topicId } = useParams<{ topicId: string }>();
  const { user, token, loading } = useRequireAuth();
  const [cards, setCards] = useState<Flashcard[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    if (!user || !token) return;
    api
      .getFlashcards(topicId, token)
      .then(setCards)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load flashcards."));
  }, [user, token, topicId]);

  function goTo(index: number) {
    setCurrentIndex(index);
    setFlipped(false);
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
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-pulse-coral">{error}</p>
        <Link href="/subjects" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to subjects
        </Link>
      </main>
    );
  }

  if (!cards) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading flashcards…</p>
      </main>
    );
  }

  if (cards.length === 0) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-graphite">This topic doesn&apos;t have any flashcards yet.</p>
        <Link href="/subjects" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to subjects
        </Link>
      </main>
    );
  }

  const card = cards[currentIndex];

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <div className="flex items-center justify-between">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
          Card {currentIndex + 1} of {cards.length}
        </p>
        <Link href="/subjects" className="text-sm text-graphite hover:text-vital-teal">
          Exit
        </Link>
      </div>

      <button
        onClick={() => setFlipped((f) => !f)}
        className="mt-6 flex min-h-[280px] w-full flex-col items-center justify-center rounded-lg border border-mist bg-white px-8 py-10 text-center transition hover:border-vital-teal"
      >
        {!flipped ? (
          <p className="font-display text-2xl font-semibold text-ink-navy">{card.front}</p>
        ) : (
          <p className="whitespace-pre-line text-lg text-graphite">{card.back}</p>
        )}
        <p className="mt-6 font-mono text-xs uppercase tracking-widest text-vital-teal">
          {flipped ? "Click to see question" : "Click to reveal answer"}
        </p>
      </button>

      <div className="mt-6 flex items-center justify-between">
        <button
          onClick={() => goTo(Math.max(0, currentIndex - 1))}
          disabled={currentIndex === 0}
          className="rounded-md border border-mist px-5 py-2.5 font-medium text-ink-navy disabled:opacity-40"
        >
          Previous
        </button>
        <button
          onClick={() => goTo(Math.min(cards.length - 1, currentIndex + 1))}
          disabled={currentIndex === cards.length - 1}
          className="rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-40"
        >
          Next card
        </button>
      </div>
    </main>
  );
}
