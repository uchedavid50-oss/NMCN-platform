"use client";
import { useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError } from "@/lib/api";

export default function SecuritySettingsPage() {
  const { user, token, loading } = useRequireAuth();
  const [secret, setSecret] = useState<string | null>(null);
  const [provisioningUri, setProvisioningUri] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(user?.totp_enabled ?? false);

  async function handleStartSetup() {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await api.setupTwoFactor(token);
      setSecret(result.secret);
      setProvisioningUri(result.provisioning_uri);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't start 2FA setup.");
    } finally {
      setBusy(false);
    }
  }

  async function handleVerify() {
    if (!token || code.length !== 6) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api.verifyTwoFactor(code, token);
      setTwoFactorEnabled(updated.totp_enabled);
      setSecret(null);
      setProvisioningUri(null);
      setCode("");
      setMessage("Two-factor authentication is now enabled.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "That code didn't match. Try again.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDisable() {
    if (!token || code.length !== 6) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api.disableTwoFactor(code, token);
      setTwoFactorEnabled(updated.totp_enabled);
      setCode("");
      setMessage("Two-factor authentication has been disabled.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "That code didn't match. Try again.");
    } finally {
      setBusy(false);
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
    <main className="mx-auto max-w-xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Security</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Two-factor authentication
      </h1>
      <p className="mt-3 text-graphite">
        Adds a second step at login using an authenticator app (Google Authenticator, Authy, etc.)
        — strongly recommended for admin accounts.
      </p>

      {message && <p className="mt-4 text-sm text-vital-teal">{message}</p>}
      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      {twoFactorEnabled ? (
        <div className="mt-6 rounded-md border border-vital-teal bg-vital-teal/10 p-5">
          <p className="text-vital-teal">✓ Two-factor authentication is enabled.</p>
          <p className="mt-3 text-sm text-graphite">
            Enter a current code from your authenticator app to disable it.
          </p>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="000000"
              className="w-32 rounded-md border border-mist px-3 py-2 text-center font-mono tracking-widest"
            />
            <button
              onClick={handleDisable}
              disabled={busy || code.length !== 6}
              className="rounded-md border border-pulse-coral px-4 py-2 text-sm font-medium text-pulse-coral transition hover:bg-pulse-coral/10 disabled:opacity-50"
            >
              Disable 2FA
            </button>
          </div>
        </div>
      ) : secret ? (
        <div className="mt-6 rounded-md border border-mist bg-card-bg p-5">
          <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">Step 1</p>
          <p className="mt-1 text-graphite">
            Add this key to your authenticator app (look for &quot;enter setup key manually&quot;
            if you can&apos;t scan a QR code):
          </p>
          <p className="mt-2 select-all break-all rounded-md border border-mist bg-white px-3 py-2 font-mono text-sm text-ink-navy">
            {secret}
          </p>
          {provisioningUri && (
            <a
              href={provisioningUri}
              className="mt-2 inline-block text-xs text-vital-teal hover:underline"
            >
              Or open directly in a compatible app
            </a>
          )}

          <p className="mt-5 font-mono text-xs uppercase tracking-widest text-vital-teal">Step 2</p>
          <p className="mt-1 text-graphite">Enter the 6-digit code your app now shows:</p>
          <div className="mt-2 flex gap-2">
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="000000"
              className="w-32 rounded-md border border-mist px-3 py-2 text-center font-mono tracking-widest"
            />
            <button
              onClick={handleVerify}
              disabled={busy || code.length !== 6}
              className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
            >
              Verify and enable
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={handleStartSetup}
          disabled={busy}
          className="mt-6 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {busy ? "Starting…" : "Set up two-factor authentication"}
        </button>
      )}

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
