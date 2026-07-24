"use client";

/**
 * A friendly, minimal mascot — a heart with a stethoscope, waving.
 * Deliberately simple/geometric so it renders reliably as inline SVG
 * (no external image files, no extra network requests) and matches the
 * platform's existing color tokens automatically, including dark mode.
 */
export function Mascot({ className = "h-32 w-32", wave = true }: { className?: string; wave?: boolean }) {
  return (
    <svg viewBox="0 0 200 200" className={className} xmlns="http://www.w3.org/2000/svg">
      {/* Body: rounded heart shape */}
      <path
        d="M100 170 C40 130, 20 90, 40 60 C55 38, 85 38, 100 62 C115 38, 145 38, 160 60 C180 90, 160 130, 100 170 Z"
        fill="var(--color-vital-teal)"
      />
      {/* Face */}
      <circle cx="82" cy="88" r="6" fill="var(--color-chart-cream)" />
      <circle cx="118" cy="88" r="6" fill="var(--color-chart-cream)" />
      <path
        d="M80 108 Q100 122 120 108"
        stroke="var(--color-chart-cream)"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      {/* Stethoscope */}
      <path
        d="M70 60 Q70 40 90 40"
        stroke="var(--color-pulse-coral)"
        strokeWidth="4"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M130 60 Q130 40 110 40"
        stroke="var(--color-pulse-coral)"
        strokeWidth="4"
        fill="none"
        strokeLinecap="round"
      />
      <circle cx="100" cy="40" r="6" fill="var(--color-pulse-coral)" />
      {/* Waving arm */}
      {wave && (
        <g style={{ transformOrigin: "165px 95px" }} className={wave ? "animate-mascot-wave" : ""}>
          <path
            d="M160 100 Q180 85 178 65"
            stroke="var(--color-vital-teal)"
            strokeWidth="10"
            strokeLinecap="round"
            fill="none"
          />
        </g>
      )}
    </svg>
  );
}
