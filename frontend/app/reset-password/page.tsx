"use client";
import { FormEvent, Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ApiError } from "@/lib/api";
import { resetPassword } from "@/lib/api-extras-3";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") || "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    if (!token) {
      setError("This reset link is missing its token — please use the link from your email.");
      return;
    }

    setSubmitting(true);
    try {
      await resetPassword(token, newPassword);
      setSuccess(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 text-center">
        <h1 className="font-display text-3xl font-semibold text-ink-navy">Password reset</h1>
        <p className="mt-3 text-graphite">Redirecting you to log in…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="font-display text-3xl font-semibold text-ink-navy">Set a new password</h1>
      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-ink-navy">New password</span>
          <div className="flex items-stretch gap-2">
            <input
              type={showPasswords ? "text" : "password"}
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="flex-1 rounded-md border border-mist px-4 py-2 focus:border-vital-teal focus:outline-none"
            />
            <button
              type="button"
              onClick={() => setShowPasswords((s) => !s)}
              className="rounded-md border border-mist px-3 text-xs font-medium text-graphite hover:border-vital-teal hover:text-vital-teal"
            >
              {showPasswords ? "Hide" : "Show"}
            </button>
          </div>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-ink-navy">Confirm new password</span>
          <input
            type={showPasswords ? "text" : "password"}
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="rounded-md border border-mist px-4 py-2 focus:border-vital-teal focus:outline-none"
          />
        </label>
        <p className="text-xs text-graphite">
          At least 8 characters, with at least one letter and one number.
        </p>
        {error && <p className="text-sm text-pulse-coral">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {submitting ? "Resetting…" : "Reset password"}
        </button>
      </form>
      <Link href="/login" className="mt-6 text-sm text-vital-teal hover:underline">
        ← Back to login
      </Link>
    </main>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<main className="flex min-h-screen items-center justify-center"><p>Loading…</p></main>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
