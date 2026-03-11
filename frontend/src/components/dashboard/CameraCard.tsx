import { Camera as CameraIcon } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { Camera } from "@/types";

interface CameraCardProps {
  camera: Camera;
}

export function CameraCard({ camera }: CameraCardProps) {
  return (
    <Card className="overflow-hidden group hover:border-zinc-700/80 transition-colors">
      <div className="relative aspect-video bg-zinc-900">
        <div className="flex h-full w-full items-center justify-center">
          <CameraIcon className="h-8 w-8 text-zinc-700" />
        </div>
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
