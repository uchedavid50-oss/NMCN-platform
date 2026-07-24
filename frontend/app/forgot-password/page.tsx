"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { ApiError } from "@/lib/api";
import { requestPasswordReset } from "@/lib/api-extras-3";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await requestPasswordReset(email);
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 text-center">
        <h1 className="font-display text-3xl font-semibold text-ink-navy">Check your email</h1>
        <p className="mt-3 text-graphite">
          If an account exists for <strong>{email}</strong>, a password reset link is on its way.
          It expires in 1 hour.
        </p>
        <Link href="/login" className="mt-6 text-vital-teal hover:underline">
          ← Back to login
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="font-display text-3xl font-semibold text-ink-navy">Reset your password</h1>
      <p className="mt-2 text-graphite">
        Enter your account email and we&apos;ll send you a link to set a new password.
      </p>
      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-ink-navy">Email</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-mist px-4 py-2 focus:border-vital-teal focus:outline-none"
          />
        </label>
        {error && <p className="text-sm text-pulse-coral">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {submitting ? "Sending…" : "Send reset link"}
        </button>
      </form>
      <Link href="/login" className="mt-6 text-sm text-vital-teal hover:underline">
        ← Back to login
      </Link>
    </main>
  );
}
