"use client";

import { useEffect, useState } from "react";

/**
 * Lightweight CSS-based confetti burst — no external library, no images.
 * Renders a fixed number of small colored rectangles that fall and fade,
 * then unmounts itself. Trigger by mounting this component conditionally
 * (e.g. `{justCompleted && <Confetti />}`) around a celebratory moment:
 * a badge unlock, a streak milestone, a successful subscription.
 */
const COLORS = ["var(--color-vital-teal)", "var(--color-pulse-coral)", "#f5c451", "#7cc4ff"];
const PIECE_COUNT = 40;

export function Confetti() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setVisible(false), 2600);
    return () => clearTimeout(t);
  }, []);

  if (!visible) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-[100] overflow-hidden">
      {Array.from({ length: PIECE_COUNT }).map((_, i) => {
        const left = Math.random() * 100;
        const delay = Math.random() * 0.4;
        const duration = 1.8 + Math.random() * 1;
        const color = COLORS[i % COLORS.length];
        const rotate = Math.random() * 360;
        return (
          <span
            key={i}
            style={{
              left: `${left}%`,
              backgroundColor: color,
              animationDelay: `${delay}s`,
              animationDuration: `${duration}s`,
              transform: `rotate(${rotate}deg)`,
            }}
            className="confetti-piece absolute top-[-10px] h-2.5 w-1.5 rounded-sm"
          />
        );
      })}
    </div>
  );
}
