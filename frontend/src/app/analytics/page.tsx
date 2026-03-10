"use client";

import { useEffect, useState } from "react";

import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { EmotionTimeline } from "@/components/analytics/EmotionTimeline";
import { OccupancyHeatmap } from "@/components/analytics/OccupancyHeatmap";
import { SatisfactionGauge } from "@/components/analytics/SatisfactionGauge";
import { api } from "@/lib/api";
import type { EmotionTimelinePoint } from "@/types";

export default function AnalyticsPage() {
  const [timeline, setTimeline] = useState<EmotionTimelinePoint[]>([]);
  const [satisfaction, setSatisfaction] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const now = new Date();
    const start = new Date(now.getTime() - 24 * 60 * 60 * 1000); // last 24h

    Promise.all([
      api
        .get<EmotionTimelinePoint[]>(
          `/emotions/timeline?start=${start.toISOString()}&end=${now.toISOString()}&bucket_minutes=30`,
        )
        .catch(() => []),
      api
        .get<{ avg_satisfaction: number | null }>(
          `/emotions/summary?start=${start.toISOString()}&end=${now.toISOString()}`,
        )
        .catch(() => ({ avg_satisfaction: null })),
    ]).then(([timelineData, summary]) => {
      setTimeline(timelineData);
      setSatisfaction(summary.avg_satisfaction);
      setLoading(false);
    });
  }, []);

  // Mock heatmap data (in production, this would come from the API)
  const heatmapData = Array.from({ length: 7 * 24 }, (_, i) => ({
    day: Math.floor(i / 24),
    hour: i % 24,
    value: Math.random() * 10,
  }));

  return (
    <div>
      <Header title="Analytics" subtitle="Ultimas 24 horas" />

      <div className="p-6 space-y-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
          </div>
        ) : (
          <>
            {/* Top row: Satisfaction + Stats */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <Card>
                <CardHeader>
                  <h3 className="text-sm font-medium text-zinc-300">
                    Satisfacao Geral
                  </h3>
                </CardHeader>
                <CardContent className="flex justify-center">
                  <SatisfactionGauge value={satisfaction} />
                </CardContent>
              </Card>

              <Card className="lg:col-span-2">
                <CardHeader>
                  <h3 className="text-sm font-medium text-zinc-300">
                    Distribuicao de Emocoes
                  </h3>
                </CardHeader>
                <CardContent>
                  <EmotionTimeline data={timeline} />
                </CardContent>
              </Card>
            </div>

            {/* Heatmap */}
            <Card>
              <CardHeader>
                <h3 className="text-sm font-medium text-zinc-300">
                  Heatmap de Ocupacao (Hora x Dia)
                </h3>
              </CardHeader>
              <CardContent>
                <OccupancyHeatmap data={heatmapData} />
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
