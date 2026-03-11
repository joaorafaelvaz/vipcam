"use client";

import { useEffect, useRef, useState } from "react";
import { Camera as CameraIcon, WifiOff } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { Camera } from "@/types";

interface CameraCardProps {
  camera: Camera;
}

export function CameraCard({ camera }: CameraCardProps) {
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    let timer: ReturnType<typeof setTimeout>;
    let fails = 0;

    async function poll() {
      try {
        const res = await fetch(`/api/cameras/${camera.id}/snapshot`);
        if (!mountedRef.current) return;
        if (res.ok) {
          const blob = await res.blob();
          if (!mountedRef.current) return;
          const url = URL.createObjectURL(blob);
          setImgSrc((prev) => {
            if (prev) URL.revokeObjectURL(prev);
            return url;
          });
          setError(false);
          fails = 0;
          timer = setTimeout(poll, 5000);
        } else {
          fails++;
          setError(true);
          if (fails < 5) timer = setTimeout(poll, 15000);
        }
      } catch {
        if (!mountedRef.current) return;
        fails++;
        setError(true);
        if (fails < 5) timer = setTimeout(poll, 15000);
      }
    }

    timer = setTimeout(poll, 500 + Math.random() * 2000);

    return () => {
      mountedRef.current = false;
      clearTimeout(timer);
    };
  }, [camera.id]);

  return (
    <Card className="overflow-hidden group hover:border-zinc-700/80 transition-colors">
      <div className="relative aspect-video bg-zinc-900">
        {imgSrc && !error ? (
          <img
            src={imgSrc}
            alt={camera.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            {error ? (
              <WifiOff className="h-8 w-8 text-zinc-700" />
            ) : (
              <CameraIcon className="h-8 w-8 text-zinc-700 animate-pulse" />
            )}
          </div>
        )}
        <div className="absolute top-2 left-2">
          <div
            className={`h-2.5 w-2.5 rounded-full ${
              camera.is_active
                ? "bg-emerald-400 shadow shadow-emerald-400/50"
                : "bg-zinc-600"
            }`}
          />
        </div>
      </div>
      <div className="px-3 py-2.5">
        <h3 className="text-sm font-medium text-zinc-200 truncate">
          {camera.name}
        </h3>
        {camera.location && (
          <p className="text-[11px] text-zinc-500 truncate">
            {camera.location}
          </p>
        )}
      </div>
    </Card>
  );
}
