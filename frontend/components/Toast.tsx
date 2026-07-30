"use client";

import { motion } from "framer-motion";

export type ToastKind = "info" | "success" | "error";

export interface ToastItemData {
  id: number;
  message: string;
  kind: ToastKind;
}

const KIND_STYLES: Record<ToastKind, string> = {
  error: "border-pulse-coral bg-pulse-coral/10 text-pulse-coral",
  success: "border-vital-teal bg-vital-teal/10 text-vital-teal",
  info: "border-mist bg-card-bg text-ink-navy",
};

export function Toast({ message, kind }: { message: string; kind: ToastKind }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 40, y: -10 }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      exit={{ opacity: 0, x: 40 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`pointer-events-auto rounded-md border px-4 py-3 text-sm font-medium shadow-lg ${KIND_STYLES[kind]}`}
    >
      {message}
    </motion.div>
  );
}
