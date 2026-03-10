"use client";

import { cn } from "@/lib/utils";

interface HeatmapData {
  day: number; // 0-6 (Sun-Sat)
  hour: number; // 0-23
  value: number;
}

interface OccupancyHeatmapProps {
  data: HeatmapData[];
  maxValue?: number;
}

const DAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function getColor(value: number, max: number): string {
  if (max === 0) return "bg-zinc-800/30";
  const ratio = value / max;
  if (ratio === 0) return "bg-zinc-800/30";
  if (ratio < 0.25) return "bg-amber-500/20";
  if (ratio < 0.5) return "bg-amber-500/40";
  if (ratio < 0.75) return "bg-amber-500/60";
  return "bg-amber-500/90";
}

export function OccupancyHeatmap({ data, maxValue }: OccupancyHeatmapProps) {
  const max = maxValue ?? Math.max(...data.map((d) => d.value), 1);
  const lookup = new Map(data.map((d) => [`${d.day}-${d.hour}`, d.value]));

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[600px]">
        {/* Hours header */}
        <div className="flex gap-0.5 ml-10 mb-1">
          {HOURS.map((h) => (
            <div
              key={h}
              className="flex-1 text-center text-[9px] text-zinc-600"
            >
              {h % 3 === 0 ? `${h}h` : ""}
            </div>
          ))}
        </div>

        {/* Grid rows */}
        {DAYS.map((day, dayIdx) => (
          <div key={day} className="flex items-center gap-0.5 mb-0.5">
            <span className="w-9 text-right text-[10px] text-zinc-500 pr-1">
              {day}
            </span>
            {HOURS.map((hour) => {
              const value = lookup.get(`${dayIdx}-${hour}`) ?? 0;
              return (
                <div
                  key={hour}
                  className={cn(
                    "flex-1 aspect-square rounded-sm transition-colors",
                    getColor(value, max),
                  )}
                  title={`${day} ${hour}h: ${value.toFixed(1)} pessoas`}
                />
              );
            })}
          </div>
        ))}

        {/* Legend */}
        <div className="flex items-center gap-2 mt-3 ml-10">
          <span className="text-[9px] text-zinc-600">Menos</span>
          <div className="flex gap-0.5">
            {["bg-zinc-800/30", "bg-amber-500/20", "bg-amber-500/40", "bg-amber-500/60", "bg-amber-500/90"].map(
              (color) => (
                <div
                  key={color}
                  className={cn("h-3 w-3 rounded-sm", color)}
                />
              ),
            )}
          </div>
          <span className="text-[9px] text-zinc-600">Mais</span>
        </div>
      </div>
    </div>
  );
}
