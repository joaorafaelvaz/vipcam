"use client";

import { useEffect, useState } from "react";
import { Users, Eye, Smile, Activity } from "lucide-react";

import { Header } from "@/components/layout/Header";
import { CameraCard } from "@/components/dashboard/CameraCard";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useCameraStore } from "@/stores/useCameraStore";
import { useRealtimeStore } from "@/stores/useRealtimeStore";
import { api } from "@/lib/api";
import { formatEmotion, emotionColor } from "@/lib/utils";

interface DashboardSummary {
  unique_persons_today: number;
  total_persons: number;
  avg_satisfaction_today: number | null;
  cameras: {
    camera_id: string;
    camera_name: string;
    camera_location: string | null;
    person_count: number;
    avg_satisfaction: number;
    unique_persons: number;
    dominant_emotion: string;
  }[];
}

function StatCard({
  icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  accent: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className={`${accent} opacity-60`}>{icon}</div>
          <div>
            <p className="text-[11px] text-zinc-500 uppercase tracking-wider">
              {label}
            </p>
            <p className={`text-xl font-bold ${accent}`}>{value}</p>
            {sub && <p className="text-[10px] text-zinc-600">{sub}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function MiniStat({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="text-center">
      <p className={`text-lg font-bold ${color}`}>{value}</p>
      <p className="text-[10px] text-zinc-500">{label}</p>
    </div>
  );
}

export default function DashboardPage() {
  const cameras = useCameraStore((s) => s.cameras);
  const fetchCameras = useCameraStore((s) => s.fetchCameras);
  const connected = useRealtimeStore((s) => s.connected);
  const occupancy = useRealtimeStore((s) => s.occupancy);
  const latestPersons = useRealtimeStore((s) => s.latestPersons);
  const processingTime = useRealtimeStore((s) => s.processingTime);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    fetchCameras();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Poll dashboard summary every 15s
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await api.get<DashboardSummary>("/analytics/dashboard");
        if (active) setSummary(data);
      } catch {
        // ignore
      }
    }
    load();
    const interval = setInterval(load, 15000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const totalOccupancy = Object.values(occupancy).reduce((a, b) => a + b, 0);

  return (
    <div>
      <Header
        title="Dashboard"
        subtitle={
          connected
            ? "Monitoramento em tempo real"
            : "Conectando ao pipeline..."
        }
      />

      <div className="p-6 space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            icon={<Users className="h-5 w-5" />}
            label="Pessoas Agora"
            value={totalOccupancy}
            accent="text-amber-400"
          />
          <StatCard
            icon={<Eye className="h-5 w-5" />}
            label="Unicas Hoje"
            value={summary?.unique_persons_today ?? "—"}
            sub={
              summary ? `${summary.total_persons} total no banco` : undefined
            }
            accent="text-blue-400"
          />
          <StatCard
            icon={<Smile className="h-5 w-5" />}
            label="Satisfacao Media"
            value={
              summary?.avg_satisfaction_today != null
                ? `${summary.avg_satisfaction_today}/10`
                : "—"
            }
            accent="text-emerald-400"
          />
          <StatCard
            icon={<Activity className="h-5 w-5" />}
            label="Pipeline"
            value={connected ? "Ativo" : "Offline"}
            sub={
              Object.keys(processingTime).length > 0
                ? `${Math.round(
                    Object.values(processingTime).reduce((a, b) => a + b, 0) /
                      Object.values(processingTime).length,
                  )}ms/frame`
                : undefined
            }
            accent={connected ? "text-emerald-400" : "text-red-400"}
          />
        </div>

        {/* Per-camera sections */}
        {summary && summary.cameras.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
              Por Unidade / Camera
            </h2>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {summary.cameras.map((cam) => {
                const rtOccupancy = occupancy[cam.camera_id];
                const rtPersons = latestPersons[cam.camera_id];
                const rtTime = processingTime[cam.camera_id];

                return (
                  <Card key={cam.camera_id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="text-sm font-semibold text-zinc-200">
                            {cam.camera_name}
                          </h3>
                          {cam.camera_location && (
                            <p className="text-[11px] text-zinc-500">
                              {cam.camera_location}
                            </p>
                          )}
                        </div>
                        <Badge
                          variant={
                            cam.dominant_emotion === "happiness"
                              ? "success"
                              : cam.dominant_emotion === "neutral"
                                ? "default"
                                : "warning"
                          }
                        >
                          {formatEmotion(cam.dominant_emotion)}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        <MiniStat
                          label="Pessoas"
                          value={rtOccupancy ?? cam.person_count}
                          color="text-amber-400"
                        />
                        <MiniStat
                          label="Unicas (5min)"
                          value={cam.unique_persons}
                          color="text-blue-400"
                        />
                        <MiniStat
                          label="Satisfacao"
                          value={
                            cam.avg_satisfaction > 0
                              ? cam.avg_satisfaction.toFixed(1)
                              : "—"
                          }
                          color="text-emerald-400"
                        />
                      </div>

                      {/* Real-time detected faces */}
                      {rtPersons && rtPersons.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-zinc-800/50">
                          <div className="flex items-center gap-2 flex-wrap">
                            {rtPersons.slice(0, 6).map((p, i) => (
                              <div
                                key={i}
                                className="flex items-center gap-1.5 rounded-md bg-zinc-800/60 px-2 py-1"
                              >
                                <div
                                  className="h-2 w-2 rounded-full"
                                  style={{
                                    backgroundColor: emotionColor(
                                      p.dominant_emotion,
                                    ),
                                  }}
                                />
                                <span className="text-[10px] text-zinc-400">
                                  {formatEmotion(p.dominant_emotion)}
                                </span>
                                {p.satisfaction_score != null && (
                                  <span className="text-[10px] text-zinc-500">
                                    {p.satisfaction_score.toFixed(1)}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {rtTime != null && (
                        <p className="text-[10px] text-zinc-600 mt-2">
                          {Math.round(rtTime)}ms/frame
                        </p>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Camera feeds */}
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
            Feeds ao Vivo
          </h2>
          {cameras.length === 0 ? (
            <div className="flex items-center justify-center rounded-xl border border-dashed border-zinc-800 py-20">
              <p className="text-sm text-zinc-500">
                Nenhuma camera configurada
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {cameras.map((camera) => (
                <CameraCard key={camera.id} camera={camera} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
