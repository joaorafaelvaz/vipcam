"use client";

interface SatisfactionGaugeProps {
  value: number | null; // 0-10
  previousValue?: number | null;
}

export function SatisfactionGauge({ value, previousValue }: SatisfactionGaugeProps) {
  const normalized = value !== null ? (value / 10) * 100 : 0;
  const radius = 80;
  const circumference = Math.PI * radius;
  const offset = circumference - (normalized / 100) * circumference;

  const color =
    normalized >= 70 ? "#22c55e" : normalized >= 40 ? "#eab308" : "#ef4444";

  const diff =
    value !== null && previousValue != null ? value - previousValue : null;

  return (
    <div className="flex flex-col items-center">
      <svg width="200" height="120" viewBox="0 0 200 120">
        {/* Background arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="#27272a"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s ease, stroke 0.5s ease" }}
        />
        {/* Value text */}
        <text
          x="100"
          y="85"
          textAnchor="middle"
          className="fill-zinc-100 text-3xl font-bold"
          style={{ fontSize: "32px" }}
        >
          {value !== null ? value.toFixed(1) : "—"}
        </text>
        <text
          x="100"
          y="105"
          textAnchor="middle"
          className="fill-zinc-500"
          style={{ fontSize: "11px" }}
        >
          de 10
        </text>
      </svg>

      {diff !== null && (
        <div
          className="flex items-center gap-1 text-xs mt-1"
          style={{ color: diff >= 0 ? "#22c55e" : "#ef4444" }}
        >
          <span>{diff >= 0 ? "+" : ""}{diff.toFixed(1)}</span>
          <span className="text-zinc-600">vs periodo anterior</span>
        </div>
      )}
    </div>
  );
}
