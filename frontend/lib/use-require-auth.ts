"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./auth-context";

/** Redirects to /login if there's no authenticated user once the initial
 * auth check has finished. Returns the same { user, token, loading } shape
 * so pages can just early-return on loading/!user. */
export function useRequireAuth() {
  const { user, token, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  return { user, token, loading };
}
