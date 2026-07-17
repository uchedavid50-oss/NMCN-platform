export function PulseTrace({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 400 80"
      className={className}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        className="pulse-trace"
        d="M0,40 L60,40 L75,10 L90,70 L105,40 L160,40 L175,25 L190,55 L205,40 L400,40"
      />
    </svg>
  );
}
