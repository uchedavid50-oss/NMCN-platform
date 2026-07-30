"use client";

import { motion } from "framer-motion";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <motion.div
      className={`rounded-md bg-mist/60 ${className}`}
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}

export function PageSkeleton() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-4 px-6 py-16">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-8 w-2/3" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-24 w-full" />
    </main>
  );
}
