"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EMOTION_COLORS, EMOTION_LABELS, EMOTION_NAMES } from "@/types";
import type { EmotionTimelinePoint } from "@/types";

interface EmotionTimelineProps {
  data: EmotionTimelinePoint[];
}

export function EmotionTimeline({ data }: EmotionTimelineProps) {
  const chartData = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis
          dataKey="time"
          stroke="#52525b"
          fontSize={11}
          tickLine={false}
        />
        <YAxis
          stroke="#52525b"
          fontSize={11}
          tickLine={false}
          domain={[0, 1]}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#18181b",
            border: "1px solid #3f3f46",
            borderRadius: "8px",
            fontSize: "12px",
          }}
          labelStyle={{ color: "#a1a1aa" }}
          formatter={(value, name) => [
            Number(value).toFixed(3),
            EMOTION_LABELS[name as keyof typeof EMOTION_LABELS] || String(name),
          ]}
        />
        {EMOTION_NAMES.map((emotion) => (
          <Area
            key={emotion}
            type="monotone"
            dataKey={emotion}
            stackId="1"
            stroke={EMOTION_COLORS[emotion]}
            fill={EMOTION_COLORS[emotion]}
            fillOpacity={0.6}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
