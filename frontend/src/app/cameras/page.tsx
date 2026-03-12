"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2, Edit2, Wifi, WifiOff, Loader2, Eye } from "lucide-react";

import { Header } from "@/components/layout/Header";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { useCameraStore } from "@/stores/useCameraStore";
import { useRealtimeStore } from "@/stores/useRealtimeStore";
import { api } from "@/lib/api";
import type { Camera } from "@/types";

function CameraTestButton({ camera }: { camera: Camera }) {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const handleTest = async () => {
    setTesting(true);
    setResult(null);
    try {
      const res = await api.post<{ status: string; message: string; frame_size: number }>(
        `/cameras/${camera.id}/test`,
        {},
      );
      setResult(res);
    } catch {
      setResult({ status: "error", message: "Erro de rede ao testar" });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button variant="ghost" size="sm" onClick={handleTest} disabled={testing}>
        {testing ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Wifi className="h-3.5 w-3.5" />
        )}
      </Button>
      {result && (
        <span
          className={`text-[10px] ${
            result.status === "ok" ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {result.status === "ok" ? "OK" : "Falha"}
        </span>
      )}
    </div>
  );
}

function CameraSnapshotPreview({ camera }: { camera: Camera }) {
  const [open, setOpen] = useState(false);
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const handleOpen = async () => {
    setOpen(true);
    setLoading(true);
    setError(false);
    try {
      const res = await fetch(`/api/cameras/${camera.id}/snapshot`);
      if (res.ok) {
        const blob = await res.blob();
        setImgSrc(URL.createObjectURL(blob));
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    if (imgSrc) {
      URL.revokeObjectURL(imgSrc);
      setImgSrc(null);
    }
  };

  return (
    <>
      <Button variant="ghost" size="sm" onClick={handleOpen}>
        <Eye className="h-3.5 w-3.5" />
      </Button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
          onClick={handleClose}
        >
          <div
            className="relative max-w-3xl w-full mx-4 rounded-xl overflow-hidden bg-zinc-900 border border-zinc-800"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
              <div>
                <h3 className="text-sm font-medium text-zinc-200">{camera.name}</h3>
                <p className="text-[11px] text-zinc-500">{camera.location || camera.rtsp_url}</p>
              </div>
              <Button variant="secondary" size="sm" onClick={handleClose}>
                Fechar
              </Button>
            </div>
            <div className="aspect-video bg-zinc-950 flex items-center justify-center">
              {loading && (
                <Loader2 className="h-8 w-8 text-zinc-600 animate-spin" />
              )}
              {error && (
                <div className="text-center">
                  <WifiOff className="h-8 w-8 text-zinc-600 mx-auto mb-2" />
                  <p className="text-xs text-zinc-500">Nao foi possivel obter snapshot</p>
                  <p className="text-[10px] text-zinc-600 mt-1">Verifique a URL RTSP e credenciais</p>
                </div>
              )}
              {imgSrc && !error && (
                <img
                  src={imgSrc}
                  alt={camera.name}
                  className="h-full w-full object-contain"
                />
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default function CamerasPage() {
  const cameras = useCameraStore((s) => s.cameras);
  const fetchCameras = useCameraStore((s) => s.fetchCameras);
  const createCamera = useCameraStore((s) => s.createCamera);
  const deleteCamera = useCameraStore((s) => s.deleteCamera);
  const occupancy = useRealtimeStore((s) => s.occupancy);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [rtspUrl, setRtspUrl] = useState("");
  const [rtspProtocol, setRtspProtocol] = useState("rtsp");
  const [resolution, setResolution] = useState("1920x1080");
  const [fpsTarget, setFpsTarget] = useState(5);

  useEffect(() => {
    fetchCameras();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await createCamera({
        name,
        location: location || null,
        rtsp_url: rtspUrl,
        rtsp_protocol: rtspProtocol,
        resolution,
        fps_target: fpsTarget,
      });
      setShowForm(false);
      setName("");
      setLocation("");
      setRtspUrl("");
      setRtspProtocol("rtsp");
      setResolution("1920x1080");
      setFpsTarget(5);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro ao salvar camera");
    }
  };

  return (
    <div>
      <Header title="Cameras" subtitle={`${cameras.length} cameras configuradas`} />

      <div className="p-6 space-y-6">
        {/* Actions */}
        <div className="flex justify-end">
          <Button onClick={() => setShowForm(!showForm)}>
            <Plus className="h-4 w-4" />
            Adicionar Camera
          </Button>
        </div>

        {/* Add form */}
        {showForm && (
          <Card>
            <CardHeader>
              <h3 className="text-sm font-medium">Nova Camera</h3>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Nome</label>
                    <input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                      placeholder="Salao Principal"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Localizacao</label>
                    <input
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                      placeholder="Unidade Centro"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Protocolo</label>
                    <select
                      value={rtspProtocol}
                      onChange={(e) => {
                        setRtspProtocol(e.target.value);
                        // Auto-adjust placeholder when switching protocol
                        if (e.target.value === "rtsps" && !rtspUrl) {
                          setRtspUrl("rtsps://");
                        }
                      }}
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                    >
                      <option value="rtsp">RTSP</option>
                      <option value="rtsps">RTSPS (Ubiquiti)</option>
                    </select>
                  </div>
                  <div className="col-span-3">
                    <label className="block text-xs text-zinc-400 mb-1">URL do Stream</label>
                    <input
                      value={rtspUrl}
                      onChange={(e) => setRtspUrl(e.target.value)}
                      required
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                      placeholder={
                        rtspProtocol === "rtsps"
                          ? "rtsps://192.168.1.100:7441/abcdef123456_2"
                          : "rtsp://admin:senha@192.168.0.101:554/onvif1"
                      }
                    />
                  </div>
                </div>

                {rtspProtocol === "rtsps" && (
                  <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 px-3 py-2">
                    <p className="text-[11px] text-blue-400 font-medium mb-1">Ubiquiti / UniFi Protect</p>
                    <p className="text-[10px] text-blue-400/70">
                      URL padrao: <code className="bg-blue-500/10 px-1 rounded">rtsps://IP:7441/CAMERA_ID_2</code> (Full HD) ou <code className="bg-blue-500/10 px-1 rounded">_0</code> (4K).
                      Obtenha o ID da camera no UniFi Protect &gt; Camera &gt; Settings &gt; RTSP.
                      O certificado SSL e aceito automaticamente.
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">Resolucao</label>
                    <select
                      value={resolution}
                      onChange={(e) => setResolution(e.target.value)}
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                    >
                      <option value="3840x2160">4K (3840x2160)</option>
                      <option value="2560x1440">2K (2560x1440)</option>
                      <option value="1920x1080">Full HD (1920x1080)</option>
                      <option value="1280x720">HD (1280x720)</option>
                      <option value="640x360">SD (640x360)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">FPS Target</label>
                    <input
                      type="number"
                      value={fpsTarget}
                      onChange={(e) => setFpsTarget(Number(e.target.value))}
                      min={1}
                      max={30}
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-800/50 px-3 py-2 text-sm text-zinc-200 focus:border-amber-500 focus:outline-none"
                    />
                  </div>
                  <div className="flex items-end">
                    <p className="text-[10px] text-zinc-500 pb-2">
                      GPU: 5-10 FPS | CPU: 1-3 FPS
                    </p>
                  </div>
                </div>
                {formError && (
                  <div className="col-span-2 rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2 text-sm text-red-400">
                    {formError}
                  </div>
                )}
                <div className="col-span-2 flex gap-2 justify-end">
                  <Button variant="secondary" type="button" onClick={() => setShowForm(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit">Salvar</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Camera list */}
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800/50">
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Camera
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Localizacao
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Resolucao
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Ocupacao
                  </th>
                  <th className="px-5 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                    Acoes
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/30">
                {cameras.map((camera) => (
                  <tr key={camera.id} className="hover:bg-zinc-900/50 transition-colors">
                    <td className="px-5 py-3">
                      <div className="font-medium text-zinc-200">{camera.name}</div>
                      <div className="text-[11px] text-zinc-600 truncate max-w-[200px]">
                        {camera.rtsp_url}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-zinc-400">
                      {camera.location || "—"}
                    </td>
                    <td className="px-5 py-3">
                      <div className="text-zinc-300 text-xs">{camera.resolution}</div>
                      <div className="text-[10px] text-zinc-600 uppercase">
                        {camera.rtsp_protocol === "rtsps" ? "RTSPS" : "RTSP"}
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <Badge variant={camera.is_active ? "success" : "default"}>
                        {camera.is_active ? "Ativa" : "Inativa"}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 tabular-nums text-zinc-300">
                      {occupancy[camera.id] ?? 0} pessoas
                    </td>
                    <td className="px-5 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <CameraTestButton camera={camera} />
                        <CameraSnapshotPreview camera={camera} />
                        <Button variant="ghost" size="sm">
                          <Edit2 className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteCamera(camera.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-red-400" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
