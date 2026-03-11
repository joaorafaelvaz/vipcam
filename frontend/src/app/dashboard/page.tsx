"use client";

import { useEffect } from "react";
import { Activity, Eye, SmilePlus, Users } from "lucide-react";

import { Header } from "@/components/layout/Header";
import { CameraGrid } from "@/components/dashboard/CameraGrid";
import { Card, CardContent } from "@/components/ui/Card";
import { useCameraStore } from "@/stores/useCameraStore";
import { useRealtimeStore } from "@/stores/useRealtimeStore";

export default function DashboardPage() {
  const cameras = useCameraStore((s) => s.cameras);
  const fetchCameras = useCameraStore((s) => s.fetchCameras);
  const loading = useCameraStore((s) => s.loading);
  const occupancy = useRealtimeStore((s) => s.occupancy);
  const latestPersons = useRealtimeStore((s) => s.latestPersons);
  const connected = useRealtimeStore((s) => s.connected);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const totalPeople = Object.values(occupancy).reduce((a, b) => a + b, 0);
  const totalFaces = Object.values(latestPersons).reduce(
    (a, b) => a + b.length,
    0,
  );
  const activeCameras = cameras.filter((c) => c.is_active).length;

  // Calculate average satisfaction across all visible persons
  const allPersons = Object.values(latestPersons).flat();
  const avgSatisfaction =
    allPersons.length > 0
      ? allPersons.reduce((sum, p) => sum + (p.satisfaction_score ?? 5), 0) /
        allPersons.length
      : null;

  const stats = [
    {
      label: "Pessoas Detectadas",
      value: totalPeople,
      icon: Users,
      color: "text-blue-400",
    },
    {
      label: "Faces Reconhecidas",
      value: totalFaces,
      icon: Eye,
      color: "text-emerald-400",
    },
    {
      label: "Cameras Ativas",
      value: activeCameras,
      icon: Activity,
      color: "text-amber-400",
    },
    {
      label: "Satisfacao Media",
      value: avgSatisfaction !== null ? `${avgSatisfaction.toFixed(1)}/10` : "—",
      icon: SmilePlus,
      color: "text-purple-400",
    },
  ];

  return (
    <div>
      <Header
        title="Dashboard"
        subtitle={connected ? "Analise em tempo real" : "Conectando..."}
      />

      <div className="p-6 space-y-6">
        {/* Stats row */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.label}>
              <CardContent className="flex items-center gap-4">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-800/50 ${stat.color}`}
                >
                  <stat.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold tabular-nums">
                    {stat.value}
                  </p>
                  <p className="text-[11px] text-zinc-500 uppercase tracking-wider">
                    {stat.label}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Camera grid */}
        <div>
          <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-3">
            Cameras
          </h3>
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
            </div>
          ) : (
            <CameraGrid cameras={cameras} />
          )}
        </div>
      </div>
    </div>
  );
}
