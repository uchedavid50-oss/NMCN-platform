"use client";

export interface MovingCardItem {
  text: string;
}

export function InfiniteMovingCards({
  items,
  speedSeconds = 32,
}: {
  items: MovingCardItem[];
  speedSeconds?: number;
}) {
  return (
    <div className="relative overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_10%,black_90%,transparent)]">
      <div className="animate-marquee flex w-max gap-4" style={{ animationDuration: `${speedSeconds}s` }}>
        {[...items, ...items].map((item, i) => (
          <div
            key={i}
            className="w-72 shrink-0 rounded-2xl border border-mist bg-card-bg p-6 shadow-md"
          >
            <p className="text-sm text-graphite">{item.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
