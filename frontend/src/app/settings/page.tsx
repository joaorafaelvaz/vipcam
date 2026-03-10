"use client";

import { useState } from "react";

import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function SettingsPage() {
  const [faceThreshold, setFaceThreshold] = useState(0.6);
  const [emaAlpha, setEmaAlpha] = useState(0.3);
  const [fpsTarget, setFpsTarget] = useState(5);

  return (
    <div>
      <Header title="Configuracoes" subtitle="Parametros do sistema" />

      <div className="p-6 space-y-6 max-w-2xl">
        {/* Pipeline settings */}
        <Card>
          <CardHeader>
            <h3 className="text-sm font-medium text-zinc-300">
              Pipeline de Processamento
            </h3>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-zinc-400">
                  Threshold de Reconhecimento Facial
                </label>
                <span className="text-sm text-zinc-200 tabular-nums font-medium">
                  {faceThreshold.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={0.3}
                max={0.9}
                step={0.05}
                value={faceThreshold}
                onChange={(e) => setFaceThreshold(Number(e.target.value))}
                className="w-full accent-amber-500"
              />
              <p className="text-[11px] text-zinc-600 mt-1">
                Similaridade minima (cosseno) para considerar a mesma pessoa. Maior = mais conservador.
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-zinc-400">
                  Suavizacao de Emocao (EMA Alpha)
                </label>
                <span className="text-sm text-zinc-200 tabular-nums font-medium">
                  {emaAlpha.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={0.1}
                max={0.9}
                step={0.05}
                value={emaAlpha}
                onChange={(e) => setEmaAlpha(Number(e.target.value))}
                className="w-full accent-amber-500"
              />
              <p className="text-[11px] text-zinc-600 mt-1">
                Peso do frame atual na media movel exponencial. Menor = mais suave.
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-zinc-400">
                  FPS Target
                </label>
                <span className="text-sm text-zinc-200 tabular-nums font-medium">
                  {fpsTarget} FPS
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={15}
                step={1}
                value={fpsTarget}
                onChange={(e) => setFpsTarget(Number(e.target.value))}
                className="w-full accent-amber-500"
              />
              <p className="text-[11px] text-zinc-600 mt-1">
                Frames por segundo processados por camera.
              </p>
            </div>

            <div className="pt-2">
              <Button>Salvar Configuracoes</Button>
            </div>
          </CardContent>
        </Card>

        {/* System info */}
        <Card>
          <CardHeader>
            <h3 className="text-sm font-medium text-zinc-300">
              Informacoes do Sistema
            </h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-500">GPU</span>
                <span className="text-zinc-300">NVIDIA RTX 3060 Ti (8GB)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">VRAM Estimado</span>
                <span className="text-zinc-300">~3.8 GB / 8 GB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Modelos</span>
                <span className="text-zinc-300">YOLOv8x + buffalo_l + enet_b2_8</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Versao</span>
                <span className="text-zinc-300">v0.1.0</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
