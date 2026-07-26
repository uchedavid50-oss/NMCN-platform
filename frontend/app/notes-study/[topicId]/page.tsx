"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import mermaid from "mermaid";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ApiError } from "@/lib/api";
import { getTopicNote, TopicNote } from "@/lib/api-extras-7";

mermaid.initialize({ startOnLoad: false, theme: "neutral" });

function MermaidBlock({ code }: { code: string }) {
  const [svg, setSvg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const id = `mermaid-${Math.random().toString(36).slice(2)}`;
    mermaid
      .render(id, code)
      .then((result) => {
        if (!cancelled) setSvg(result.svg);
      })
      .catch(() => {
        if (!cancelled) setSvg(null);
      });
    return () => {
      cancelled = true;
    };
  }, [code]);

  if (!svg) return <p className="text-sm text-graphite">Loading diagram…</p>;
  return <div className="my-4 flex justify-center" dangerouslySetInnerHTML={{ __html: svg }} />;
}

export default function TopicStudyNotePage() {
  const { topicId } = useParams<{ topicId: string }>();
  const { user, token, loading } = useRequireAuth();
  const [note, setNote] = useState<TopicNote | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (!token) return;
    getTopicNote(topicId, token)
      .then(setNote)
      .catch((err) => {
        setError(
          err instanceof ApiError && err.status === 404
            ? "No study note has been generated for this topic yet."
            : "Couldn't load the study note. Try refreshing."
        );
      })
      .finally(() => setFetching(false));
  }, [topicId, token]);

  if (loading || !user || fetching) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <Link href={`/practice/${topicId}`} className="text-sm text-vital-teal hover:underline">
        ← Back to topic
      </Link>

      <p className="mt-4 font-mono text-sm uppercase tracking-widest text-vital-teal">
        Study Notes
      </p>

      {error && <p className="mt-6 text-pulse-coral">{error}</p>}

      {note && (
        <article className="prose prose-slate mt-6 max-w-none">
          <ReactMarkdown
            components={{
              code({ className, children, ...props }) {
                const match = /language-mermaid/.exec(className || "");
                if (match) {
                  return <MermaidBlock code={String(children).trim()} />;
                }
                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {note.content}
          </ReactMarkdown>
        </article>
      )}

      <div className="mt-10 flex gap-3">
        <Link
          href={`/practice/${topicId}`}
          className="rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
        >
          Practice this topic →
        </Link>
      </div>
    </main>
  );
}