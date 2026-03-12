"use client";

import { useEffect, useState } from "react";
import { Loader2, Check, AlertCircle } from "lucide-react";

import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";

interface Settings {
  face_match_threshold: number;
  emotion_ema_alpha: number;
  processing_fps_target: number;
  enable_pipeline: boolean;
  yolo_conf: number;
  yolo_imgsz: number;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "ok" | "error">("idle");

  const [faceThreshold, setFaceThreshold] = useState(0.6);
  const [emaAlpha, setEmaAlpha] = useState(0.3);
  const [fpsTarget, setFpsTarget] = useState(5);
  const [enablePipeline, setEnablePipeline] = useState(false);
  const [yoloConf, setYoloConf] = useState(0.5);

  useEffect(() => {
    api
      .get<Settings>("/settings")
      .then((s) => {
        setSettings(s);
        setFaceThreshold(s.face_match_threshold);
        setEmaAlpha(s.emotion_ema_alpha);
        setFpsTarget(s.processing_fps_target);
        setEnablePipeline(s.enable_pipeline);
        setYoloConf(s.yolo_conf);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaveStatus("idle");
    try {
      const updated = await api.patch<Settings>("/settings", {
        face_match_threshold: faceThreshold,
        emotion_ema_alpha: emaAlpha,
        processing_fps_target: fpsTarget,
        enable_pipeline: enablePipeline,
        yolo_conf: yoloConf,
      });
      setSettings(updated);
      setSaveStatus("ok");
      setTimeout(() => setSaveStatus("idle"), 3000);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Header title="Configuracoes" subtitle="Parametros do sistema" />
        <div className="flex items-center justify-center p-20">
          <Loader2 className="h-6 w-6 animate-spin text-zinc-600" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <Header title="Configuracoes" subtitle="Parametros do sistema" />

      <div className="p-6 space-y-6 max-w-2xl">
        {/* Pipeline toggle */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-zinc-300">
                Pipeline GPU
              </h3>
              <Badge variant={enablePipeline ? "success" : "default"}>
                {enablePipeline ? "Ativo" : "Desativado"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">
                  Processamento de deteccao facial, reconhecimento e emocoes
                </p>
                <p className="text-[11px] text-zinc-600 mt-1">
                  Requer GPU NVIDIA. Modelos: YOLOv8x + InsightFace + HSEmotion
                </p>
              </div>
              <button
                onClick={() => setEnablePipeline(!enablePipeline)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  enablePipeline ? "bg-amber-500" : "bg-zinc-700"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    enablePipeline ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
            <p className="text-[11px] text-amber-500/80 mt-3">
              Nota: ativar/desativar o pipeline requer reiniciar o backend para ter efeito.
            </p>
          </CardContent>
        </Card>

        {/* Pipeline settings */}
        <Card>
          <CardHeader>
            <h3 className="text-sm font-medium text-zinc-300">
              Parametros de Processamento
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
                  Confianca YOLO
                </label>
                <span className="text-sm text-zinc-200 tabular-nums font-medium">
                  {yoloConf.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={0.2}
                max={0.9}
                step={0.05}
                value={yoloConf}
                onChange={(e) => setYoloConf(Number(e.target.value))}
                className="w-full accent-amber-500"
              />
              <p className="text-[11px] text-zinc-600 mt-1">
                Confianca minima para deteccao de pessoas. Menor = mais deteccoes (mais falsos positivos).
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

            <div className="pt-2 flex items-center gap-3">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Salvar Configuracoes"
                )}
              </Button>
              {saveStatus === "ok" && (
                <span className="flex items-center gap-1 text-sm text-emerald-400">
                  <Check className="h-4 w-4" />
                  Salvo
                </span>
              )}
              {saveStatus === "error" && (
                <span className="flex items-center gap-1 text-sm text-red-400">
                  <AlertCircle className="h-4 w-4" />
                  Erro ao salvar
                </span>
              )}
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
                <span className="text-zinc-300">NVIDIA RTX 3060 12GB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Pipeline</span>
                <span className="text-zinc-300">
                  {settings?.enable_pipeline ? "Ativo" : "Desativado"}
                </span>
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
