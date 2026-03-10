"use client";

import type { Camera } from "@/types";
import { CameraCard } from "./CameraCard";

interface CameraGridProps {
  cameras: Camera[];
}

export function CameraGrid({ cameras }: CameraGridProps) {
  if (cameras.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-dashed border-zinc-800 py-20">
        <div className="text-center">
          <p className="text-sm text-zinc-500">Nenhuma camera configurada</p>
          <p className="text-xs text-zinc-600 mt-1">
            Adicione cameras na pagina de configuracao
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {cameras.map((camera) => (
        <CameraCard key={camera.id} camera={camera} />
      ))}
    </div>
  );
}
