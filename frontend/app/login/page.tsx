"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [requiresTwoFactor, setRequiresTwoFactor] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function attemptLogin(code?: string) {
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password, code);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        // Password was correct -- server is asking for the second factor.
        setRequiresTwoFactor(true);
      } else {
        setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await attemptLogin();
  }

  async function handleTwoFactorSubmit(e: FormEvent) {
    e.preventDefault();
    await attemptLogin(totpCode);
  }

  if (requiresTwoFactor) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
        <h1 className="font-display text-3xl font-semibold text-ink-navy">Enter your code</h1>
        <p className="mt-2 text-graphite">
          Open your authenticator app and enter the 6-digit code for this account.
        </p>
        <form onSubmit={handleTwoFactorSubmit} className="mt-8 flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-ink-navy">Authentication code</span>
            <input
              type="text"
              inputMode="numeric"
              autoFocus
              required
              maxLength={6}
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
              className="rounded-md border border-mist px-4 py-2 text-center font-mono text-lg tracking-widest focus:border-vital-teal focus:outline-none"
            />
          </label>
          {error && <p className="text-sm text-pulse-coral">{error}</p>}
          <button
            type="submit"
            disabled={submitting || totpCode.length !== 6}
            className="mt-2 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
          >
            {submitting ? "Verifying…" : "Verify and log in"}
          </button>
          <button
            type="button"
            onClick={() => {
              setRequiresTwoFactor(false);
              setTotpCode("");
              setError(null);
            }}
            className="text-sm text-graphite hover:underline"
          >
            ← Back
          </button>
        </form>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="font-display text-3xl font-semibold text-ink-navy">Log in</h1>
      <p className="mt-2 text-graphite">Pick up where you left off.</p>
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
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-ink-navy">Password</span>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-mist px-4 py-2 focus:border-vital-teal focus:outline-none"
          />
        </label>
        {error && <p className="text-sm text-pulse-coral">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className="mt-6 text-sm text-graphite">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="font-medium text-vital-teal hover:underline">
          Sign up
        </Link>
      </p>
    </main>
  );
}
