"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Camera as CameraIcon, WifiOff } from "lucide-react";

import { Card } from "@/components/ui/Card";
import { useRealtimeStore } from "@/stores/useRealtimeStore";
import type { Camera } from "@/types";
import { OccupancyBadge } from "./OccupancyBadge";

const EMPTY_PERSONS: never[] = [];

interface CameraCardProps {
  camera: Camera;
}

export function CameraCard({ camera }: CameraCardProps) {
  const occupancy = useRealtimeStore(
    useCallback((s) => s.occupancy[camera.id] ?? 0, [camera.id]),
  );
  const persons = useRealtimeStore(
    useCallback((s) => s.latestPersons[camera.id] ?? EMPTY_PERSONS, [camera.id]),
  );
  const connected = useRealtimeStore((s) => s.connected);
  const [snapshotUrl, setSnapshotUrl] = useState<string | null>(null);
  const [snapshotError, setSnapshotError] = useState(false);
  const failCountRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let active = true;

    async function fetchSnapshot() {
      try {
        const res = await fetch(`/api/cameras/${camera.id}/snapshot`);
        if (!active) return;
        if (res.ok) {
          const blob = await res.blob();
          if (!active) return;
          const url = URL.createObjectURL(blob);
          setSnapshotUrl((prev) => {
            if (prev) URL.revokeObjectURL(prev);
            return url;
          });
          setSnapshotError(false);
          failCountRef.current = 0;
          scheduleNext(2000);
        } else {
          failCountRef.current++;
          if (failCountRef.current <= 1) setSnapshotError(true);
          // After 3 failures, poll slowly; after 10, stop entirely
          if (failCountRef.current >= 10) return;
          scheduleNext(failCountRef.current >= 3 ? 30000 : 5000);
        }
      } catch {
        if (!active) return;
        failCountRef.current++;
        if (failCountRef.current <= 1) setSnapshotError(true);
        if (failCountRef.current >= 10) return;
        scheduleNext(failCountRef.current >= 3 ? 30000 : 5000);
      }
    }

    function scheduleNext(delay: number) {
      if (!active) return;
      timeoutRef.current = setTimeout(fetchSnapshot, delay);
    }

    // Delay initial fetch to avoid burst on page load
    timeoutRef.current = setTimeout(fetchSnapshot, 1000);

    return () => {
      active = false;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [camera.id]);

  const dominantEmotion = persons.length > 0 ? persons[0]?.dominant_emotion : null;

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

        {/* Simple emotion indicator */}
        {dominantEmotion && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-3 py-2">
            <span className="text-[10px] text-zinc-300">{dominantEmotion}</span>
          </div>
        )}
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
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <div
            className={`h-1.5 w-1.5 rounded-full ${
              connected ? "bg-emerald-400" : "bg-zinc-600"
            }`}
          />
          <span className="text-[10px] text-zinc-600 tabular-nums">
            {camera.fps_target} FPS
          </span>
        </div>
      </div>
    </Card>
  );
}
