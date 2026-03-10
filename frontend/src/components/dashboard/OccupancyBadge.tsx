import { cn } from "@/lib/utils";

interface OccupancyBadgeProps {
  count: number;
}

export function OccupancyBadge({ count }: OccupancyBadgeProps) {
  const level =
    count <= 2 ? "low" : count <= 5 ? "moderate" : "high";

  const styles = {
    low: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    moderate: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    high: "bg-red-500/20 text-red-300 border-red-500/40",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold tabular-nums",
        styles[level],
      )}
    >
      <svg
        className="h-3 w-3"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
      </svg>
      {count}
    </div>
  );
}
