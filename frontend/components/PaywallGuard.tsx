"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

// Pages an unpaid user may see. Everything else is paywalled. The landing
// page and auth pages are public; /subscribe and /payment/callback are how
// they pay; /settings/* is account management (devices, 2FA), which the
// backend also leaves open. This is a default-deny list, so a newly added
// page is protected automatically.
const OPEN_EXACT = new Set([
  "/",
  "/login",
  "/signup",
  "/forgot-password",
  "/reset-password",
  "/verify-email",
  "/subscribe",
  "/payment/callback",
]);
const OPEN_PREFIXES = ["/settings/"];

function isOpen(pathname: string) {
  const p = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  return OPEN_EXACT.has(p) || OPEN_PREFIXES.some((prefix) => p.startsWith(prefix));
}

/** Route guard: a logged-in user who isn't paid (and isn't an admin) is
 * redirected to /subscribe from every protected page. Anonymous visitors
 * are left to each page's own login redirect. The backend enforces the
 * same rule (require_paid_user); this only avoids showing a broken page. */
export function PaywallGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const blocked =
    !!user && user.role !== "admin" && user.subscription_status !== "active" && !isOpen(pathname);

  useEffect(() => {
    if (blocked) router.replace("/subscribe");
  }, [blocked, router]);

  // Don't flash protected content while auth is resolving or while redirecting.
  if (blocked || (loading && !isOpen(pathname))) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }
  return <>{children}</>;
}
