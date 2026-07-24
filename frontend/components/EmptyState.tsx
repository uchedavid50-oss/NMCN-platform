import { Mascot } from "./Mascot";

/**
 * Reusable friendly empty-state — mascot + message + optional action,
 * instead of a bare line of gray text. Use anywhere a list/collection is
 * empty: no notes yet, no cases yet, no badges earned yet, etc.
 */
export function EmptyState({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center rounded-md border border-dashed border-mist px-6 py-12 text-center">
      <Mascot className="h-20 w-20" wave={false} />
      <p className="mt-4 font-display text-lg font-semibold text-ink-navy">{title}</p>
      {subtitle && <p className="mt-1 max-w-sm text-sm text-graphite">{subtitle}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
