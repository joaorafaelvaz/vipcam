"use client";

import { useEffect, useState } from "react";
import { Camera as CameraIcon, WifiOff } from "lucide-react";

import { Card } from "@/components/ui/Card";
import { useRealtimeStore } from "@/stores/useRealtimeStore";
import type { Camera } from "@/types";
import { EmotionOverlay } from "./EmotionOverlay";
import { OccupancyBadge } from "./OccupancyBadge";

interface CameraCardProps {
  camera: Camera;
}

export function CameraCard({ camera }: CameraCardProps) {
  const occupancy = useRealtimeStore((s) => s.occupancy[camera.id] ?? 0);
  const persons = useRealtimeStore((s) => s.latestPersons[camera.id] ?? []);
  const [snapshotUrl, setSnapshotUrl] = useState<string | null>(null);
  const [snapshotError, setSnapshotError] = useState(false);

  useEffect(() => {
    let active = true;

    async function fetchSnapshot() {
      try {
        const res = await fetch(`/api/cameras/${camera.id}/snapshot`);
        if (res.ok && active) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          setSnapshotUrl((prev) => {
            if (prev) URL.revokeObjectURL(prev);
            return url;
          });
          setSnapshotError(false);
        } else {
          setSnapshotError(true);
        }
      } catch {
        setSnapshotError(true);
      }
    }

    fetchSnapshot();
    const interval = setInterval(fetchSnapshot, 2000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [camera.id]);

  return (
    <Card className="overflow-hidden group hover:border-zinc-700/80 transition-colors">
      {/* Snapshot area */}
      <div className="relative aspect-video bg-zinc-900">
        {snapshotUrl && !snapshotError ? (
          <img
            src={snapshotUrl}
            alt={camera.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            {snapshotError ? (
              <WifiOff className="h-8 w-8 text-zinc-700" />
            ) : (
              <CameraIcon className="h-8 w-8 text-zinc-700 animate-pulse" />
            )}
          </div>
        )}

        {/* Occupancy badge */}
        <div className="absolute top-2 right-2">
          <OccupancyBadge count={occupancy} />
        </div>

        {/* Active indicator */}
        <div className="absolute top-2 left-2">
          <div
            className={`h-2.5 w-2.5 rounded-full ${
              camera.is_active
                ? "bg-emerald-400 shadow shadow-emerald-400/50"
                : "bg-zinc-600"
            }`}
          />
        </div>

        {/* Emotion overlay */}
        <EmotionOverlay persons={persons} />
      </div>

      {/* Info bar */}
      <div className="px-3 py-2.5 flex items-center justify-between">
        <div className="min-w-0">
          <h3 className="text-sm font-medium text-zinc-200 truncate">
            {camera.name}
          </h3>
          {camera.location && (
            <p className="text-[11px] text-zinc-500 truncate">
              {camera.location}
            </p>
          )}
        </div>
        <span className="text-[10px] text-zinc-600 tabular-nums shrink-0 ml-2">
          {camera.fps_target} FPS
        </span>
      </div>
    </Card>
  );
}
