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
  const connected = useRealtimeStore((s) => s.connected);

  useEffect(() => {
    fetchCameras();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeCameras = cameras.filter((c) => c.is_active).length;

  return (
    <div>
      <Header
        title="Dashboard"
        subtitle={connected ? "Analise em tempo real" : "Conectando..."}
      />

      <div className="p-6 space-y-6">
        {/* Stats row */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            icon={Users}
            label="Cameras Ativas"
            value={activeCameras}
            color="text-blue-400"
          />
          <StatCard
            icon={Eye}
            label="Faces Reconhecidas"
            value={0}
            color="text-emerald-400"
          />
          <StatCard
            icon={Activity}
            label="Total Cameras"
            value={cameras.length}
            color="text-amber-400"
          />
          <StatCard
            icon={SmilePlus}
            label="Satisfacao Media"
            value="—"
            color="text-purple-400"
          />
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

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-800/50 ${color}`}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-2xl font-bold tabular-nums">{value}</p>
          <p className="text-[11px] text-zinc-500 uppercase tracking-wider">
            {label}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
